"""
Tests for advanced language features (Module 4 completion).

Tests:
- AST Analyzer
- Symbol Table
- Dependency Graph
- Equivalence Matrix
- Language Mapper
"""

import pytest
from pathlib import Path

from transmute.languages.ast_analyzer import (
    ASTNode,
    ASTAnalyzer,
    PythonASTAnalyzer,
    analyze_code_structure
)
from transmute.languages.symbol_table import (
    SymbolTable,
    Symbol,
    Scope,
    SymbolKind,
    ScopeType
)
from transmute.languages.dependency_graph import (
    DependencyGraph,
    DependencyEdge,
    DependencyType
)
from transmute.languages.equivalence_matrix import (
    EquivalenceMatrix,
    FeatureMapping,
    TranslationDifficulty
)
from transmute.languages.language_mapper import LanguageMapper


class TestASTNode:
    """Tests for ASTNode."""
    
    def test_ast_node_creation(self):
        """Test creating AST node."""
        node = ASTNode("function", value="test_func")
        
        assert node.node_type == "function"
        assert node.value == "test_func"
        assert node.children == []
        assert node.parent is None
    
    def test_add_child(self):
        """Test adding child nodes."""
        parent = ASTNode("class", value="MyClass")
        child = ASTNode("function", value="method")
        
        parent.add_child(child)
        
        assert len(parent.children) == 1
        assert child.parent == parent
    
    def test_get_descendants(self):
        """Test getting all descendants."""
        root = ASTNode("module")
        class_node = ASTNode("class", value="MyClass")
        method1 = ASTNode("function", value="method1")
        method2 = ASTNode("function", value="method2")
        
        root.add_child(class_node)
        class_node.add_child(method1)
        class_node.add_child(method2)
        
        descendants = root.get_descendants()
        
        assert len(descendants) == 3
        assert class_node in descendants
        assert method1 in descendants
    
    def test_find_nodes_by_type(self):
        """Test finding nodes by type."""
        root = ASTNode("module")
        func1 = ASTNode("function", value="func1")
        func2 = ASTNode("function", value="func2")
        class_node = ASTNode("class", value="MyClass")
        
        root.add_child(func1)
        root.add_child(func2)
        root.add_child(class_node)
        
        functions = root.find_nodes_by_type("function")
        
        assert len(functions) == 2
        assert all(f.node_type == "function" for f in functions)


class TestPythonASTAnalyzer:
    """Tests for PythonASTAnalyzer."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = PythonASTAnalyzer()
        
        assert analyzer.language == "python"
    
    def test_parse_simple_function(self):
        """Test parsing simple function."""
        analyzer = PythonASTAnalyzer()
        
        code = """
def hello():
    print("Hello")
"""
        
        root = analyzer.parse(code)
        
        assert root is not None
        functions = root.find_nodes_by_type("function")
        assert len(functions) >= 1
    
    def test_parse_class(self):
        """Test parsing class."""
        analyzer = PythonASTAnalyzer()
        
        code = """
class MyClass:
    def __init__(self):
        self.value = 0
    
    def method(self):
        pass
"""
        
        root = analyzer.parse(code)
        classes = root.find_nodes_by_type("class")
        
        assert len(classes) >= 1
    
    def test_extract_structure(self):
        """Test extracting structure."""
        analyzer = PythonASTAnalyzer()
        
        code = """
import os

class MyClass:
    pass

def my_function():
    pass
"""
        
        root = analyzer.parse(code)
        structure = analyzer.extract_structure(root)
        
        assert 'functions' in structure
        assert 'classes' in structure
        assert 'imports' in structure
    
    def test_get_complexity_metrics(self):
        """Test calculating complexity metrics."""
        analyzer = PythonASTAnalyzer()
        
        code = """
def complex_function():
    for i in range(10):
        if i > 5:
            print(i)
