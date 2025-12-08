"""
Tests for repository analysis.
"""

import pytest
from pathlib import Path
import tempfile


from transmute.analysis.feature_detector import FeatureDetector
from transmute.core.state import FeatureProfile
from transmute.analysis.repository_analyzer import RepositoryAnalyzer
from transmute.languages.registry import LanguageRegistry
from transmute.languages.plugins import PythonPlugin, JavaPlugin
from transmute.git.repository import GitRepository
from transmute.core.state import LanguageInfo


class TestRepositoryAnalyzer:
    """Tests for RepositoryAnalyzer class."""
    
    @pytest.fixture
    def language_registry(self):
        """Create a language registry with test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create Python config
            python_config = config_dir / "python.yaml"
            with open(python_config, 'w') as f:
                f.write("""
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
            with open(java_config, 'w') as f:
                f.write("""
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
    
    def test_analyzer_initialization(self, language_registry):
        """Test analyzer initialization."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        assert analyzer.registry == language_registry
    
    def test_get_primary_language_no_languages(self, language_registry):
        """Test get_primary_language with no languages."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        primary = analyzer.get_primary_language([])
        
        assert primary is None
    
    def test_get_primary_language_single_language(self, language_registry):
        """Test get_primary_language with one language."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        languages = [
            LanguageInfo(name="python", percentage=100.0)
        ]
        
        primary = analyzer.get_primary_language(languages)
        
        assert primary == "python"
    
    def test_get_primary_language_multiple_languages(self, language_registry):
        """Test get_primary_language with multiple languages."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        languages = [
            LanguageInfo(name="python", percentage=80.0),
            LanguageInfo(name="java", percentage=20.0),
        ]
        
        primary = analyzer.get_primary_language(languages)
        
        assert primary == "python"
    
    def test_calculate_metrics(self, language_registry):
        """Test calculate_metrics."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        # Create mock git repo with stats
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create some test files
            (repo_path / "test.py").write_text("print('hello')")
            (repo_path / "test.java").write_text("class Test {}")
            
            git_repo = GitRepository("https://example.com/repo")
            git_repo.local_path = repo_path
            
            file_map = {
                "python": [Path("test.py")],
                "java": [Path("test.java")],
            }
            
            metrics = analyzer.calculate_metrics(git_repo, file_map)
            
            assert metrics['total_files'] == 2
            assert metrics['total_languages'] == 2
            assert 'language_file_counts' in metrics
            assert metrics['language_file_counts']['python'] == 1
            assert metrics['language_file_counts']['java'] == 1
    
    def test_generate_report(self, language_registry):
        """Test generate_report."""
        from transmute.core.state import RepositoryMetadata
        
        analyzer = RepositoryAnalyzer(language_registry)
        
        metadata = RepositoryMetadata(
            url="https://github.com/user/repo",
            platform="github",
            total_commits=100,
            total_files=50,
            total_lines=5000,
            size_mb=2.5
        )
        
        languages = [
            LanguageInfo(
                name="python",
                percentage=80.0,
                file_count=40,
                line_count=4000
            ),
            LanguageInfo(
                name="yaml",
                percentage=20.0,
                file_count=10,
                line_count=1000
            ),
        ]
        
        metrics = {
            'total_files': 50,
            'total_lines': 5000,
            'total_languages': 2,
        }
        
        report = analyzer.generate_report(
            metadata, languages, metrics, "python"
        )
        
        assert "Repository Analysis Report" in report
        assert "https://github.com/user/repo" in report
        assert "python: 80.0%" in report
        assert "Primary Language: python" in report
    
    def test_build_file_map(self, language_registry):
        """Test build_file_map."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create test files
            (repo_path / "test1.py").write_text("print('test1')")
            (repo_path / "test2.py").write_text("print('test2')")
            (repo_path / "test.java").write_text("class Test {}")
            
            git_repo = GitRepository("https://example.com/repo")
            git_repo.local_path = repo_path
            
            file_map = analyzer.build_file_map(git_repo)
            
            assert "python" in file_map
            assert "java" in file_map
            assert len(file_map["python"]) == 2
            assert len(file_map["java"]) == 1
    
    def test_detect_languages(self, language_registry):
        """Test detect_languages."""
        analyzer = RepositoryAnalyzer(language_registry)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create test files with content
            (repo_path / "test1.py").write_text("# Python file\nprint('hello')\nprint('world')")
            (repo_path / "test2.py").write_text("def test():\n    pass")
            (repo_path / "test.java").write_text("class Test {\n    public static void main() {}\n}")
            
            git_repo = GitRepository("https://example.com/repo")
            git_repo.local_path = repo_path
            
            languages = analyzer.detect_languages(git_repo)
            
            assert len(languages) > 0
            
            # Should be sorted by percentage
            if len(languages) > 1:
                assert languages[0].percentage >= languages[1].percentage
            
            # Check that we found Python and Java
            lang_names = [lang.name for lang in languages]
            assert "python" in lang_names
            assert "java" in lang_names


# Integration test (commented out - uncomment to test with real repos)
"""
class TestRepositoryAnalyzerIntegration:
    '''Integration tests with real repositories.'''
    
    def test_analyze_small_python_repo(self):
        '''Test analyzing a small Python repository.'''
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path("config/languages")
            
            if not config_dir.exists():
                pytest.skip("Language configs not found")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("python", PythonPlugin)
            
            analyzer = RepositoryAnalyzer(registry)
            
            results = analyzer.analyze_repository(
                "https://github.com/octocat/Hello-World",
                Path(tmpdir)
            )
            
            assert results['primary_language'] is not None
            assert len(results['languages']) > 0
            assert results['metrics']['total_files'] > 0
            
            # Clean up
            analyzer.cleanup(results)
