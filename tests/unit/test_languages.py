"""
Tests for language system.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from transmute.languages.plugins import PythonPlugin, JavaPlugin
from transmute.languages.base import LanguagePlugin, LanguageConfig
from transmute.languages.registry import LanguageRegistry


# Mock plugin for testing
class MockLanguagePlugin(LanguagePlugin):
    """Mock language plugin for testing."""
    
    def parse_file(self, file_path: Path):
        return {"classes": [], "functions": []}
    
    def detect_features(self, code: str):
        return ["classes", "functions"]
    
    def format_code(self, code: str):
        return code.strip()


class TestLanguageConfig:
    """Tests for LanguageConfig model."""
    
    def test_language_config_minimal(self):
        """Test LanguageConfig with minimal fields."""
        config = LanguageConfig(
            name="testlang",
            display_name="Test Language",
            extensions=[".test"]
        )
        
        assert config.name == "testlang"
        assert config.display_name == "Test Language"
        assert ".test" in config.extensions
    
    def test_language_config_full(self):
        """Test LanguageConfig with all fields."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            version="3.11",
            extensions=[".py", ".pyw"],
            features=["classes", "async", "decorators"],
            keywords=["def", "class", "import"],
            frameworks=["django", "flask"],
            build_tools=["poetry", "pip"],
            package_managers=["pip", "poetry"]
        )
        
        assert config.version == "3.11"
        assert "async" in config.features
        assert "django" in config.frameworks


class TestLanguagePlugin:
    """Tests for LanguagePlugin base class."""
    
    def test_language_plugin_initialization(self):
        """Test plugin initialization."""
        config = LanguageConfig(
            name="test",
            display_name="Test",
            extensions=[".test"]
        )
        
        plugin = MockLanguagePlugin(config)
        
        assert plugin.name == "test"
        assert plugin.display_name == "Test"
        assert plugin.config == config
    
    def test_is_source_file(self):
        """Test is_source_file method."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py", ".pyw"]
        )
        
        plugin = MockLanguagePlugin(config)
        
        assert plugin.is_source_file(Path("test.py")) is True
        assert plugin.is_source_file(Path("test.pyw")) is True
        assert plugin.is_source_file(Path("test.java")) is False
    
    def test_get_features(self):
        """Test get_features method."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"],
            features=["classes", "async"]
        )
        
        plugin = MockLanguagePlugin(config)
        features = plugin.get_features()
        
        assert "classes" in features
        assert "async" in features
    
    def test_supports_feature(self):
        """Test supports_feature method."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"],
            features=["classes", "async"]
        )
        
        plugin = MockLanguagePlugin(config)
        
        assert plugin.supports_feature("classes") is True
        assert plugin.supports_feature("async") is True
        assert plugin.supports_feature("generics") is False


class TestLanguageRegistry:
    """Tests for LanguageRegistry."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = LanguageRegistry(config_dir=Path("config/languages"))
        
        assert registry.config_dir == Path("config/languages")
        assert len(registry.get_supported_languages()) == 0
    
    def test_load_language_config(self):
        """Test loading language config from YAML."""
        registry = LanguageRegistry(config_dir=Path("config/languages"))
        
        # Try to load Python config (should exist)
        if (Path("config/languages/python.yaml")).exists():
            config = registry.load_language_config("python")
            
            assert config.name == "python"
            assert config.display_name == "Python"
            assert ".py" in config.extensions
        else:
            pytest.skip("Python config file not found")
    
    def test_load_language_config_not_found(self):
        """Test loading non-existent config."""
        registry = LanguageRegistry(config_dir=Path("config/languages"))
        
        with pytest.raises(FileNotFoundError, match="Language config not found"):
            registry.load_language_config("nonexistent")
    
    def test_register_plugin(self):
        """Test registering a plugin."""
        # Create temp config
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Write test config
            config_path = config_dir / "testlang.yaml"
            with open(config_path, 'w') as f:
                yaml.dump({
                    'name': 'testlang',
                    'display_name': 'Test Language',
                    'extensions': ['.test']
                }, f)
            
            # Create registry and register plugin
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("testlang", MockLanguagePlugin)
            
            # Verify registration
            assert registry.is_supported("testlang")
            plugin = registry.get_plugin("testlang")
            assert plugin is not None
            assert plugin.name == "testlang"
    
    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            config_path = config_dir / "testlang.yaml"
            with open(config_path, 'w') as f:
                yaml.dump({
                    'name': 'testlang',
                    'display_name': 'Test',
                    'extensions': ['.test']
                }, f)
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("testlang", MockLanguagePlugin)
            
            # Try to register again
            with pytest.raises(ValueError, match="already registered"):
                registry.register_plugin("testlang", MockLanguagePlugin)
    
    def test_get_all_plugins(self):
        """Test getting all plugins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create two test configs
            for lang in ["lang1", "lang2"]:
                config_path = config_dir / f"{lang}.yaml"
                with open(config_path, 'w') as f:
                    yaml.dump({
                        'name': lang,
                        'display_name': lang.title(),
                        'extensions': [f'.{lang}']
                    }, f)
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("lang1", MockLanguagePlugin)
            registry.register_plugin("lang2", MockLanguagePlugin)
            
            plugins = registry.get_all_plugins()
            assert len(plugins) == 2
            assert "lang1" in plugins
            assert "lang2" in plugins
    
    def test_detect_language(self):
        """Test language detection from file extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            config_path = config_dir / "python.yaml"
            with open(config_path, 'w') as f:
                yaml.dump({
                    'name': 'python',
                    'display_name': 'Python',
                    'extensions': ['.py', '.pyw']
                }, f)
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("python", MockLanguagePlugin)
            
            # Test detection
            assert registry.detect_language(Path("test.py")) == "python"
            assert registry.detect_language(Path("test.pyw")) == "python"
            assert registry.detect_language(Path("test.java")) is None


