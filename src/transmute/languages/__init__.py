"""Language system for Transmute."""

from transmute.languages.base import LanguageConfig, LanguagePlugin
from transmute.languages.registry import LanguageRegistry

# Advanced features
from transmute.languages.ast_analyzer import (
    ASTAnalyzer,
    ASTNode,
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

__all__ = [
    # Core
    "LanguageConfig",
    "LanguagePlugin",
    "LanguageRegistry",
    
    # AST Analysis
    "ASTAnalyzer",
    "ASTNode",
    "PythonASTAnalyzer",
    "analyze_code_structure",
    
    # Symbol Table
    "SymbolTable",
    "Symbol",
    "Scope",
    "SymbolKind",
    "ScopeType",
    
    # Dependency Graph
    "DependencyGraph",
    "DependencyEdge",
    "DependencyType",
    
    # Cross-Language Mapping
    "EquivalenceMatrix",
    "FeatureMapping",
    "TranslationDifficulty",
    "LanguageMapper",
]