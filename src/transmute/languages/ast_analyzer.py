"""
Advanced AST analysis utilities.

Provides deep AST traversal, pattern matching, and structural analysis.
"""

from typing import Dict, Any, List, Optional, Set, Callable
from pathlib import Path
import ast
from abc import ABC, abstractmethod

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class ASTNode:
    """
    Represents a node in the AST with additional metadata.
    
    Wraps language-specific AST nodes with common interface.
    """
    
    def __init__(
        self,
        node_type: str,
        value: Any = None,
        children: Optional[List['ASTNode']] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_location: Optional[Dict[str, int]] = None
    ):
        """
        Initialize AST node.
        
        Args:
            node_type: Type of node (e.g., "function", "class", "variable")
            value: Node value (e.g., function name)
            children: Child nodes
            metadata: Additional metadata
            source_location: Line/column information
        """
        self.node_type = node_type
        self.value = value
        self.children = children or []
        self.metadata = metadata or {}
        self.source_location = source_location or {}
        self.parent: Optional['ASTNode'] = None
    
    def add_child(self, child: 'ASTNode') -> None:
        """Add child node."""
        child.parent = self
        self.children.append(child)
    
    def get_descendants(self) -> List['ASTNode']:
        """Get all descendant nodes (depth-first)."""
        descendants = []
        
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        
        return descendants
    
    def find_nodes_by_type(self, node_type: str) -> List['ASTNode']:
        """Find all nodes of specific type in subtree."""
        nodes = []
        
        if self.node_type == node_type:
            nodes.append(self)
        
        for child in self.children:
            nodes.extend(child.find_nodes_by_type(node_type))
        
        return nodes
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ASTNode({self.node_type}, value={self.value})"


class ASTAnalyzer(ABC):
    """
    Abstract base class for AST analyzers.
    
    Provides common utilities for AST analysis.
    """
    
    def __init__(self, language: str):
        """
        Initialize AST analyzer.
        
        Args:
            language: Programming language
        """
        self.language = language
        self.cache: Dict[str, Any] = {}
    
    @abstractmethod
    def parse(self, code: str) -> ASTNode:
        """
        Parse code into AST.
        
        Args:
            code: Source code
            
        Returns:
            Root AST node
        """
        pass
    
    def traverse(
        self,
        node: ASTNode,
        visitor: Callable[[ASTNode], None]
    ) -> None:
        """
        Traverse AST with visitor pattern.
        
        Args:
            node: Root node
            visitor: Visitor function called on each node
            
        Example:
            >>> def print_node(node):
            ...     print(node.node_type)
            >>> analyzer.traverse(root, print_node)
        """
        visitor(node)
        
        for child in node.children:
            self.traverse(child, visitor)
    
    def find_pattern(
        self,
        node: ASTNode,
        pattern: Dict[str, Any]
    ) -> List[ASTNode]:
        """
        Find nodes matching pattern.
        
        Args:
            node: Root node
            pattern: Pattern to match (e.g., {"node_type": "function", "value": "main"})
            
        Returns:
            List of matching nodes
            
        Example:
            >>> matches = analyzer.find_pattern(root, {"node_type": "class"})
        """
        matches = []
        
        def check_match(n: ASTNode):
            if all(getattr(n, key, None) == value for key, value in pattern.items()):
                matches.append(n)
        
        self.traverse(node, check_match)
        
        return matches
    
    def get_complexity_metrics(self, node: ASTNode) -> Dict[str, int]:
        """
        Calculate complexity metrics for AST.
        
        Args:
            node: Root node
            
        Returns:
            Dictionary of metrics (depth, node_count, etc.)
            
        Example:
            >>> metrics = analyzer.get_complexity_metrics(root)
            >>> print(f"Depth: {metrics['max_depth']}")
        """
        metrics = {
            'node_count': 0,
            'max_depth': 0,
            'function_count': 0,
            'class_count': 0,
            'loop_count': 0,
            'conditional_count': 0
        }
        
        def count_nodes(n: ASTNode, depth: int = 0):
            metrics['node_count'] += 1
            metrics['max_depth'] = max(metrics['max_depth'], depth)
            
            if n.node_type == 'function':
                metrics['function_count'] += 1
            elif n.node_type == 'class':
                metrics['class_count'] += 1
            elif n.node_type in ['for_loop', 'while_loop']:
                metrics['loop_count'] += 1
            elif n.node_type in ['if_statement', 'switch']:
                metrics['conditional_count'] += 1
            
            for child in n.children:
                count_nodes(child, depth + 1)
        
        count_nodes(node)
        
        return metrics
    
    def extract_structure(self, node: ASTNode) -> Dict[str, Any]:
        """
        Extract high-level structure from AST.
        
        Args:
            node: Root node
            
        Returns:
            Structure dictionary
            
        Example:
            >>> structure = analyzer.extract_structure(root)
            >>> print(structure['classes'])
        """
        structure = {
            'functions': [],
            'classes': [],
            'variables': [],
            'imports': []
        }
        
        # Find all top-level elements
        for child in node.children:
            if child.node_type == 'function':
                structure['functions'].append({
                    'name': child.value,
                    'params': child.metadata.get('params', []),
                    'line': child.source_location.get('line')
                })
            elif child.node_type == 'class':
                structure['classes'].append({
                    'name': child.value,
                    'methods': [c.value for c in child.find_nodes_by_type('function')],
                    'line': child.source_location.get('line')
                })
            elif child.node_type == 'variable':
                structure['variables'].append({
                    'name': child.value,
                    'line': child.source_location.get('line')
                })
            elif child.node_type == 'import':
                structure['imports'].append({
                    'module': child.value,
                    'line': child.source_location.get('line')
                })
        
        return structure


