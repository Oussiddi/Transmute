"""
Tests for new language plugins (JavaScript, TypeScript, C#, PHP).
"""

import pytest
from pathlib import Path
import tempfile

from transmute.languages.plugins import (
    JavaScriptPlugin,
    TypeScriptPlugin,
    CSharpPlugin,
    PHPPlugin,
)
from transmute.languages.registry import LanguageRegistry


class TestJavaScriptPlugin:
    """Tests for JavaScript plugin."""
    
    @pytest.fixture
    def js_plugin(self):
        """Create JavaScript plugin with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Create config
            config_file = config_dir / "javascript.yaml"
            config_file.write_text("""
name: javascript
display_name: JavaScript
version: "ES2023"
extensions:
  - .js
  - .jsx
features:
  - classes
  - arrow_functions
  - async
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("javascript", JavaScriptPlugin)
            
            yield registry.get_plugin("javascript")
    
    def test_js_plugin_initialization(self, js_plugin):
        """Test JavaScript plugin initialization."""
        assert js_plugin.config.name == "javascript"
        assert ".js" in js_plugin.config.extensions
    
    def test_js_detect_arrow_functions(self, js_plugin):
        """Test detecting arrow functions."""
        code = "const add = (a, b) => a + b;"
        
        features = js_plugin.detect_features(code)
        
        assert "arrow_functions" in features
    
    def test_js_detect_async(self, js_plugin):
        """Test detecting async/await."""
        code = """
async function fetchData() {
    const data = await fetch('/api');
    return data;
}
"""
        
        features = js_plugin.detect_features(code)
        
        assert "async" in features
        assert "await" in features
    
    def test_js_detect_classes(self, js_plugin):
        """Test detecting classes."""
        code = """
class Person {
    constructor(name) {
        this.name = name;
    }
    
    greet() {
        return `Hello, ${this.name}`;
    }
}
"""
        
        features = js_plugin.detect_features(code)
        
        assert "classes" in features
    
    def test_js_detect_template_literals(self, js_plugin):
        """Test detecting template literals."""
        code = "const msg = `Hello ${name}`;"
        
        features = js_plugin.detect_features(code)
        
        assert "template_literals" in features
    
    def test_js_parse_file(self, js_plugin):
        """Test parsing a JavaScript file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.js"
            test_file.write_text("""
class MyClass {
    async method() {
        return await fetch('/api');
    }
}

