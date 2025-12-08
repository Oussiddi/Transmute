"""
Python language plugin.

Handles Python-specific parsing, feature detection, and code formatting.
"""

from typing import List, Dict, Any
from pathlib import Path
import ast
import re

from transmute.languages.base import LanguagePlugin, LanguageConfig
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class PythonPlugin(LanguagePlugin):
    """
    Python language plugin.
    
    Provides Python-specific functionality for parsing, feature detection,
    and code generation.
    """
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Python file using AST.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with parsed structure
        """
        logger.debug(f"Parsing Python file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code, filename=str(file_path))
            
            result = {
                'classes': self._extract_classes(tree),
                'functions': self._extract_functions(tree),
                'imports': self._extract_imports(tree),
                'features_used': self.detect_features(code),
                'line_count': len(code.splitlines()),
            }
            
            logger.info(f"Parsed Python file: {len(result['classes'])} classes, "
                       f"{len(result['functions'])} functions")
            
            return result
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return {
                'error': str(e),
                'classes': [],
                'functions': [],
                'imports': [],
                'features_used': [],
                'line_count': 0,
            }
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect Python features used in code.
        
        Args:
            code: Python source code
            
        Returns:
            List of detected features
        """
        features = []
        
        try:
            tree = ast.parse(code)
            
            # Walk the AST and detect features
            for node in ast.walk(tree):
                # Classes
                if isinstance(node, ast.ClassDef) and 'classes' not in features:
                    features.append('classes')
                
                # Functions
                if isinstance(node, ast.FunctionDef) and 'functions' not in features:
                    features.append('functions')
                
                # Async functions
                if isinstance(node, ast.AsyncFunctionDef) and 'async' not in features:
                    features.append('async')
                
                # Decorators
                if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and 
                    node.decorator_list and 'decorators' not in features):
                    features.append('decorators')
                
                # Generators (yield)
                if isinstance(node, ast.Yield) and 'generators' not in features:
                    features.append('generators')
                
                # Comprehensions
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)) and \
                   'comprehensions' not in features:
                    features.append('comprehensions')
                
                # Context managers (with)
                if isinstance(node, ast.With) and 'context_managers' not in features:
                    features.append('context_managers')
                
                # Type hints
                if hasattr(node, 'annotation') and node.annotation and \
                   'type_hints' not in features:
                    features.append('type_hints')
                
                # Match statements (Python 3.10+)
                if hasattr(ast, 'Match') and isinstance(node, ast.Match) and \
                   'pattern_matching' not in features:
                    features.append('pattern_matching')
            
            # Check for lambda
            if 'lambda' in code and 'lambdas' not in features:
                features.append('lambdas')
            
            # Check for walrus operator :=
            if ':=' in code and 'walrus_operator' not in features:
                features.append('walrus_operator')
            
            # Check for dataclasses
            if '@dataclass' in code and 'dataclasses' not in features:
                features.append('dataclasses')
            
            logger.debug(f"Detected Python features: {features}")
            
        except SyntaxError:
            logger.warning("Could not parse code for feature detection")
        
        return features
    
    def format_code(self, code: str) -> str:
        """
        Format Python code (basic formatting).
        
        Args:
            code: Unformatted code
            
        Returns:
            Formatted code
        """
        # Basic formatting - remove trailing whitespace
        lines = code.splitlines()
        formatted_lines = [line.rstrip() for line in lines]
        
        # Remove multiple blank lines
        result = []
        prev_blank = False
        for line in formatted_lines:
            if line.strip() == '':
                if not prev_blank:
                    result.append(line)
                prev_blank = True
            else:
                result.append(line)
                prev_blank = False
        
        return '\n'.join(result)
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions from AST."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'bases': [self._get_name(base) for base in node.bases],
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    'decorators': [self._get_name(d) for d in node.decorator_list],
                    'line_number': node.lineno,
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods (they're inside classes)
                if not any(isinstance(parent, ast.ClassDef) 
                          for parent in ast.walk(tree) 
                          if hasattr(parent, 'body') and node in parent.body):
                    functions.append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                        'decorators': [self._get_name(d) for d in node.decorator_list],
                        'line_number': node.lineno,
                    })
        
        return functions
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return list(set(imports))  # Remove duplicates
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return str(node)