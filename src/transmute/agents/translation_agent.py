"""
Translation agent for code translation with REAL LLM integration.

Translates code using RAG patterns and Claude API.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from transmute.agents.base import BaseAgent
from transmute.core.state import TransmuteState, TranslationStatus, TranslationUnit, MigrationPlan
from transmute.llm.claude_client import ClaudeClient
from transmute.rag.rag_system import RAGSystem
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TranslationAgent(BaseAgent):
    """
    Translates code from source to target language using LLM.
    
    This agent:
    1. Retrieves relevant patterns from RAG
    2. Prepares context for translation
    3. Uses Claude API for intelligent translation
    4. Validates and stores results
    5. Tracks progress
    """
    
    def __init__(
        self,
        rag_system: Optional[RAGSystem] = None,
        claude_client: Optional[ClaudeClient] = None,
        use_llm: bool = True
    ):
        """
        Initialize translation agent.
        
        Args:
            rag_system: RAG system for pattern retrieval (optional)
            claude_client: Claude API client (optional)
            use_llm: Whether to use LLM (False = placeholder mode)
        """
        super().__init__("TranslationAgent")
        
        self.rag_system = rag_system
        self.claude_client = claude_client
        self.use_llm = use_llm
        
        if use_llm and not claude_client:
            # Initialize default Claude client
            try:
                self.claude_client = ClaudeClient()
                self.log_info("Initialized Claude API client")
            except Exception as e:
                self.log_warning(f"Could not initialize Claude client: {e}")
                self.use_llm = False
    
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Process translation.
        
        Args:
            state: Current state
            
        Returns:
            State updates with translation results
        """
        self.log_info("Starting translation")
        
        if not state.migration_plan:
            self.log_error("No migration plan available")
            return {
                "errors": state.errors + ["No migration plan"],
                "current_step": "error"
            }
        
        plan = state.migration_plan
        
        # Get pending units
        pending = plan.get_pending_units()
        
        if not pending:
            self.log_info("No pending translations")
            return {
                "current_step": "validation",
            }
        
        # Translate ALL pending units
        self.log_info(f"Translating {len(pending)} units")
        
        for unit in pending:
            self.log_info(f"Translating unit: {unit.source_path}")
            
            # Mark in progress
            unit.mark_in_progress()
            
            try:
                # Load source code if not already loaded
                if not unit.source_code:
                    unit.source_code = self._load_source_code(unit, state)
                
                # Translate
                if self.use_llm and self.claude_client:
                    result = self._translate_with_llm(unit, state)
                else:
                    result = self._translate_placeholder(unit, state)
                
                # Update unit
                unit.translated_code = result['translated_code']
                unit.confidence_score = result.get('confidence', 0.8)
                unit.translation_strategy = result.get('strategy', 'llm')
                unit.metadata['explanation'] = result.get('explanation', '')
                
                # Mark completed
                unit.mark_completed()
                
                # SAVE TRANSLATION TO DISK IMMEDIATELY
                try:
                    from pathlib import Path
                    
                    # Get output directory from state metadata or use default
                    output_base = Path(state.metadata.get('output_dir', 'demo_output/translations'))
                    output_base.mkdir(parents=True, exist_ok=True)
                    
                    # Create subdirectories if needed (preserve structure)
                    relative_path = unit.source_path
                    if relative_path.parent != Path('.'):
                        output_dir = output_base / relative_path.parent
                        output_dir.mkdir(parents=True, exist_ok=True)
                    else:
                        output_dir = output_base
                    
                    # Determine target extension based on target language
                    target_ext_map = {
                        'java': '.java',
                        'javascript': '.js',
                        'typescript': '.ts',
                        'csharp': '.cs',
                        'php': '.php',
                        'python': '.py',
                    }
                    
                    target_lang_name = state.target_language.name.lower() if state.target_language else 'unknown'
                    target_ext = target_ext_map.get(target_lang_name, '.txt')
                    
                    # Get source extension
                    source_ext = relative_path.suffix
                    
                    # Replace source extension with target extension
                    output_file = output_dir / relative_path.name.replace(source_ext, target_ext)
                    
                    output_file.write_text(unit.translated_code, encoding='utf-8')
                    
                    self.log_info(f"💾 Saved: {output_file}")
                    
                except Exception as e:
                    self.log_warning(f"Could not save translation to disk: {e}")
                
                self.log_info(f"Completed translation: {unit.source_path} (confidence: {unit.confidence_score:.2f})")

            except Exception as e:
                self.log_error(f"Translation failed for {unit.source_path}: {e}")
                unit.mark_failed(str(e))
        
        # Check completion
        completed = len(plan.get_completed_units())
        self.log_info(f"Progress: {completed}/{plan.total_units}")
        
        return {
            "migration_plan": plan,
            "current_step": "validation",
        }
    
    def _load_source_code(self, unit: TranslationUnit, state: TransmuteState) -> str:
        """Load source code from file."""
        clone_path = state.metadata.get('clone_path')
        
        if not clone_path:
            raise ValueError("No clone_path in metadata")
        
        file_path = Path(clone_path) / unit.source_path
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _translate_with_llm(
        self,
        unit: TranslationUnit,
        state: TransmuteState
    ) -> Dict[str, Any]:
        """
        Translate using Claude API + RAG.
        
        Args:
            unit: Translation unit
            state: Current state
            
        Returns:
            Translation result
        """
        self.log_info("Using Claude API for translation")
        
        # Retrieve similar patterns from RAG
        context_patterns = None
        
        if self.rag_system:
            try:
                context_patterns = self.rag_system.retrieve_context(
                    query_code=unit.source_code[:500],  # First 500 chars
                    source_language=state.source_language.name,
                    target_language=state.target_language.name,
                    top_k=3
                )
                self.log_debug(f"Retrieved {len(context_patterns)} similar patterns")
            except Exception as e:
                self.log_warning(f"RAG retrieval failed: {e}")
        
        # Translate with Claude
        result = self.claude_client.translate_code(
            source_code=unit.source_code,
            source_language=state.source_language.name,
            target_language=state.target_language.name,
            feature_profile=state.feature_profile,
            context_patterns=context_patterns
        )
        
        result['strategy'] = 'llm_with_rag' if context_patterns else 'llm'
        
        return result
    
    def _translate_placeholder(
        self,
        unit: TranslationUnit,
        state: TransmuteState
    ) -> Dict[str, Any]:
        """Placeholder translation (no LLM)."""
        self.log_info("Using placeholder translation (no LLM)")
        
        return {
            'translated_code': f"// Translated from {state.source_language.name}\n// TODO: Actual translation\n\n{unit.source_code}",
            'confidence': 0.5,
            'explanation': 'Placeholder translation - LLM not available',
            'strategy': 'placeholder'
        }
    
    def prepare_translation_context(
        self,
        unit: TranslationUnit,
        state: TransmuteState
    ) -> str:
        """
        Prepare context for LLM translation.
        
        Args:
            unit: Translation unit
            state: Current state
            
        Returns:
            Context string for LLM
        """
        context_parts = []
        
        context_parts.append(f"Translate from {state.source_language.name} to {state.target_language.name}")
        context_parts.append(f"File: {unit.source_path}")
        
        if state.feature_profile:
            context_parts.append(f"Complexity: {state.feature_profile.complexity_score:.2f}")
        
        if unit.source_code:
            context_parts.append(f"\nSource code:\n{unit.source_code[:500]}")
        
        return "\n".join(context_parts)
    
    def calculate_translation_confidence(
        self,
        source_code: str,
        translated_code: str
    ) -> float:
        """
        Calculate confidence in translation.
        
        Args:
            source_code: Original code
            translated_code: Translated code
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.8  # Base confidence
        
        # Check lengths are similar (rough heuristic)
        len_ratio = len(translated_code) / max(len(source_code), 1)
        
        if 0.5 <= len_ratio <= 2.0:
            confidence += 0.1
        else:
            confidence -= 0.2
        
        # Check if translation has content
        if not translated_code.strip():
            confidence = 0.0
        
        return max(0.0, min(1.0, confidence))
    
    def get_translation_progress(
        self,
        plan: MigrationPlan
    ) -> Dict[str, Any]:
        """
        Get translation progress statistics.
        
        Args:
            plan: Migration plan
            
        Returns:
            Progress dictionary
        """
        completed = len(plan.get_completed_units())
        pending = len(plan.get_pending_units())
        
        return {
            'completed': completed,
            'pending': pending,
            'total': plan.total_units,
            'percentage': (completed / plan.total_units * 100) if plan.total_units > 0 else 0,
        }