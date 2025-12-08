"""
Main workflow for Transmute using LangGraph.

Orchestrates the complete code translation pipeline.
"""

from typing import Dict, Any, Optional, Literal
from pathlib import Path
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from transmute.core.state import TransmuteState, LanguageInfo
from transmute.agents import AnalysisAgent, PlanningAgent, TranslationAgent
from transmute.languages.registry import LanguageRegistry
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TransmuteWorkflow:
    """
    Complete workflow for code translation.
    
    Uses LangGraph to orchestrate agents through the translation pipeline:
    1. Analysis - Analyze repository
    2. Planning - Create migration plan
    3. Translation - Translate code
    4. Completion - Finalize results
    """
    
    def __init__(
        self,
        language_registry: LanguageRegistry,
        work_dir: Path = Path("/tmp/transmute"),
        use_checkpoints: bool = True
    ):
        """
        Initialize workflow.
        
        Args:
            language_registry: Registry with language plugins
            work_dir: Working directory
            use_checkpoints: Enable checkpoint saving
        """
        self.language_registry = language_registry
        self.work_dir = work_dir
        self.use_checkpoints = use_checkpoints
        
        # Initialize agents
        self.analysis_agent = AnalysisAgent(language_registry, work_dir)
        self.planning_agent = PlanningAgent()
        self.translation_agent = TranslationAgent()
        
        # Create workflow graph
        self.graph = self._create_graph()
        
        logger.info("TransmuteWorkflow initialized")
    
    def _create_graph(self) -> StateGraph:
        """
        Create LangGraph StateGraph.
        
        Returns:
            Compiled StateGraph
        """
        logger.info("Creating workflow graph")
        
        # Create graph
        workflow = StateGraph(TransmuteState)
        
        # Add nodes (agents)
        workflow.add_node("analysis", self.analysis_agent)
        workflow.add_node("planning", self.planning_agent)
        workflow.add_node("translation", self.translation_agent)
        workflow.add_node("completion", self._complete)
        
        # Set entry point
        workflow.set_entry_point("analysis")
        
        # Add edges
        workflow.add_edge("analysis", "planning")
        workflow.add_edge("planning", "translation")
        
        # Conditional edge: continue translating or complete?
        workflow.add_conditional_edges(
            "translation",
            self._should_continue_translation,
            {
                "continue": "translation",  # Loop back for next file
                "complete": "completion",   # All done
                "error": END                # Error occurred
            }
        )
        
        workflow.add_edge("completion", END)
        
        # Compile graph with checkpointing
        if self.use_checkpoints:
            memory = MemorySaver()
            compiled = workflow.compile(checkpointer=memory)
        else:
            compiled = workflow.compile()
        
        logger.info("Workflow graph created")
        
        return compiled
    
    def _should_continue_translation(
        self,
        state: TransmuteState
    ) -> Literal["continue", "complete", "error"]:
        """
        Determine if translation should continue.
        
        Args:
            state: Current state
            
        Returns:
            Next step: "continue", "complete", or "error"
        """
        # Check for errors
        if state.errors:
            logger.error(f"Workflow has {len(state.errors)} errors")
            return "error"
        
        # Check if we have a plan
        if not state.migration_plan:
            logger.warning("No migration plan - completing")
            return "complete"
        
        # Check if all units are translated
        plan = state.migration_plan
        completed = len(plan.get_completed_units())
        total = plan.total_units
        
        logger.info(f"Translation progress: {completed}/{total}")
        
        if completed >= total:
            return "complete"
        else:
            return "continue"
    
    def _complete(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Completion node - finalize workflow.
        
        Args:
            state: Current state
            
        Returns:
            Final state updates
        """
        logger.info("Completing workflow")
        
        # Mark as completed
        state.mark_completed()
        
        # Generate summary
        summary = self._generate_summary(state)
        
        logger.info("Workflow completed successfully")
        logger.info(summary)
        
        return {
            "current_step": "completed",
            "metadata": {
                **state.metadata,
                "summary": summary,
            }
        }
    
    def _generate_summary(self, state: TransmuteState) -> str:
        """Generate workflow summary."""
        lines = [
            "=" * 60,
            "TRANSMUTE WORKFLOW SUMMARY",
            "=" * 60,
        ]
        
        if state.repository:
            lines.extend([
                f"Repository: {state.repository.url}",
                f"Platform: {state.repository.platform}",
            ])
        
        if state.source_language and state.target_language:
            lines.extend([
                "",
                f"Translation: {state.source_language.name} → {state.target_language.name}",
            ])
        
        if state.migration_plan:
            plan = state.migration_plan
            completed = len(plan.get_completed_units())
            lines.extend([
                "",
                f"Progress: {completed}/{plan.total_units} files translated",
                f"Strategy: {plan.overall_strategy.value}",
                f"Duration: {state.duration_seconds:.1f}s",
            ])
        
        if state.feature_profile:
            lines.extend([
                "",
                f"Complexity: {state.feature_profile.complexity_score:.2f}",
                f"Features: {len(state.feature_profile.features_used)}",
            ])
        
        if state.errors:
            lines.extend([
                "",
                f"Errors: {len(state.errors)}",
            ])
            for error in state.errors[:3]:  # Show first 3
                lines.append(f"  - {error}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def run(
        self,
        repository_url: str,
        target_language: str,
        branch: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> TransmuteState:
        """
        Run complete workflow.
        
        Args:
            repository_url: Git repository URL
            target_language: Target language name
            branch: Git branch (optional)
            config: Additional configuration (optional)
            
        Returns:
            Final TransmuteState
        """
        logger.info(f"Starting workflow: {repository_url} → {target_language}")
        
        # Create initial state
        session_id = str(uuid.uuid4())
        
        initial_state = TransmuteState(
            session_id=session_id,
            target_language=LanguageInfo(name=target_language),
            metadata={
                "repository_url": repository_url,
                "branch": branch,
                **(config or {})
            }
        )
        
        # Run workflow
        try:
            # Create config for checkpointing
            run_config = {
                "configurable": {
                    "thread_id": session_id
                }
            }
            
            # Invoke graph
            final_state = self.graph.invoke(initial_state, run_config)
            
            logger.info("Workflow completed")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            
            # Add error to state
            initial_state.add_error(f"Workflow failed: {str(e)}")
            initial_state.current_step = "error"
            
            return initial_state
    
    def stream(
        self,
        repository_url: str,
        target_language: str,
        branch: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Stream workflow execution (yields updates).
        
        Args:
            repository_url: Git repository URL
            target_language: Target language name
            branch: Git branch (optional)
            config: Additional configuration (optional)
            
        Yields:
            State updates at each step
        """
        logger.info(f"Streaming workflow: {repository_url} → {target_language}")
        
        # Create initial state
        session_id = str(uuid.uuid4())
        
        initial_state = TransmuteState(
            session_id=session_id,
            target_language=LanguageInfo(name=target_language),
            metadata={
                "repository_url": repository_url,
                "branch": branch,
                **(config or {})
            }
        )
        
        # Stream workflow
        try:
            # Create config for checkpointing
            stream_config = {
                "configurable": {
                    "thread_id": session_id
                }
            }
            
            for output in self.graph.stream(initial_state, stream_config):
                yield output
                
        except Exception as e:
            logger.error(f"Workflow streaming failed: {e}")
            yield {
                "errors": [f"Workflow failed: {str(e)}"],
                "current_step": "error"
            }
    
    def get_status(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            state: Current state
            
        Returns:
            Status information
        """
        status = {
            "session_id": state.session_id,
            "current_step": state.current_step,
            "is_completed": state.is_completed,
            "duration_seconds": state.duration_seconds,
            "has_errors": len(state.errors) > 0,
            "error_count": len(state.errors),
        }
        
        if state.migration_plan:
            plan = state.migration_plan
            completed = len(plan.get_completed_units())
            status.update({
                "total_files": plan.total_units,
                "completed_files": completed,
                "progress_percentage": (completed / plan.total_units * 100) if plan.total_units > 0 else 0,
            })
        
        return status
    
    def export_results(
        self,
        state: TransmuteState,
        output_dir: Path
    ) -> Path:
        """
        Export translation results.
        
        Args:
            state: Final state
            output_dir: Directory to export to
            
        Returns:
            Path to exported results
        """
        from transmute.utils.paths import ensure_dir
        
        logger.info(f"Exporting results to {output_dir}")
        
        ensure_dir(output_dir)
        
        # Export summary
        summary_file = output_dir / "summary.txt"
        summary = self._generate_summary(state)
        summary_file.write_text(summary)
        
        # Export translated files (if any)
        if state.migration_plan:
            translations_dir = output_dir / "translations"
            ensure_dir(translations_dir)
            
            for unit in state.migration_plan.get_completed_units():
                if unit.translated_code:
                    # Create target file
                    target_file = translations_dir / unit.source_path.name
                    target_file.write_text(unit.translated_code)
        
        logger.info(f"Results exported to {output_dir}")
        
        return output_dir
    
    def cleanup(self, state: TransmuteState) -> None:
        """
        Clean up workflow resources.
        
        Args:
            state: Current state
        """
        logger.info("Cleaning up workflow resources")
        
        # Clean up cloned repository
        clone_path = state.metadata.get('clone_path')
        if clone_path:
            import shutil
            clone_path = Path(clone_path)
            if clone_path.exists():
                shutil.rmtree(clone_path)
                logger.info(f"Removed clone: {clone_path}")