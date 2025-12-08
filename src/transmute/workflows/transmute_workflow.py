"""
Enhanced Transmute workflow with advanced agent orchestration.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from transmute.core.state import TransmuteState
from transmute.agents import (
    AnalysisAgent,
    PlanningAgent,
    TranslationAgent,
    ValidationAgent,
    AgentOrchestrator,
    RetryHandler,
    HITLSystem,
    MiddlewarePipeline,
    CodeNormalizationMiddleware,
    CommentPreservationMiddleware,
    QualityCheckMiddleware,
)
from transmute.rag import RAGSystem
from transmute.llm import ClaudeClient
from transmute.languages import LanguageRegistry
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TransmuteWorkflow:
    """
    Enhanced LangGraph workflow for code translation.
    
    Features:
    - Agent orchestration
    - Retry mechanisms
    - Human-in-the-loop review
    - Quality pipelines
    """
    
    def __init__(
        self,
        registry: LanguageRegistry,
        rag_system: Optional[RAGSystem] = None,
        claude_client: Optional[ClaudeClient] = None,
        use_hitl: bool = False,
        hitl_confidence_threshold: float = 0.7
    ):
        """
        Initialize workflow.
        
        Args:
            registry: Language registry
            rag_system: Optional RAG system
            claude_client: Optional Claude client
            use_hitl: Enable human-in-the-loop
            hitl_confidence_threshold: HITL threshold
        """
        self.registry = registry
        self.rag_system = rag_system
        self.claude_client = claude_client
        self.use_hitl = use_hitl
        
        self.analysis_agent = AnalysisAgent(language_registry=registry)
        self.planning_agent = PlanningAgent()
        self.translation_agent = TranslationAgent(
            # language_registry=registry,
            rag_system=rag_system,
            claude_client=claude_client
        )
        self.validation_agent = ValidationAgent()
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator()
        self._setup_orchestrator()
        
        # Initialize retry handler
        self.retry_handler = RetryHandler(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0
        )
        
        # Initialize HITL if enabled
        self.hitl_system = None
        if use_hitl:
            self.hitl_system = HITLSystem(
                confidence_threshold=hitl_confidence_threshold
            )
        
        # Initialize middleware pipeline
        self.middleware = MiddlewarePipeline("TranslationPipeline")
        self._setup_middleware()
        
        # Build graph
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
        
        logger.info("Enhanced TransmuteWorkflow initialized")
    
    def _setup_orchestrator(self):
        """Setup agent orchestrator."""
        self.orchestrator.register_agent("analysis", self.analysis_agent)
        self.orchestrator.register_agent("planning", self.planning_agent)
        self.orchestrator.register_agent("translation", self.translation_agent)
        self.orchestrator.register_agent("validation", self.validation_agent)
        
        # Set execution order
        self.orchestrator.set_execution_order([
            "analysis",
            "planning",
            "translation",
            "validation"
        ])
        
        # Register callbacks
        def on_agent_complete(agent_name: str, state: TransmuteState):
            logger.info(f"✓ {agent_name} completed")
        
        def on_agent_error(agent_name: str, state: TransmuteState):
            logger.error(f"✗ {agent_name} failed")
        
        self.orchestrator.register_callback('after_agent', on_agent_complete)
        self.orchestrator.register_callback('on_error', on_agent_error)
    
    def _setup_middleware(self):
        """Setup middleware pipeline."""
        self.middleware.add(CodeNormalizationMiddleware())
        self.middleware.add(CommentPreservationMiddleware())
        self.middleware.add(QualityCheckMiddleware(min_quality=0.6))
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(TransmuteState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("translate", self._translate_node)
        workflow.add_node("validate", self._validate_node)
        
        # Add HITL node if enabled
        if self.use_hitl:
            workflow.add_node("review", self._review_node)
        
        # Add edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "translate")
        
        if self.use_hitl:
            workflow.add_edge("translate", "review")
            workflow.add_edge("review", "validate")
        else:
            workflow.add_edge("translate", "validate")
        
        workflow.add_edge("validate", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _analyze_node(self, state: TransmuteState) -> Dict[str, Any]:
        """Analysis node with retry."""
        logger.info("📊 Running analysis...")
        
        def run_analysis():
            return self.analysis_agent(state)
        
        try:
            result = self.retry_handler.execute_with_retry(run_analysis)
            return result
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            state.add_error(f"Analysis failed: {str(e)}")
            return {"errors": state.errors}
    
    def _plan_node(self, state: TransmuteState) -> Dict[str, Any]:
        """Planning node with retry."""
        logger.info("📋 Creating migration plan...")
        
        def run_planning():
            return self.planning_agent(state)
        
        try:
            result = self.retry_handler.execute_with_retry(run_planning)
            return result
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state.add_error(f"Planning failed: {str(e)}")
            return {"errors": state.errors}
    
    def _translate_node(self, state: TransmuteState) -> Dict[str, Any]:
        """Translation node with retry and middleware."""
        logger.info("🔄 Translating code...")
        
        # Apply pre-processing middleware
        if state.migration_plan and state.migration_plan.translation_units:
            for unit in state.migration_plan.translation_units:
                if unit.source_code:
                    # Process through middleware
                    unit = self.middleware.process(unit)
        
        def run_translation():
            return self.translation_agent(state)
        
        try:
            result = self.retry_handler.execute_with_retry(
                run_translation,
                fallback=lambda: self._fallback_translation(state)
            )
            return result
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            state.add_error(f"Translation failed: {str(e)}")
            return {"errors": state.errors}
    
    def _fallback_translation(self, state: TransmuteState) -> Dict[str, Any]:
        """Fallback translation (placeholder mode)."""
        logger.warning("Using fallback translation mode")
        
        # Use translation agent in non-LLM mode
        old_use_llm = self.translation_agent.use_llm
        self.translation_agent.use_llm = False
        
        try:
            result = self.translation_agent(state)
        finally:
            self.translation_agent.use_llm = old_use_llm
        
        return result
    
    def _review_node(self, state: TransmuteState) -> Dict[str, Any]:
        """HITL review node."""
        logger.info("👤 Human review checkpoint...")
        
        if not self.hitl_system or not state.migration_plan:
            return {}
        
        reviewed_count = 0
        
        for unit in state.migration_plan.translation_units:
            if unit.status == "completed":
                # Check if needs review
                if self.hitl_system.needs_review(unit, state):
                    decision = self.hitl_system.request_review(unit)
                    
                    if decision.value == "reject":
                        unit.status = "failed"
                        unit.add_error("Rejected in human review")
                    elif decision.value == "modify":
                        # Could trigger re-translation or manual edit
                        unit.metadata['needs_modification'] = True
                    
                    reviewed_count += 1
        
        if reviewed_count > 0:
            logger.info(f"Reviewed {reviewed_count} translations")
        
        return {}
    
    def _validate_node(self, state: TransmuteState) -> Dict[str, Any]:
        """Validation node with retry."""
        logger.info("✓ Validating translations...")
        
        def run_validation():
            return self.validation_agent(state)
        
        try:
            result = self.retry_handler.execute_with_retry(run_validation)
            return result
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state.add_error(f"Validation failed: {str(e)}")
            return {"errors": state.errors}
    
    def run(
        self,
        initial_state: TransmuteState,
        thread_id: str = "default"
    ) -> TransmuteState:
        """
        Run workflow synchronously.
        
        Args:
            initial_state: Initial state
            thread_id: Thread ID for checkpointing
            
        Returns:
            Final state
        """
        logger.info("🚀 Starting enhanced Transmute workflow")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Run workflow
        result = self.graph.invoke(initial_state, config=config)
        
        # Extract final state
        final_state = result if isinstance(result, TransmuteState) else initial_state
        
        logger.info("✅ Workflow completed")
        
        return final_state
    
    def stream(
        self,
        initial_state: TransmuteState,
        thread_id: str = "default"
    ):
        """
        Stream workflow execution.
        
        Args:
            initial_state: Initial state
            thread_id: Thread ID for checkpointing
            
        Yields:
            State updates
        """
        logger.info("🚀 Starting enhanced Transmute workflow (streaming)")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        for state_update in self.graph.stream(initial_state, config=config):
            yield state_update
        
        logger.info("✅ Workflow completed")
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get workflow statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'orchestrator_status': self.orchestrator.get_agent_status(),
            'retry_history': self.retry_handler.get_error_history(),
            'middleware_enabled': self.middleware.get_enabled()
        }
        
        if self.hitl_system:
            stats['hitl_statistics'] = self.hitl_system.get_review_statistics()
        
        return stats