"""
        
        root = analyzer.parse(code)
        metrics = analyzer.get_complexity_metrics(root)
        
        assert 'node_count' in metrics
        assert 'function_count' in metrics
        assert 'loop_count' in metrics
        assert metrics['loop_count'] >= 1
    
    def test_analyze_code_structure(self):
        """Test analyze_code_structure helper."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        
        result = analyze_code_structure(code, "python")
        
        assert 'functions' in result
        assert 'classes' in result
        assert 'metrics' in result


class TestSymbolTable:
    """Tests for SymbolTable."""
    
    def test_symbol_table_initialization(self):
        """Test symbol table initialization."""
        table = SymbolTable()
        
        assert "global" in table.scopes
        assert table.current_scope_id == "global"
    
    def test_add_symbol(self):
        """Test adding symbols."""
        table = SymbolTable()
        
        symbol = table.add_symbol("my_var", SymbolKind.VARIABLE, line=10)
        
        assert symbol.name == "my_var"
        assert symbol.kind == SymbolKind.VARIABLE
        assert symbol.line == 10
    
    def test_lookup_symbol(self):
        """Test looking up symbols."""
        table = SymbolTable()
        
        table.add_symbol("test", SymbolKind.VARIABLE, line=5)
        
        symbol = table.lookup_symbol("test")
        
        assert symbol is not None
        assert symbol.name == "test"
    
    def test_lookup_nonexistent_symbol(self):
        """Test looking up nonexistent symbol."""
        table = SymbolTable()
        
        symbol = table.lookup_symbol("nonexistent")
        
        assert symbol is None
    
    def test_enter_exit_scope(self):
        """Test entering and exiting scopes."""
        table = SymbolTable()
        
        # Enter function scope
        func_scope = table.enter_scope(ScopeType.FUNCTION, "my_function")
        
        assert table.current_scope_id == func_scope
        assert func_scope in table.scopes
        
        # Exit scope
        parent = table.exit_scope()
        
        assert parent == "global"
        assert table.current_scope_id == "global"
    
    def test_scope_hierarchy(self):
        """Test scope hierarchy lookup."""
        table = SymbolTable()
        
        # Add global variable
        table.add_symbol("global_var", SymbolKind.VARIABLE, line=1)
        
        # Enter function scope
        table.enter_scope(ScopeType.FUNCTION, "func")
        
        # Should still find global variable
        symbol = table.lookup_symbol("global_var")
        
        assert symbol is not None
        assert symbol.scope_id == "global"
    
    def test_add_reference(self):
        """Test adding references to symbols."""
        table = SymbolTable()
        
        table.add_symbol("my_var", SymbolKind.VARIABLE, line=5)
        
        success = table.add_reference("my_var", line=10)
        
        assert success is True
        
        symbol = table.lookup_symbol("my_var")
        assert len(symbol.references) == 1
    
    def test_get_unused_symbols(self):
        """Test getting unused symbols."""
        table = SymbolTable()
        
        table.add_symbol("used", SymbolKind.VARIABLE, line=5)
        table.add_symbol("unused", SymbolKind.VARIABLE, line=10)
        
        table.add_reference("used", line=15)
        
        unused = table.get_unused_symbols()
        
        assert len(unused) == 1
        assert unused[0].name == "unused"
    
    def test_get_symbols_by_kind(self):
        """Test filtering symbols by kind."""
        table = SymbolTable()
        
        table.add_symbol("func1", SymbolKind.FUNCTION, line=1)
        table.add_symbol("func2", SymbolKind.FUNCTION, line=5)
        table.add_symbol("var1", SymbolKind.VARIABLE, line=10)
        
        functions = table.get_symbols_by_kind(SymbolKind.FUNCTION)
        
        assert len(functions) == 2
        assert all(s.kind == SymbolKind.FUNCTION for s in functions)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        table = SymbolTable()
        
        table.add_symbol("func1", SymbolKind.FUNCTION, line=1)
        table.add_symbol("var1", SymbolKind.VARIABLE, line=5)
        
        stats = table.get_statistics()
        
        assert stats['total_symbols'] == 2
        assert stats['functions'] == 1
        assert stats['variables'] == 1


