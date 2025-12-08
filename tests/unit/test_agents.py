"""
Tests for agents.
"""

import pytest
from pathlib import Path
import tempfile

from transmute.agents.base import BaseAgent
from transmute.agents.planning_agent import PlanningAgent
from transmute.agents.validation_agent import ValidationAgent
from transmute.agents.analysis_agent import AnalysisAgent 
from transmute.agents.translation_agent import TranslationAgent  
from transmute.languages.registry import LanguageRegistry 
from transmute.core.state import (
    TransmuteState,
    LanguageInfo,
    FeatureProfile,
    TranslationUnit,
    MigrationPlan,
)


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def process(self, state: TransmuteState):
        return {"current_step": "test"}


class TestBaseAgent:
    """Tests for BaseAgent."""
    
    def test_base_agent_initialization(self):
        """Test base agent initialization."""
        agent = MockAgent("TestAgent")
        
        assert agent.name == "TestAgent"
    
    def test_base_agent_callable(self):
        """Test that agent is callable."""
        agent = MockAgent("TestAgent")
        state = TransmuteState(session_id="test")
        
        result = agent(state)
        
        assert isinstance(result, dict)
        assert "current_step" in result


class TestPlanningAgent:
    """Tests for PlanningAgent."""
    
    def test_planning_agent_initialization(self):
        """Test planning agent initialization."""
        agent = PlanningAgent()
        
        assert agent.name == "PlanningAgent"
    
    def test_planning_agent_creates_plan(self):
        """Test that planning agent creates a migration plan."""
        agent = PlanningAgent()
        
        state = TransmuteState(
            session_id="test",
            source_language=LanguageInfo(name="python"),
            target_language=LanguageInfo(name="java"),
            feature_profile=FeatureProfile(
                language="python",
                complexity_score=0.5
            ),
            metadata={
                "file_map": {
                    "python": ["test1.py", "test2.py", "test3.py"]
                }
            }
        )
        
        result = agent.process(state)
        
        assert "migration_plan" in result
        plan = result["migration_plan"]
        
        assert plan.total_units == 3
        assert plan.source_language == "python"
        assert plan.target_language == "java"
        assert len(plan.translation_units) == 3
    
    def test_planning_agent_missing_languages(self):
        """Test planning agent with missing language info."""
        agent = PlanningAgent()
        
        state = TransmuteState(session_id="test")
        
        result = agent.process(state)
        
        assert "errors" in result
        assert "current_step" in result
        assert result["current_step"] == "error"


class TestValidationAgent:
    """Tests for ValidationAgent."""
    
    def test_validation_agent_initialization(self):
        """Test validation agent initialization."""
        agent = ValidationAgent()
        
        assert agent.name == "ValidationAgent"
    
    def test_validation_agent_no_plan(self):
        """Test validation with no plan."""
        agent = ValidationAgent()
        state = TransmuteState(session_id="test")
        
        result = agent.process(state)
        
        assert "errors" in result
        assert result["current_step"] == "error"
    
    def test_validation_agent_empty_plan(self):
        """Test validation with empty plan."""
        agent = ValidationAgent()
        
        plan = MigrationPlan(
            plan_id="test",
            source_language="python",
            target_language="java",
            total_units=0,
            translation_units=[]
        )
        
        state = TransmuteState(
            session_id="test",
            migration_plan=plan
        )
        
        result = agent.process(state)
        
        assert result["current_step"] == "completed"
    
    def test_validation_agent_with_completed_unit(self):
        """Test validation with completed unit."""
        agent = ValidationAgent()
        
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py"),
            source_code="def hello(): pass",
            translated_code="public void hello() {}"
        )
        unit.mark_completed()
        
        plan = MigrationPlan(
            plan_id="test",
            source_language="python",
            target_language="java",
            total_units=1,
            translation_units=[unit]
        )
        
        state = TransmuteState(
            session_id="test",
            source_language=LanguageInfo(name="python"),
            target_language=LanguageInfo(name="java"),
            migration_plan=plan
        )
        
        result = agent.process(state)
        
        assert "validation_results" in result
        assert len(result["validation_results"]) == 1
        assert "average_quality" in result["metadata"]


class TestEnhancedAgentMethods:
    """Tests for enhanced agent methods."""
    
    def test_analysis_agent_file_statistics(self):
        """Test get_file_statistics."""
        registry = LanguageRegistry(Path("config/languages"))
        agent = AnalysisAgent(registry)
        
        file_map = {
            'python': ['test1.py', 'test2.py'],
            'java': ['Test.java']
        }
        
        stats = agent.get_file_statistics(file_map)
        
        assert stats['total_files'] == 3
        assert 'languages' in stats
        assert stats['languages']['python']['file_count'] == 2
    
    def test_analysis_agent_validate_repository(self):
        """Test validate_repository."""
        registry = LanguageRegistry(Path("config/languages"))
        agent = AnalysisAgent(registry)
        
        assert agent.validate_repository("https://github.com/user/repo") is True
        assert agent.validate_repository("git@github.com:user/repo.git") is True
        assert agent.validate_repository("invalid") is False
        assert agent.validate_repository("") is False
    
    def test_planning_agent_estimate_difficulty(self):
        """Test estimate_difficulty."""
        agent = PlanningAgent()
        
        assert agent.estimate_difficulty(0.2) == "easy"
        assert agent.estimate_difficulty(0.5) == "medium"
        assert agent.estimate_difficulty(0.7) == "hard"
        assert agent.estimate_difficulty(0.9) == "very_hard"
    
    def test_translation_agent_calculate_confidence(self):
        """Test calculate_translation_confidence."""
        agent = TranslationAgent()
        
        source = "def hello(): pass"
        translated = "public void hello() {}"
        
        confidence = agent.calculate_translation_confidence(source, translated)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have reasonable confidence
    
    def test_translation_agent_get_progress(self):
        """Test get_translation_progress."""
        agent = TranslationAgent()
        
        unit1 = TranslationUnit(unit_id="1", source_path=Path("test1.py"))
        unit2 = TranslationUnit(unit_id="2", source_path=Path("test2.py"))
        unit1.mark_completed()
        
        plan = MigrationPlan(
            plan_id="test",
            source_language="python",
            target_language="java",
            total_units=2,
            translation_units=[unit1, unit2]
        )
        
        progress = agent.get_translation_progress(plan)
        
        assert progress['completed'] == 1
        assert progress['pending'] == 1
        assert progress['total'] == 2
        assert progress['percentage'] == 50.0