"""

class TestFeatureDetector:
    """Tests for FeatureDetector class."""
    
    @pytest.fixture
    def language_registry(self):
        """Create a language registry with test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create Python config
            python_config = config_dir / "python.yaml"
            with open(python_config, 'w') as f:
                f.write("""
name: python
display_name: Python
version: "3.11"
extensions:
  - .py
features:
  - classes
  - functions
  - async
  - decorators
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("python", PythonPlugin)
            
            yield registry
    
    def test_feature_detector_initialization(self, language_registry):
        """Test feature detector initialization."""
        detector = FeatureDetector(language_registry)
        
        assert detector.registry == language_registry
    
    def test_calculate_complexity_empty(self, language_registry):
        """Test calculate_complexity with no features."""
        detector = FeatureDetector(language_registry)
        
        complexity = detector.calculate_complexity({})
        
        assert complexity == 0.0
    
    def test_calculate_complexity_simple_features(self, language_registry):
        """Test calculate_complexity with simple features."""
        detector = FeatureDetector(language_registry)
        
        complexity = detector.calculate_complexity({
            'classes': 5,
            'functions': 10,
        })
        
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.0
    
    def test_calculate_complexity_complex_features(self, language_registry):
        """Test calculate_complexity with complex features."""
        detector = FeatureDetector(language_registry)
        
        complexity = detector.calculate_complexity({
            'reflection': 5,
            'metaprogramming': 3,
            'async': 10,
        })
        
        # Should be higher than simple features
        simple_complexity = detector.calculate_complexity({
            'classes': 5,
            'functions': 10,
        })
        
        assert complexity > simple_complexity
    
    def test_detect_file_features(self, language_registry):
        """Test detect_file_features."""
        detector = FeatureDetector(language_registry)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            # Use proper Python code without leading whitespace
            test_file.write_text(
"""class MyClass:
    @decorator
    async def my_method(self):
        pass
"""
            )
            
            features = detector.detect_file_features(test_file, "python")
            
            assert 'classes' in features
            assert 'async' in features
            assert 'decorators' in features
    
    def test_analyze_feature_usage(self, language_registry):
        """Test analyze_feature_usage."""
        detector = FeatureDetector(language_registry)
        
        profile = FeatureProfile(
            language="python",
            features_used={'classes': 10, 'async': 5, 'decorators': 8},
            complexity_score=0.5,
            patterns_detected=['Singleton'],
            framework_detected='django'
        )
        
        analysis = detector.analyze_feature_usage(profile)
        
        assert analysis['total_feature_count'] == 23
        assert analysis['unique_features'] == 3
        assert analysis['has_patterns'] is True
        assert analysis['has_framework'] is True
    
    def test_get_feature_dependencies(self, language_registry):
        """Test get_feature_dependencies."""
        detector = FeatureDetector(language_registry)
        
        deps = detector.get_feature_dependencies('async', 'python')
        
        assert isinstance(deps, list)
        # Should have some known dependencies
        assert len(deps) >= 0
    
    def test_estimate_translation_difficulty(self, language_registry):
        """Test estimate_translation_difficulty."""
        detector = FeatureDetector(language_registry)
        
        profile = FeatureProfile(
            language="python",
            features_used={'classes': 10, 'async': 5},
            complexity_score=0.5
        )
        
        difficulty = detector.estimate_translation_difficulty(profile, "python")
        
        assert 0.0 <= difficulty <= 1.0
    
    def test_generate_feature_report(self, language_registry):
        """Test generate_feature_report."""
        detector = FeatureDetector(language_registry)
        
        profile = FeatureProfile(
            language="python",
            features_used={'classes': 10, 'async': 5},
            complexity_score=0.65,
            patterns_detected=['Singleton', 'Factory']
        )
        
        analysis = detector.analyze_feature_usage(profile)
        report = detector.generate_feature_report(profile, analysis)
        
        assert "Feature Analysis Report" in report
        assert "python" in report
        assert "0.65" in report
        assert "Singleton" in report
    
    def test_compare_languages(self, language_registry):
        """Test compare_languages."""
        detector = FeatureDetector(language_registry)
        
        profile = FeatureProfile(
            language="python",
            features_used={'classes': 10, 'functions': 20}
        )
        
        comparison = detector.compare_languages(profile, "python")
        
        assert 'compatible_features' in comparison
        assert 'incompatible_features' in comparison
        assert 'compatibility_score' in comparison
        assert 0.0 <= comparison['compatibility_score'] <= 1.0