class TestDependencyGraph:
    """Tests for DependencyGraph."""
    
    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = DependencyGraph()
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_node(self):
        """Test adding nodes."""
        graph = DependencyGraph()
        
        graph.add_node("module_a")
        
        assert "module_a" in graph.nodes
    
    def test_add_dependency(self):
        """Test adding dependencies."""
        graph = DependencyGraph()
        
        graph.add_dependency("module_a", "module_b", DependencyType.IMPORT)
        
        assert "module_a" in graph.nodes
        assert "module_b" in graph.nodes
        assert len(graph.edges) == 1
    
    def test_get_dependencies(self):
        """Test getting dependencies."""
        graph = DependencyGraph()
        
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("a", "c", DependencyType.IMPORT)
        
        deps = graph.get_dependencies("a")
        
        assert len(deps) == 2
        assert "b" in deps
        assert "c" in deps
    
    def test_get_dependents(self):
        """Test getting dependents."""
        graph = DependencyGraph()
        
        graph.add_dependency("a", "c", DependencyType.IMPORT)
        graph.add_dependency("b", "c", DependencyType.IMPORT)
        
        dependents = graph.get_dependents("c")
        
        assert len(dependents) == 2
        assert "a" in dependents
        assert "b" in dependents
    
    def test_find_circular_dependencies(self):
        """Test finding circular dependencies."""
        graph = DependencyGraph()
        
        # Create a cycle: a -> b -> c -> a
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("b", "c", DependencyType.IMPORT)
        graph.add_dependency("c", "a", DependencyType.IMPORT)
        
        cycles = graph.find_circular_dependencies()
        
        assert len(cycles) > 0
    
    def test_topological_sort(self):
        """Test topological sorting."""
        graph = DependencyGraph()
        
        # Linear dependency: a -> b -> c
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("b", "c", DependencyType.IMPORT)
        
        order = graph.topological_sort()
        
        assert order is not None
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")
    
    def test_topological_sort_with_cycle(self):
        """Test topological sort with cycles."""
        graph = DependencyGraph()
        
        # Create cycle
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("b", "a", DependencyType.IMPORT)
        
        order = graph.topological_sort()
        
        assert order is None  # Cannot sort with cycles
    
    def test_get_impact_analysis(self):
        """Test impact analysis."""
        graph = DependencyGraph()
        
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("b", "c", DependencyType.IMPORT)
        
        # Impact analysis: "If I change node X, what else is affected?"
        # Graph: a -> b -> c
        # If we change "c", then "b" and "a" are affected (they depend on c)
        impact = graph.get_impact_analysis("c")
        
        assert impact['node'] == "c"
        assert impact['total_affected'] >= 1  # At least "b" is affected
    
    def test_calculate_metrics(self):
        """Test calculating graph metrics."""
        graph = DependencyGraph()
        
        graph.add_dependency("a", "b", DependencyType.IMPORT)
        graph.add_dependency("b", "c", DependencyType.IMPORT)
        
        metrics = graph.calculate_metrics()
        
        assert metrics['node_count'] == 3
        assert metrics['edge_count'] == 2