const add = (a, b) => a + b;
""")
            
            result = js_plugin.parse_file(test_file)
            
            assert "classes" in result
            assert "functions" in result
            assert "features_used" in result
            assert len(result["classes"]) > 0


class TestTypeScriptPlugin:
    """Tests for TypeScript plugin."""
    
    @pytest.fixture
    def ts_plugin(self):
        """Create TypeScript plugin with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            config_file = config_dir / "typescript.yaml"
            config_file.write_text("""
name: typescript
display_name: TypeScript
version: "5.3"
extensions:
  - .ts
  - .tsx
features:
  - classes
  - interfaces
  - generics
  - type_annotations
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("typescript", TypeScriptPlugin)
            
            yield registry.get_plugin("typescript")
    
    def test_ts_plugin_initialization(self, ts_plugin):
        """Test TypeScript plugin initialization."""
        assert ts_plugin.config.name == "typescript"
        assert ".ts" in ts_plugin.config.extensions
    
    def test_ts_detect_interfaces(self, ts_plugin):
        """Test detecting interfaces."""
        code = """
interface User {
    name: string;
    age: number;
}
"""
        
        features = ts_plugin.detect_features(code)
        
        assert "interfaces" in features
    
    def test_ts_detect_type_annotations(self, ts_plugin):
        """Test detecting type annotations."""
        code = "function add(a: number, b: number): number { return a + b; }"
        
        features = ts_plugin.detect_features(code)
        
        assert "type_annotations" in features
    
    def test_ts_detect_generics(self, ts_plugin):
        """Test detecting generics."""
        code = "function identity<T>(arg: T): T { return arg; }"
        
        features = ts_plugin.detect_features(code)
        
        assert "generics" in features
    
    def test_ts_detect_enums(self, ts_plugin):
        """Test detecting enums."""
        code = "enum Color { Red, Green, Blue }"
        
        features = ts_plugin.detect_features(code)
        
        assert "enums" in features


class TestCSharpPlugin:
    """Tests for C# plugin."""
    
    @pytest.fixture
    def cs_plugin(self):
        """Create C# plugin with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            config_file = config_dir / "csharp.yaml"
            config_file.write_text("""
name: csharp
display_name: "C#"
version: "12.0"
extensions:
  - .cs
features:
  - classes
  - interfaces
  - properties
  - async
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("csharp", CSharpPlugin)
            
            yield registry.get_plugin("csharp")
    
    def test_cs_plugin_initialization(self, cs_plugin):
        """Test C# plugin initialization."""
        assert cs_plugin.config.name == "csharp"
        assert ".cs" in cs_plugin.config.extensions
    
    def test_cs_detect_classes(self, cs_plugin):
        """Test detecting classes."""
        code = "public class MyClass { }"
        
        features = cs_plugin.detect_features(code)
        
        assert "classes" in features
    
    def test_cs_detect_interfaces(self, cs_plugin):
        """Test detecting interfaces."""
        code = "public interface IMyInterface { }"
        
        features = cs_plugin.detect_features(code)
        
        assert "interfaces" in features
    
    def test_cs_detect_properties(self, cs_plugin):
        """Test detecting properties."""
        code = "public string Name { get; set; }"
        
        features = cs_plugin.detect_features(code)
        
        assert "properties" in features
    
    def test_cs_detect_async(self, cs_plugin):
        """Test detecting async/await."""
        code = """
public async Task<string> FetchDataAsync() {
    var data = await client.GetAsync("/api");
    return data;
}
"""
        
        features = cs_plugin.detect_features(code)
        
        assert "async" in features
        assert "await" in features
    
    def test_cs_detect_generics(self, cs_plugin):
        """Test detecting generics."""
        code = "public class List<T> { }"
        
        features = cs_plugin.detect_features(code)
        
        assert "generics" in features
    
    def test_cs_detect_linq(self, cs_plugin):
        """Test detecting LINQ."""
        code = "var query = from item in items where item.Active select item;"
        
        features = cs_plugin.detect_features(code)
        
        assert "linq" in features
    
    def test_cs_parse_file(self, cs_plugin):
        """Test parsing a C# file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.cs"
            test_file.write_text("""
public class Person {
    public string Name { get; set; }
    
    public async Task<string> GreetAsync() {
        await Task.Delay(100);
        return "Hello";
    }
}
""")
            
            result = cs_plugin.parse_file(test_file)
            
            assert "classes" in result
            assert "properties" in result
            assert "features_used" in result


class TestPHPPlugin:
    """Tests for PHP plugin."""
    
    @pytest.fixture
    def php_plugin(self):
        """Create PHP plugin with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            config_file = config_dir / "php.yaml"
            config_file.write_text("""
name: php
display_name: PHP
version: "8.3"
extensions:
  - .php
features:
  - classes
  - interfaces
  - traits
  - namespaces
""")
            
            registry = LanguageRegistry(config_dir=config_dir)
            registry.register_plugin("php", PHPPlugin)
            
            yield registry.get_plugin("php")
    
    def test_php_plugin_initialization(self, php_plugin):
        """Test PHP plugin initialization."""
        assert php_plugin.config.name == "php"
        assert ".php" in php_plugin.config.extensions
    
    def test_php_detect_classes(self, php_plugin):
        """Test detecting classes."""
        code = "<?php class MyClass { }"
        
        features = php_plugin.detect_features(code)
        
        assert "classes" in features
    
    def test_php_detect_traits(self, php_plugin):
        """Test detecting traits."""
        code = "<?php trait MyTrait { }"
        
        features = php_plugin.detect_features(code)
        
        assert "traits" in features
    
    def test_php_detect_namespaces(self, php_plugin):
        """Test detecting namespaces."""
        code = "<?php namespace App\\Models;"
        
        features = php_plugin.detect_features(code)
        
        assert "namespaces" in features
    
    def test_php_detect_arrow_functions(self, php_plugin):
        """Test detecting arrow functions."""
        code = "<?php $add = fn($a, $b) => $a + $b;"
        
        features = php_plugin.detect_features(code)
        
        assert "arrow_functions" in features
    
    def test_php_detect_enums(self, php_plugin):
        """Test detecting enums (PHP 8.1+)."""
        code = "<?php enum Status { case Active; case Inactive; }"
        
        features = php_plugin.detect_features(code)
        
        assert "enums" in features
    
    def test_php_detect_attributes(self, php_plugin):
        """Test detecting attributes (PHP 8+)."""
        code = "<?php #[Route('/api')] class ApiController { }"
        
        features = php_plugin.detect_features(code)
        
        assert "attributes" in features
    
    def test_php_parse_file(self, php_plugin):
        """Test parsing a PHP file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.php"
            test_file.write_text("""<?php
namespace App;

class User {
    public string $name;
    
    public function getName(): string {
        return $this->name;
    }
}
""")
            
            result = php_plugin.parse_file(test_file)
            
            assert "classes" in result
            assert "functions" in result
            assert "features_used" in result