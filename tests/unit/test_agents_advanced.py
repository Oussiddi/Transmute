"""
Tests for advanced agent features (Module 11 completion).

Tests:
- AgentOrchestrator
- RetryHandler
- HITLSystem
- Middleware
"""

import pytest
from pathlib import Path
import time

from transmute.agents.orchestrator import AgentOrchestrator
from transmute.agents.retry_handler import RetryHandler, ErrorSeverity
from transmute.agents.hitl import HITLSystem, ReviewDecision
from transmute.agents.middleware import (
    CodeNormalizationMiddleware,
    CommentPreservationMiddleware,
    QualityCheckMiddleware,
    MiddlewarePipeline,
)
from transmute.agents.base import BaseAgent
from transmute.core.state import TransmuteState, TranslationUnit, LanguageInfo


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, name: str, should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
        self.call_count = 0
    
    def process(self, state: TransmuteState):
        self.call_count += 1
        
        if self.should_fail:
            raise ValueError(f"{self.name} failed")
        
        return {
            "metadata": {
                **state.metadata,
                f"{self.name}_executed": True
            }
        }


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.agents == {}
        assert orchestrator.execution_order == []
        assert 'before_agent' in orchestrator.callbacks
    
    def test_register_agent(self):
        """Test registering agents."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent")
        
        orchestrator.register_agent("test", agent)
        
        assert "test" in orchestrator.agents
        assert orchestrator.agents["test"] == agent
    
    def test_set_execution_order(self):
        """Test setting execution order."""
        orchestrator = AgentOrchestrator()
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)
        
        orchestrator.set_execution_order(["agent1", "agent2"])
        
        assert orchestrator.execution_order == ["agent1", "agent2"]
    
    def test_set_execution_order_invalid_agent(self):
        """Test setting execution order with invalid agent."""
        orchestrator = AgentOrchestrator()
        
        with pytest.raises(ValueError, match="Agent not registered"):
            orchestrator.set_execution_order(["nonexistent"])
    
    def test_register_callback(self):
        """Test registering callbacks."""
        orchestrator = AgentOrchestrator()
        
        called = []
        
        def callback(name, state):
            called.append(name)
        
        orchestrator.register_callback('before_agent', callback)
        
        assert len(orchestrator.callbacks['before_agent']) == 1
    
    def test_register_callback_invalid_event(self):
        """Test registering callback with invalid event."""
        orchestrator = AgentOrchestrator()
        
        with pytest.raises(ValueError, match="Unknown event"):
            orchestrator.register_callback('invalid_event', lambda x, y: None)
    
    def test_execute_success(self):
        """Test successful execution."""
        orchestrator = AgentOrchestrator()
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)
        orchestrator.set_execution_order(["agent1", "agent2"])
        
        state = TransmuteState(session_id="test")
        
        final_state = orchestrator.execute(state)
        
        assert agent1.call_count == 1
        assert agent2.call_count == 1
        assert final_state.metadata.get("Agent1_executed") is True
        assert final_state.metadata.get("Agent2_executed") is True
    
    def test_execute_with_error(self):
        """Test execution with agent failure."""
        orchestrator = AgentOrchestrator()
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2", should_fail=True)
        agent3 = MockAgent("Agent3")
        
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)
        orchestrator.register_agent("agent3", agent3)
        orchestrator.set_execution_order(["agent1", "agent2", "agent3"])
        
        state = TransmuteState(session_id="test")
        
        final_state = orchestrator.execute(state, stop_on_error=False)
        
        assert agent1.call_count == 1
        assert agent2.call_count == 1
        assert agent3.call_count == 1  # Continues after error
        assert len(final_state.errors) > 0
    
    def test_execute_stop_on_error(self):
        """Test execution stopping on error."""
        orchestrator = AgentOrchestrator()
        
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2", should_fail=True)
        agent3 = MockAgent("Agent3")
        
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)
        orchestrator.register_agent("agent3", agent3)
        orchestrator.set_execution_order(["agent1", "agent2", "agent3"])
        
        state = TransmuteState(session_id="test")
        
        final_state = orchestrator.execute(state, stop_on_error=True)
        
        assert agent1.call_count == 1
        assert agent2.call_count == 1
        assert agent3.call_count == 0  # Stopped
    
    def test_get_agent_status(self):
        """Test getting agent status."""
        orchestrator = AgentOrchestrator()
        
        agent1 = MockAgent("Agent1")
        orchestrator.register_agent("agent1", agent1)
        
        status = orchestrator.get_agent_status()
        
        assert "agent1" in status
        assert status["agent1"] == "ready"


class TestRetryHandler:
    """Tests for RetryHandler."""
    
    def test_retry_handler_initialization(self):
        """Test retry handler initialization."""
        handler = RetryHandler(max_retries=5)
        
        assert handler.max_retries == 5
        assert handler.base_delay == 1.0
        assert handler.retry_count == 0
    
    def test_classify_error_critical(self):
        """Test classifying critical errors."""
        handler = RetryHandler()
        
        error = KeyboardInterrupt()
        severity = handler.classify_error(error)
        
        assert severity == ErrorSeverity.CRITICAL
    
    def test_classify_error_high(self):
        """Test classifying high severity errors."""
        handler = RetryHandler()
        
        error = Exception("rate limit exceeded")
        severity = handler.classify_error(error)
        
        assert severity == ErrorSeverity.HIGH
    
    def test_classify_error_medium(self):
        """Test classifying medium severity errors."""
        handler = RetryHandler()
        
        error = ConnectionError("connection timeout")
        severity = handler.classify_error(error)
        
        assert severity == ErrorSeverity.MEDIUM
    
    def test_classify_error_low(self):
        """Test classifying low severity errors."""
        handler = RetryHandler()
        
        error = ValueError("invalid value")
        severity = handler.classify_error(error)
        
        assert severity == ErrorSeverity.LOW
    
    def test_calculate_delay(self):
        """Test calculating delay."""
        handler = RetryHandler(base_delay=1.0)
        
        # First retry
        delay1 = handler.calculate_delay(0, ErrorSeverity.MEDIUM)
        assert delay1 == 1.0
        
        # Second retry (exponential backoff)
        delay2 = handler.calculate_delay(1, ErrorSeverity.MEDIUM)
        assert delay2 == 2.0
        
        # Third retry
        delay3 = handler.calculate_delay(2, ErrorSeverity.MEDIUM)
        assert delay3 == 4.0
    
    def test_calculate_delay_critical(self):
        """Test calculating delay for critical errors."""
        handler = RetryHandler()
        
        delay = handler.calculate_delay(0, ErrorSeverity.CRITICAL)
        
        assert delay == 0.0
    
    def test_should_retry_critical(self):
        """Test should not retry critical errors."""
        handler = RetryHandler()
        
        error = KeyboardInterrupt()
        should_retry = handler.should_retry(error, 0)
        
        assert should_retry is False
    
    def test_should_retry_max_attempts(self):
        """Test should not retry after max attempts."""
        handler = RetryHandler(max_retries=3)
        
        error = ValueError("test")
        should_retry = handler.should_retry(error, 3)
        
        assert should_retry is False
    
    def test_should_retry_valid(self):
        """Test should retry valid errors."""
        handler = RetryHandler()
        
        error = ValueError("test")
        should_retry = handler.should_retry(error, 1)
        
        assert should_retry is True
    
    def test_execute_with_retry_success(self):
        """Test executing function with retry - success."""
        handler = RetryHandler()
        
        call_count = [0]
        
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("temporary error")
            return "success"
        
        result = handler.execute_with_retry(flaky_function)
        
        assert result == "success"
        assert call_count[0] == 2
    
    def test_execute_with_retry_fallback(self):
        """Test executing with retry using fallback."""
        handler = RetryHandler(max_retries=1)
        
        def always_fail():
            raise ValueError("always fails")
        
        def fallback():
            return "fallback_result"
        
        result = handler.execute_with_retry(always_fail, fallback=fallback)
        
        assert result == "fallback_result"
    
    def test_get_error_history(self):
        """Test getting error history."""
        handler = RetryHandler(max_retries=1)
        
        def fail_once():
            raise ValueError("test error")
        
        try:
            handler.execute_with_retry(fail_once)
        except:
            pass
        
        history = handler.get_error_history()
        
        assert len(history) > 0
        assert 'error' in history[0]
    
    def test_reset(self):
        """Test resetting handler."""
        handler = RetryHandler()
        handler.retry_count = 5
        handler.error_history = [{'error': 'test'}]
        
        handler.reset()
        
        assert handler.retry_count == 0
        assert handler.error_history == []


class TestHITLSystem:
    """Tests for HITLSystem."""
    
    def test_hitl_initialization(self):
        """Test HITL system initialization."""
        hitl = HITLSystem(confidence_threshold=0.8)
        
        assert hitl.confidence_threshold == 0.8
        assert hitl.review_history == []
    
    def test_needs_review_low_confidence(self):
        """Test needs review for low confidence."""
        hitl = HITLSystem(confidence_threshold=0.7)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        unit.confidence_score = 0.5
        
        state = TransmuteState(session_id="test")
        
        needs_review = hitl.needs_review(unit, state)
        
        assert needs_review is True
    
    def test_needs_review_high_confidence(self):
        """Test does not need review for high confidence."""
        hitl = HITLSystem(confidence_threshold=0.7)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        unit.confidence_score = 0.9
        
        state = TransmuteState(session_id="test")
        
        needs_review = hitl.needs_review(unit, state)
        
        assert needs_review is False
    
    def test_needs_review_failed_status(self):
        """Test needs review for failed status."""
        hitl = HITLSystem()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        unit.status = "failed"
        
        state = TransmuteState(session_id="test")
        
        needs_review = hitl.needs_review(unit, state)
        
        assert needs_review is True
    
    def test_request_review_with_callback(self):
        """Test requesting review with callback."""
        def review_callback(data):
            return ReviewDecision.APPROVE
        
        hitl = HITLSystem(review_callback=review_callback)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        
        decision = hitl.request_review(unit)
        
        assert decision == ReviewDecision.APPROVE
        assert len(hitl.review_history) == 1
    
    def test_request_review_no_callback(self):
        """Test requesting review without callback."""
        hitl = HITLSystem()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        
        decision = hitl.request_review(unit)
        
        assert decision == ReviewDecision.APPROVE  # Auto-approve
    
    def test_apply_correction(self):
        """Test applying correction."""
        hitl = HITLSystem()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        unit.translated_code = "original code"
        
        hitl.apply_correction(unit, "corrected code", "Fixed bug")
        
        assert unit.translated_code == "corrected code"
        assert unit.confidence_score == 1.0
        assert unit.metadata.get('human_reviewed') is True
        assert len(hitl.corrections) == 1
    
    def test_get_review_statistics(self):
        """Test getting review statistics."""
        def review_callback(data):
            return ReviewDecision.APPROVE
        
        hitl = HITLSystem(review_callback=review_callback)
        
        unit1 = TranslationUnit(unit_id="1", source_path=Path("test1.py"))
        unit2 = TranslationUnit(unit_id="2", source_path=Path("test2.py"))
        
        hitl.request_review(unit1)
        hitl.request_review(unit2)
        
        stats = hitl.get_review_statistics()
        
        assert stats['total_reviews'] == 2
        assert stats['approval_rate'] == 1.0
    
    def test_export_corrections(self, tmp_path):
        """Test exporting corrections."""
        hitl = HITLSystem()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
        )
        
        hitl.apply_correction(unit, "corrected", "note")
        
        output_file = tmp_path / "corrections.json"
        count = hitl.export_corrections(output_file)
        
        assert count == 1
        assert output_file.exists()


class TestMiddleware:
    """Tests for Middleware system."""
    
    def test_code_normalization_middleware(self):
        """Test code normalization middleware."""
        middleware = CodeNormalizationMiddleware()
        
        code = "def hello():  \n\n\n    print('hi')  \n"
        normalized = middleware.process(code)
        
        assert "  \n" not in normalized  # No trailing whitespace
        assert "\n\n\n" not in normalized  # No triple newlines
    
    def test_comment_preservation_middleware(self):
        """Test comment preservation middleware."""
        middleware = CommentPreservationMiddleware()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py"),
            source_code="# Important comment\ndef hello():\n    pass"
        )
        
        result = middleware.process(unit)
        
        assert 'preserved_comments' in result.metadata
        assert len(result.metadata['preserved_comments']) > 0
    
    def test_quality_check_middleware(self):
        """Test quality check middleware."""
        middleware = QualityCheckMiddleware(min_quality=0.5)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py"),
            translated_code="public class Test { }"
        )
        
        result = middleware.process(unit)
        
        assert 'quality_score' in result.metadata
        assert result.metadata['quality_score'] > 0
    
    def test_quality_check_low_quality(self):
        """Test quality check with low quality code."""
        middleware = QualityCheckMiddleware(min_quality=0.8)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py"),
            translated_code="// TODO: implement"
        )
        
        result = middleware.process(unit)
        
        assert result.metadata.get('needs_review') is True
    
    def test_middleware_pipeline(self):
        """Test middleware pipeline."""
        pipeline = MiddlewarePipeline("TestPipeline")
        
        pipeline.add(CodeNormalizationMiddleware())
        pipeline.add(CommentPreservationMiddleware())
        
        assert len(pipeline.middlewares) == 2
    
    def test_pipeline_process(self):
        """Test processing through pipeline."""
        pipeline = MiddlewarePipeline()
        
        middleware1 = CodeNormalizationMiddleware()
        middleware2 = QualityCheckMiddleware()
        
        pipeline.add(middleware1).add(middleware2)
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py"),
            translated_code="public class Test {  \n\n\n}"
        )
        
        result = pipeline.process(unit)
        
        assert 'quality_score' in result.metadata
    
    def test_pipeline_remove(self):
        """Test removing middleware from pipeline."""
        pipeline = MiddlewarePipeline()
        
        middleware = CodeNormalizationMiddleware()
        pipeline.add(middleware)
        
        removed = pipeline.remove("CodeNormalization")
        
        assert removed is True
        assert len(pipeline.middlewares) == 0
    
    def test_pipeline_enable_disable(self):
        """Test enabling/disabling middleware."""
        pipeline = MiddlewarePipeline()
        
        middleware = CodeNormalizationMiddleware()
        pipeline.add(middleware)
        
        pipeline.disable_all()
        assert middleware.enabled is False
        
        pipeline.enable_all()
        assert middleware.enabled is True
    
    def test_pipeline_get_enabled(self):
        """Test getting enabled middleware."""
        pipeline = MiddlewarePipeline()
        
        middleware1 = CodeNormalizationMiddleware()
        middleware2 = QualityCheckMiddleware()
        
        pipeline.add(middleware1).add(middleware2)
        
        middleware1.enabled = False
        
        enabled = pipeline.get_enabled()
        
        assert len(enabled) == 1
        assert "QualityCheck" in enabled