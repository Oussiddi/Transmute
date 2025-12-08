"""
Tests for workflows.
"""

import pytest
from pathlib import Path
import tempfile

from transmute.workflows import TransmuteWorkflow
from transmute.languages.registry import LanguageRegistry
from transmute.languages.plugins import PythonPlugin, JavaPlugin
from transmute.core.state import TransmuteState, LanguageInfo, MigrationPlan, TranslationUnit


class TestTransmuteWorkflow:
    """Tests for TransmuteWorkflow."""
    
    @pytest.fixture
    def language_registry(self):
        """Create language registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create Python config
            python_config = config_dir / "python.yaml"
            python_config.write_text("""
name: python
display_name: Python
version: "3.11"
extensions:
  - .py
features:
  - classes
  - functions
""")
            
            # Create Java config
            java_config = config_dir / "java.yaml"
            java_config.write_text("""
name: java
display_name: Java
version: "17"
extensions:
  - .java
features:
  - classes
  - interfaces
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("python", PythonPlugin)
            registry.register_plugin("java", JavaPlugin)
            
            yield registry
    
    def test_workflow_initialization(self, language_registry):
        """Test workflow initialization."""
        workflow = TransmuteWorkflow(language_registry)
        
        assert workflow.language_registry == language_registry
        assert workflow.analysis_agent is not None
        assert workflow.planning_agent is not None
        assert workflow.translation_agent is not None
        assert workflow.graph is not None
    
    def test_should_continue_translation_complete(self, language_registry):
        """Test should_continue when all units are complete."""
        workflow = TransmuteWorkflow(language_registry)
        
        # Create state with completed plan
        unit = TranslationUnit(
            unit_id="test",
            source_path=Path("test.py")
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
            migration_plan=plan
        )
        
        result = workflow._should_continue_translation(state)
        
        assert result == "complete"
    
    def test_should_continue_translation_pending(self, language_registry):
        """Test should_continue when units are pending."""
        workflow = TransmuteWorkflow(language_registry)
        
        # Create state with pending units
        unit1 = TranslationUnit(unit_id="test1", source_path=Path("test1.py"))
        unit2 = TranslationUnit(unit_id="test2", source_path=Path("test2.py"))
        unit1.mark_completed()
        # unit2 is still pending
        
        plan = MigrationPlan(
            plan_id="test",
            source_language="python",
            target_language="java",
            total_units=2,
            translation_units=[unit1, unit2]
        )
        
        state = TransmuteState(
            session_id="test",
            migration_plan=plan
        )
        
        result = workflow._should_continue_translation(state)
        
        assert result == "continue"
    
    def test_should_continue_translation_error(self, language_registry):
        """Test should_continue with errors."""
        workflow = TransmuteWorkflow(language_registry)
        
        state = TransmuteState(
            session_id="test",
            errors=["Test error"]
        )
        
        result = workflow._should_continue_translation(state)
        
        assert result == "error"
    
    def test_get_status(self, language_registry):
        """Test get_status method."""
        workflow = TransmuteWorkflow(language_registry)
        
        state = TransmuteState(session_id="test")
        
        status = workflow.get_status(state)
        
        assert status["session_id"] == "test"
        assert status["current_step"] == "init"
        assert status["is_completed"] is False
        assert status["has_errors"] is False
    
    def test_generate_summary(self, language_registry):
        """Test summary generation."""
        workflow = TransmuteWorkflow(language_registry)
        
        state = TransmuteState(
            session_id="test",
            source_language=LanguageInfo(name="python"),
            target_language=LanguageInfo(name="java")
        )
        
        summary = workflow._generate_summary(state)
        
        assert "TRANSMUTE WORKFLOW SUMMARY" in summary
        assert "python → java" in summary
    
    def test_export_results(self, language_registry):
        """Test exporting results."""
        workflow = TransmuteWorkflow(language_registry)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            
            state = TransmuteState(session_id="test")
            
            result_path = workflow.export_results(state, output_dir)
            
            assert result_path.exists()
            assert (output_dir / "summary.txt").exists()