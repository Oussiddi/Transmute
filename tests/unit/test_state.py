"""
Tests for state definitions.
"""

import pytest
from pathlib import Path
from datetime import datetime

from transmute.core.state import (
    RepositoryMetadata,
    LanguageInfo,
    FeatureProfile,
    FeatureType,
    TranslationUnit,
    TranslationStatus,
    TranslationStrategy,
    StrategyType,
    ValidationResult,
    MigrationPlan,
    TransmuteState,
)


class TestRepositoryMetadata:
    """Tests for RepositoryMetadata model."""
    
    def test_repository_metadata_minimal(self):
        """Test RepositoryMetadata with minimal fields."""
        repo = RepositoryMetadata(
            url="https://github.com/user/repo",
            platform="github"
        )
        
        assert repo.url == "https://github.com/user/repo"
        assert repo.platform == "github"
        assert repo.default_branch == "main"
        assert repo.total_files == 0
    
    def test_repository_metadata_full(self):
        """Test RepositoryMetadata with all fields."""
        repo = RepositoryMetadata(
            url="https://gitlab.com/user/project",
            platform="gitlab",
            local_path=Path("/tmp/repo"),
            default_branch="master",
            total_commits=150,
            total_files=50,
            total_lines=5000,
            size_mb=2.5,
            primary_language="python",
            language_distribution={"python": 80.0, "yaml": 20.0}
        )
        
        assert repo.platform == "gitlab"
        assert repo.total_commits == 150
        assert repo.primary_language == "python"
        assert repo.language_distribution["python"] == 80.0
    
    def test_repository_metadata_invalid_platform(self):
        """Test that invalid platform raises error."""
        with pytest.raises(ValueError, match="Platform must be one of"):
            RepositoryMetadata(
                url="https://example.com/repo",
                platform="invalid"
            )
    
    def test_repository_metadata_platform_case_insensitive(self):
        """Test that platform is converted to lowercase."""
        repo = RepositoryMetadata(
            url="https://github.com/user/repo",
            platform="GitHub"
        )
        assert repo.platform == "github"


class TestLanguageInfo:
    """Tests for LanguageInfo model."""
    
    def test_language_info_minimal(self):
        """Test LanguageInfo with minimal fields."""
        lang = LanguageInfo(name="python")
        
        assert lang.name == "python"
        assert lang.file_count == 0
        assert lang.line_count == 0
        assert lang.percentage == 0.0
    
    def test_language_info_full(self):
        """Test LanguageInfo with all fields."""
        lang = LanguageInfo(
            name="java",
            version="17",
            file_count=45,
            line_count=12000,
            percentage=85.5,
            extensions=[".java"],
            features_detected=["classes", "generics", "annotations"]
        )
        
        assert lang.name == "java"
        assert lang.version == "17"
        assert lang.file_count == 45
        assert lang.percentage == 85.5
        assert "generics" in lang.features_detected
    
    def test_language_info_percentage_validation(self):
        """Test that percentage is validated."""
        # Should work
        lang = LanguageInfo(name="python", percentage=50.0)
        assert lang.percentage == 50.0
        
        # Out of range should fail
        with pytest.raises(ValueError):
            LanguageInfo(name="python", percentage=150.0)
        
        with pytest.raises(ValueError):
            LanguageInfo(name="python", percentage=-10.0)


class TestFeatureProfile:
    """Tests for FeatureProfile model."""
    
    def test_feature_profile_minimal(self):
        """Test FeatureProfile with minimal fields."""
        profile = FeatureProfile(language="java")
        
        assert profile.language == "java"
        assert profile.complexity_score == 0.0
        assert len(profile.features_used) == 0
    
    def test_feature_profile_with_features(self):
        """Test FeatureProfile with features."""
        profile = FeatureProfile(
            language="python",
            features_used={"classes": 10, "async": 5, "decorators": 15},
            complexity_score=0.7,
            patterns_detected=["Singleton", "Factory"],
            external_dependencies=["flask", "sqlalchemy"]
        )
        
        assert profile.features_used["classes"] == 10
        assert profile.complexity_score == 0.7
        assert "Singleton" in profile.patterns_detected
    
    def test_feature_profile_has_feature(self):
        """Test has_feature method."""
        profile = FeatureProfile(
            language="java",
            features_used={"classes": 5, "generics": 0}
        )
        
        assert profile.has_feature("classes") is True
        assert profile.has_feature("generics") is False
        assert profile.has_feature("nonexistent") is False
    
    def test_feature_profile_get_feature_count(self):
        """Test get_feature_count method."""
        profile = FeatureProfile(
            language="java",
            features_used={"classes": 10, "interfaces": 3}
        )
        
        assert profile.get_feature_count("classes") == 10
        assert profile.get_feature_count("interfaces") == 3
        assert profile.get_feature_count("nonexistent") == 0
    
    def test_feature_profile_top_features(self):
        """Test top_features method."""
        profile = FeatureProfile(
            language="python",
            features_used={
                "classes": 20,
                "functions": 50,
                "decorators": 15,
                "async": 30,
                "generators": 5
            }
        )
        
        top_3 = profile.top_features(n=3)
        
        assert len(top_3) == 3
        assert top_3[0] == ("functions", 50)
        assert top_3[1] == ("async", 30)
        assert top_3[2] == ("classes", 20)