class TestPythonPlugin:
    """Tests for PythonPlugin."""
    
    def test_python_plugin_initialization(self):
        """Test Python plugin initialization."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"]
        )
        
        plugin = PythonPlugin(config)
        assert plugin.name == "python"
    
    def test_detect_features_classes(self):
        """Test detecting classes in Python code."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"]
        )
        
        plugin = PythonPlugin(config)
        code = """
class MyClass:
    def __init__(self):
        pass
"""
        
        features = plugin.detect_features(code)
        assert 'classes' in features
        assert 'functions' in features
    
    def test_detect_features_async(self):
        """Test detecting async in Python code."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"]
        )
        
        plugin = PythonPlugin(config)
        code = """
async def fetch_data():
    pass
"""
        
        features = plugin.detect_features(code)
        assert 'async' in features
    
    def test_detect_features_decorators(self):
        """Test detecting decorators in Python code."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"]
        )
        
        plugin = PythonPlugin(config)
        code = """
@decorator
def my_function():
    pass
"""
        
        features = plugin.detect_features(code)
        assert 'decorators' in features
    
    def test_format_code(self):
        """Test code formatting."""
        config = LanguageConfig(
            name="python",
            display_name="Python",
            extensions=[".py"]
        )
        
        plugin = PythonPlugin(config)
        code = "def test():   \n    pass   \n\n\n\nprint('hello')   "
        
        formatted = plugin.format_code(code)
        
        # Should remove trailing whitespace
        assert not any(line.endswith(' ') for line in formatted.splitlines())


class TestJavaPlugin:
    """Tests for JavaPlugin."""
    
    def test_java_plugin_initialization(self):
        """Test Java plugin initialization."""
        config = LanguageConfig(
            name="java",
            display_name="Java",
            extensions=[".java"]
        )
        
        plugin = JavaPlugin(config)
        assert plugin.name == "java"
    
    def test_detect_features_classes(self):
        """Test detecting classes in Java code."""
        config = LanguageConfig(
            name="java",
            display_name="Java",
            extensions=[".java"]
        )
        
        plugin = JavaPlugin(config)
        code = """
public class MyClass {
    public void myMethod() {
    }
}
"""
        
        features = plugin.detect_features(code)
        assert 'classes' in features
    
    def test_detect_features_generics(self):
        """Test detecting generics in Java code."""
        config = LanguageConfig(
            name="java",
            display_name="Java",
            extensions=[".java"]
        )
        
        plugin = JavaPlugin(config)
        code = "List<String> items = new ArrayList<>();"
        
        features = plugin.detect_features(code)
        assert 'generics' in features
    
    def test_detect_features_lambdas(self):
        """Test detecting lambdas in Java code."""
        config = LanguageConfig(
            name="java",
            display_name="Java",
            extensions=[".java"]
        )
        
        plugin = JavaPlugin(config)
        code = "items.forEach(item -> System.out.println(item));"
        
        features = plugin.detect_features(code)
        assert 'lambdas' in features