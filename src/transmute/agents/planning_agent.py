"""
Planning agent for migration planning.

Creates migration plans based on analysis results.
"""

from typing import Dict, Any, List 
from pathlib import Path
import uuid

from transmute.agents.base import BaseAgent
from transmute.core.state import (
    TransmuteState,
    MigrationPlan,
    TranslationUnit,
    TranslationStatus,
    StrategyType,
)


class PlanningAgent(BaseAgent):
    """
    Creates migration plans based on repository analysis.
    
    This agent:
    1. Determines translation strategy
    2. Creates translation units for each file
    3. Resolves dependencies
    4. Sets execution order
    5. Estimates duration and complexity
    """
    
    def __init__(self):
        """Initialize planning agent."""
        super().__init__("PlanningAgent")
    
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Create migration plan.
        
        Args:
            state: Current state
            
        Returns:
            State updates with migration plan
        """
        self.log_info("Creating migration plan")
        
        if not state.source_language or not state.target_language:
            self.log_error("Source or target language not specified")
            return {
                "errors": state.errors + ["Missing source or target language"],
                "current_step": "error"
            }
        
        try:
            # Get file map from metadata
            file_map = state.metadata.get('file_map', {})
            source_lang = state.source_language.name
            
            if source_lang not in file_map:
                self.log_error(f"No files found for language: {source_lang}")
                return {
                    "errors": state.errors + [f"No {source_lang} files found"],
                    "current_step": "error"
                }
            
            # Create translation units
            files = file_map[source_lang]
            
            # Respect max_files limit if set
            max_files = state.metadata.get('max_files')
            if max_files and max_files > 0:
                files = files[:max_files]
                self.log_info(f"Limited to {max_files} files (from {len(file_map[source_lang])} total)")
            
            translation_units = []
            
            self.log_info(f"Creating translation units for {len(files)} files")
            
            for file_path in files:
                unit = TranslationUnit(
                    unit_id=str(uuid.uuid4()),
                    source_path=Path(file_path),
                    status=TranslationStatus.PENDING,
                    priority=0,
                    complexity=0.5,  # Default complexity
                )
                translation_units.append(unit)
            
            # Determine overall strategy
            complexity = state.feature_profile.complexity_score if state.feature_profile else 0.5
            
            if complexity < 0.3:
                strategy = StrategyType.DIRECT
            elif complexity < 0.7:
                strategy = StrategyType.PATTERN
            else:
                strategy = StrategyType.REFACTOR
            
            # Create execution order (simple: by priority, then by name)
            execution_order = [unit.unit_id for unit in sorted(
                translation_units,
                key=lambda u: (u.priority, str(u.source_path))
            )]
            
            # Estimate duration (rough estimate: 1 minute per file)
            estimated_duration = len(translation_units) * 1
            
            # Create migration plan
            plan = MigrationPlan(
                plan_id=str(uuid.uuid4()),
                source_language=source_lang,
                target_language=state.target_language.name,
                total_units=len(translation_units),
                translation_units=translation_units,
                execution_order=execution_order,
                overall_strategy=strategy,
                estimated_duration_minutes=estimated_duration,
                estimated_complexity=complexity,
                dependencies_resolved=True,  # Simplified for now
            )
            
            self.log_info(f"Created plan: {len(translation_units)} units, "
                         f"strategy={strategy.value}, duration~{estimated_duration}min")
            
            return {
                "migration_plan": plan,
                "current_step": "translation",
            }
            
        except Exception as e:
            self.log_error(f"Planning failed: {e}")
            raise
    def optimize_execution_order(
        self,
        units: List[TranslationUnit]
    ) -> List[str]:
        """
        Optimize execution order based on dependencies and complexity.
        
        Args:
            units: Translation units
            
        Returns:
            Optimized execution order (unit IDs)
        """
        # Sort by: priority (desc), complexity (asc), name
        sorted_units = sorted(
            units,
            key=lambda u: (-u.priority, u.complexity, str(u.source_path))
        )
        
        return [u.unit_id for u in sorted_units]
    
    def estimate_difficulty(self, complexity: float) -> str:
        """
        Estimate difficulty level from complexity score.
        
        Args:
            complexity: Complexity score (0.0-1.0)
            
        Returns:
            Difficulty level string
        """
        if complexity < 0.3:
            return "easy"
        elif complexity < 0.6:
            return "medium"
        elif complexity < 0.8:
            return "hard"
        else:
            return "very_hard"
    
    def calculate_confidence(self, plan: MigrationPlan) -> float:
        """
        Calculate confidence in migration plan.
        
        Args:
            plan: MigrationPlan
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 1.0
        
        # Lower confidence for complex migrations
        complexity_penalty = plan.estimated_complexity * 0.3
        confidence -= complexity_penalty
        
        # Lower confidence for large migrations
        if plan.total_units > 100:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))