class PythonASTAnalyzer(ASTAnalyzer):
    """
    AST analyzer for Python using built-in ast module.
    """
    
    def __init__(self):
        """Initialize Python AST analyzer."""
        super().__init__("python")
    
    def parse(self, code: str) -> ASTNode:
        """
        Parse Python code into AST.
        
        Args:
            code: Python source code
            
        Returns:
            Root AST node
        """
        try:
            tree = ast.parse(code)
            return self._convert_python_ast(tree)
        except SyntaxError as e:
            logger.error(f"Python syntax error: {e}")
            raise
    
    def _convert_python_ast(self, node: ast.AST) -> ASTNode:
        """Convert Python AST to generic ASTNode."""
        # Determine node type
        node_type = self._get_node_type(node)
        value = self._get_node_value(node)
        
        # Create ASTNode
        ast_node = ASTNode(
            node_type=node_type,
            value=value,
            source_location={
                'line': getattr(node, 'lineno', 0),
                'col': getattr(node, 'col_offset', 0)
            }
        )
        
        # Add metadata
        if isinstance(node, ast.FunctionDef):
            ast_node.metadata['params'] = [arg.arg for arg in node.args.args]
            ast_node.metadata['is_async'] = isinstance(node, ast.AsyncFunctionDef)
        elif isinstance(node, ast.ClassDef):
            ast_node.metadata['bases'] = [self._get_name(base) for base in node.bases]
        
        # Convert children
        for child in ast.iter_child_nodes(node):
            child_node = self._convert_python_ast(child)
            ast_node.add_child(child_node)
        
        return ast_node
    
    def _get_node_type(self, node: ast.AST) -> str:
        """Get node type string."""
        if isinstance(node, ast.FunctionDef):
            return 'function'
        elif isinstance(node, ast.AsyncFunctionDef):
            return 'async_function'
        elif isinstance(node, ast.ClassDef):
            return 'class'
        elif isinstance(node, ast.Import):
            return 'import'
        elif isinstance(node, ast.ImportFrom):
            return 'import_from'
        elif isinstance(node, ast.Assign):
            return 'assignment'
        elif isinstance(node, ast.For):
            return 'for_loop'
        elif isinstance(node, ast.While):
            return 'while_loop'
        elif isinstance(node, ast.If):
            return 'if_statement'
        elif isinstance(node, ast.Return):
            return 'return'
        elif isinstance(node, ast.Call):
            return 'function_call'
        else:
            return node.__class__.__name__.lower()
    
    def _get_node_value(self, node: ast.AST) -> Any:
        """Get node value."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return node.name
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                return [alias.name for alias in node.names]
            else:
                return node.module
        else:
            return None
    
    def _get_name(self, node: ast.AST) -> Optional[str]:
        """Get name from node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return None


def analyze_code_structure(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyze code structure using AST.
    
    Args:
        code: Source code
        language: Programming language
        
    Returns:
        Structure analysis
        
    Example:
        >>> structure = analyze_code_structure(python_code)
        >>> print(f"Functions: {len(structure['functions'])}")
    """
    if language == "python":
        analyzer = PythonASTAnalyzer()
    else:
        raise ValueError(f"Unsupported language: {language}")
    
    try:
        root = analyzer.parse(code)
        structure = analyzer.extract_structure(root)
        metrics = analyzer.get_complexity_metrics(root)
        
        return {
            **structure,
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Failed to analyze structure: {e}")
        return {
            'functions': [],
            'classes': [],
            'variables': [],
            'imports': [],
            'metrics': {}
        }