class TestTranslationUnit:
    """Tests for TranslationUnit model."""
    
    def test_translation_unit_minimal(self):
        """Test TranslationUnit with minimal fields."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("src/Main.java")
        )
        
        assert unit.unit_id == "unit_001"
        assert unit.source_path == Path("src/Main.java")
        assert unit.status == TranslationStatus.PENDING
        assert unit.priority == 0
    
    def test_translation_unit_full(self):
        """Test TranslationUnit with all fields."""
        unit = TranslationUnit(
            unit_id="unit_002",
            source_path=Path("src/Utils.java"),
            target_path=Path("src/utils.py"),
            status=TranslationStatus.COMPLETED,
            dependencies=["unit_001"],
            dependents=["unit_003"],
            priority=5,
            complexity=0.8,
            source_code="public class Utils {}",
            translated_code="class Utils: pass",
            translation_strategy="direct",
            confidence_score=0.95
        )
        
        assert unit.status == TranslationStatus.COMPLETED
        assert unit.priority == 5
        assert unit.confidence_score == 0.95
        assert "unit_001" in unit.dependencies
    
    def test_translation_unit_is_ready_for_translation(self):
        """Test is_ready_for_translation method."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java")
        )
        
        assert unit.is_ready_for_translation() is True
        
        unit.status = TranslationStatus.IN_PROGRESS
        assert unit.is_ready_for_translation() is False
    
    def test_translation_unit_mark_in_progress(self):
        """Test mark_in_progress method."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java")
        )
        
        unit.mark_in_progress()
        assert unit.status == TranslationStatus.IN_PROGRESS
    
    def test_translation_unit_mark_completed(self):
        """Test mark_completed method."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java")
        )
        
        unit.mark_completed()
        assert unit.status == TranslationStatus.COMPLETED
    
    def test_translation_unit_mark_failed(self):
        """Test mark_failed method."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java")
        )
        
        unit.mark_failed("Compilation error")
        
        assert unit.status == TranslationStatus.FAILED
        assert "Compilation error" in unit.errors
    
    def test_translation_unit_complexity_validation(self):
        """Test that complexity is validated."""
        # Valid complexity
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java"),
            complexity=0.5
        )
        assert unit.complexity == 0.5
        
        # Out of range should fail
        with pytest.raises(ValueError):
            TranslationUnit(
                unit_id="unit_001",
                source_path=Path("test.java"),
                complexity=1.5
            )

class TestTranslationStrategy:
    """Tests for TranslationStrategy model."""
    
    def test_translation_strategy_minimal(self):
        """Test TranslationStrategy with minimal fields."""
        strategy = TranslationStrategy(
            strategy_type=StrategyType.DIRECT,
            confidence=0.9,
            reasoning="Simple code with direct equivalents"
        )
        
        assert strategy.strategy_type == StrategyType.DIRECT
        assert strategy.confidence == 0.9
        assert strategy.requires_rag is False
        assert strategy.requires_refactoring is False
    
    def test_translation_strategy_full(self):
        """Test TranslationStrategy with all fields."""
        strategy = TranslationStrategy(
            strategy_type=StrategyType.PATTERN,
            confidence=0.75,
            reasoning="Uses complex patterns requiring RAG",
            requires_rag=True,
            requires_refactoring=False,
            estimated_difficulty=0.6,
            recommended_patterns=["Factory", "Singleton"]
        )
        
        assert strategy.strategy_type == StrategyType.PATTERN
        assert strategy.requires_rag is True
        assert len(strategy.recommended_patterns) == 2


class TestValidationResult:
    """Tests for ValidationResult model."""
    
    def test_validation_result_success(self):
        """Test ValidationResult for successful validation."""
        result = ValidationResult(
            is_valid=True,
            compilation_successful=True,
            tests_passed=10,
            tests_failed=0,
            quality_score=0.95
        )
        
        assert result.is_valid is True
        assert result.compilation_successful is True
        assert result.test_pass_rate == 1.0
    
    def test_validation_result_failure(self):
        """Test ValidationResult for failed validation."""
        result = ValidationResult(
            is_valid=False,
            compilation_successful=False,
            tests_passed=5,
            tests_failed=5,
            compilation_errors=["Syntax error on line 10"]
        )
        
        assert result.is_valid is False
        assert result.test_pass_rate == 0.5
        assert len(result.compilation_errors) == 1
    
    def test_validation_result_test_pass_rate_zero_tests(self):
        """Test test_pass_rate with no tests."""
        result = ValidationResult(
            is_valid=True,
            compilation_successful=True
        )
        
        assert result.test_pass_rate == 0.0


class TestMigrationPlan:
    """Tests for MigrationPlan model."""
    
    def test_migration_plan_minimal(self):
        """Test MigrationPlan with minimal fields."""
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python"
        )
        
        assert plan.plan_id == "plan_001"
        assert plan.source_language == "java"
        assert plan.total_units == 0
        assert plan.completion_percentage == 0.0
    
    def test_migration_plan_with_units(self):
        """Test MigrationPlan with translation units."""
        unit1 = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("Main.java"),
            status=TranslationStatus.COMPLETED
        )
        unit2 = TranslationUnit(
            unit_id="unit_002",
            source_path=Path("Utils.java"),
            status=TranslationStatus.PENDING
        )
        
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python",
            total_units=2,
            translation_units=[unit1, unit2],
            execution_order=["unit_001", "unit_002"]
        )
        
        assert plan.total_units == 2
        assert len(plan.translation_units) == 2
        assert plan.completion_percentage == 50.0
    
    def test_migration_plan_get_unit(self):
        """Test get_unit method."""
        unit = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test.java")
        )
        
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python",
            translation_units=[unit]
        )
        
        found = plan.get_unit("unit_001")
        assert found is not None
        assert found.unit_id == "unit_001"
        
        not_found = plan.get_unit("nonexistent")
        assert not_found is None
    
    def test_migration_plan_get_pending_units(self):
        """Test get_pending_units method."""
        unit1 = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test1.java"),
            status=TranslationStatus.PENDING
        )
        unit2 = TranslationUnit(
            unit_id="unit_002",
            source_path=Path("test2.java"),
            status=TranslationStatus.COMPLETED
        )
        
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python",
            translation_units=[unit1, unit2]
        )
        
        pending = plan.get_pending_units()
        assert len(pending) == 1
        assert pending[0].unit_id == "unit_001"
    
    def test_migration_plan_get_completed_units(self):
        """Test get_completed_units method."""
        unit1 = TranslationUnit(
            unit_id="unit_001",
            source_path=Path("test1.java"),
            status=TranslationStatus.PENDING
        )
        unit2 = TranslationUnit(
            unit_id="unit_002",
            source_path=Path("test2.java"),
            status=TranslationStatus.COMPLETED
        )
        
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python",
            translation_units=[unit1, unit2]
        )
        
        completed = plan.get_completed_units()
        assert len(completed) == 1
        assert completed[0].unit_id == "unit_002"


class TestTransmuteState:
    """Tests for TransmuteState model."""
    
    def test_transmute_state_minimal(self):
        """Test TransmuteState with minimal fields."""
        state = TransmuteState(session_id="session_001")
        
        assert state.session_id == "session_001"
        assert state.current_step == "init"
        assert len(state.messages) == 0
        assert state.is_completed is False
    
    def test_transmute_state_add_message(self):
        """Test add_message method."""
        state = TransmuteState(session_id="session_001")
        
        state.add_message("user", "Start migration")
        state.add_message("assistant", "Starting...")
        
        assert len(state.messages) == 2
        assert state.messages[0]["role"] == "user"
        assert state.messages[1]["role"] == "assistant"
    
    def test_transmute_state_add_error(self):
        """Test add_error method."""
        state = TransmuteState(session_id="session_001")
        
        state.add_error("Compilation failed")
        
        assert len(state.errors) == 1
        assert "Compilation failed" in state.errors
    
    def test_transmute_state_add_warning(self):
        """Test add_warning method."""
        state = TransmuteState(session_id="session_001")
        
        state.add_warning("Deprecated feature used")
        
        assert len(state.warnings) == 1
        assert "Deprecated feature used" in state.warnings
    
    def test_transmute_state_mark_completed(self):
        """Test mark_completed method."""
        state = TransmuteState(session_id="session_001")
        
        assert state.is_completed is False
        
        state.mark_completed()
        
        assert state.is_completed is True
        assert state.completed_at is not None
    
    def test_transmute_state_duration(self):
        """Test duration_seconds property."""
        state = TransmuteState(session_id="session_001")
        
        # Duration should be > 0 even without completion
        duration = state.duration_seconds
        assert duration >= 0
    
    def test_transmute_state_with_full_workflow(self):
        """Test TransmuteState with complete workflow data."""
        repo = RepositoryMetadata(
            url="https://github.com/user/repo",
            platform="github"
        )
        
        source_lang = LanguageInfo(name="java", version="17")
        target_lang = LanguageInfo(name="python", version="3.11")
        
        plan = MigrationPlan(
            plan_id="plan_001",
            source_language="java",
            target_language="python"
        )
        
        state = TransmuteState(
            session_id="session_001",
            repository=repo,
            source_language=source_lang,
            target_language=target_lang,
            migration_plan=plan,
            current_step="translation"
        )
        
        assert state.repository.platform == "github"
        assert state.source_language.name == "java"
        assert state.target_language.name == "python"
        assert state.migration_plan.plan_id == "plan_001"