class TestEquivalenceMatrix:
    """Tests for EquivalenceMatrix."""
    
    def test_matrix_initialization(self):
        """Test matrix initialization."""
        matrix = EquivalenceMatrix()
        
        assert len(matrix.mappings) > 0  # Has default mappings
    
    def test_get_mapping(self):
        """Test getting feature mapping."""
        matrix = EquivalenceMatrix()
        
        mapping = matrix.get_mapping("python", "java", "classes")
        
        assert mapping is not None
        assert mapping.source_feature == "classes"
    
    def test_get_nonexistent_mapping(self):
        """Test getting nonexistent mapping."""
        matrix = EquivalenceMatrix()
        
        mapping = matrix.get_mapping("python", "java", "nonexistent_feature")
        
        assert mapping is None
    
    def test_add_custom_mapping(self):
        """Test adding custom mapping."""
        matrix = EquivalenceMatrix()
        
        custom = FeatureMapping(
            source_feature="my_feature",
            target_feature="target_feature",
            difficulty=TranslationDifficulty.EASY
        )
        
        matrix.add_mapping("lang_a", "lang_b", custom)
        
        mapping = matrix.get_mapping("lang_a", "lang_b", "my_feature")
        
        assert mapping is not None
        assert mapping.target_feature == "target_feature"
    
    def test_calculate_translation_difficulty(self):
        """Test calculating translation difficulty."""
        matrix = EquivalenceMatrix()
        
        features = ["classes", "functions"]
        
        analysis = matrix.calculate_translation_difficulty(
            "python", "java", features
        )
        
        assert 'average_difficulty' in analysis
        assert 'features' in analysis
        assert 'is_feasible' in analysis
    
    def test_get_supported_language_pairs(self):
        """Test getting supported language pairs."""
        matrix = EquivalenceMatrix()
        
        pairs = matrix.get_supported_language_pairs()
        
        assert len(pairs) > 0
        assert ("python", "java") in pairs


class TestLanguageMapper:
    """Tests for LanguageMapper."""
    
    def test_mapper_initialization(self):
        """Test mapper initialization."""
        mapper = LanguageMapper()
        
        assert mapper.equivalence_matrix is not None
        assert 'python' in mapper.ast_analyzers
    
    def test_analyze_code(self):
        """Test analyzing code."""
        mapper = LanguageMapper()
        
        code = """
class MyClass:
    def method(self):
        pass
"""
        
        analysis = mapper.analyze_code(code, "python")
        
        assert analysis['language'] == "python"
        assert 'structure' in analysis
        assert 'metrics' in analysis
    
    def test_get_translation_strategy(self):
        """Test getting translation strategy."""
        mapper = LanguageMapper()
        
        features = ["classes", "functions"]
        
        strategy = mapper.get_translation_strategy(
            "python", "java", features
        )
        
        assert 'approach' in strategy
        assert 'difficulty_score' in strategy
        assert 'is_feasible' in strategy
    
    def test_map_feature(self):
        """Test mapping specific feature."""
        mapper = LanguageMapper()
        
        mapping = mapper.map_feature("python", "java", "classes")
        
        assert mapping is not None
        assert 'source_feature' in mapping
        assert 'target_feature' in mapping
        assert 'difficulty' in mapping
    
    def test_calculate_compatibility_score(self):
        """Test calculating compatibility score."""
        mapper = LanguageMapper()
        
        score = mapper.calculate_compatibility_score(
            "python", "java", ["classes", "functions"]
        )
        
        assert 0.0 <= score <= 1.0
    
    def test_generate_migration_report(self):
        """Test generating migration report."""
        mapper = LanguageMapper()
        
        code = """
class MyClass:
    def method(self):
        pass
"""
        
        analysis = mapper.analyze_code(code, "python")
        report = mapper.generate_migration_report("python", "java", analysis)
        
        assert "MIGRATION REPORT" in report
        assert "python" in report.lower()
        assert "java" in report.lower()
    
    def test_get_all_mappings(self):
        """Test getting all mappings."""
        mapper = LanguageMapper()
        
        mappings = mapper.get_all_mappings("python", "java")
        
        assert len(mappings) > 0
        assert all('source_feature' in m for m in mappings)
    
    def test_add_custom_mapping(self):
        """Test adding custom mapping."""
        mapper = LanguageMapper()
        
        custom = FeatureMapping(
            source_feature="custom",
            target_feature="custom_target",
            difficulty=TranslationDifficulty.EASY
        )
        
        mapper.add_custom_mapping("lang_a", "lang_b", custom)
        
        mapping = mapper.map_feature("lang_a", "lang_b", "custom")
        
        assert mapping is not None