"""
JavaScript language plugin with full AST parsing.

Uses esprima for proper JavaScript AST analysis.
"""

from typing import Dict, Any, List
from pathlib import Path
import re

import esprima
from esprima import nodes

from transmute.languages.base import LanguagePlugin
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class JavaScriptPlugin(LanguagePlugin):
    """
    JavaScript language plugin with full AST parsing.
    
    Uses esprima for accurate JavaScript code analysis.
    """
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse JavaScript file using esprima.
        
        Args:
            file_path: Path to JavaScript file
            
        Returns:
            Dictionary with parsed information
        """
        logger.debug(f"Parsing JavaScript file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Parse with esprima
            try:
                ast = esprima.parseScript(code, {'tolerant': True, 'jsx': True})
            except Exception:
                # Try as module
                ast = esprima.parseModule(code, {'tolerant': True, 'jsx': True})
            
            # Extract information
            classes = self._extract_classes(ast)
            functions = self._extract_functions(ast)
            imports = self._extract_imports(ast)
            exports = self._extract_exports(ast)
            
            features_used = self.detect_features(code)
            line_count = len(code.splitlines())
            
            return {
                'classes': classes,
                'functions': functions,
                'imports': imports,
                'exports': exports,
                'features_used': features_used,
                'line_count': line_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {
                'classes': [],
                'functions': [],
                'imports': [],
                'exports': [],
                'features_used': [],
                'line_count': 0,
                'error': str(e)
            }
    
    def _extract_classes(self, ast) -> List[Dict[str, Any]]:
        """Extract class declarations."""
        classes = []
        
        def visit(node):
            if isinstance(node, nodes.ClassDeclaration):
                class_info = {
                    'name': node.id.name if node.id else '<anonymous>',
                    'methods': [],
                    'properties': [],
                    'extends': node.superClass.name if node.superClass and hasattr(node.superClass, 'name') else None,
                }
                
                # Extract methods and properties
                if hasattr(node, 'body') and hasattr(node.body, 'body'):
                    for item in node.body.body:
                        if isinstance(item, nodes.MethodDefinition):
                            class_info['methods'].append({
                                'name': item.key.name if hasattr(item.key, 'name') else str(item.key),
                                'static': item.static,
                                'kind': item.kind,  # method, constructor, get, set
                            })
                        elif isinstance(item, nodes.PropertyDefinition):
                            class_info['properties'].append({
                                'name': item.key.name if hasattr(item.key, 'name') else str(item.key),
                                'static': getattr(item, 'static', False),
                            })
                
                classes.append(class_info)
            
            # Recurse
            for key, value in node.__dict__.items():
                if isinstance(value, nodes.Node):
                    visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, nodes.Node):
                            visit(item)
        
        visit(ast)
        return classes
    
    def _extract_functions(self, ast) -> List[Dict[str, Any]]:
        """Extract function declarations."""
        functions = []
        
        def visit(node):
            if isinstance(node, (nodes.FunctionDeclaration, nodes.ArrowFunctionExpression)):
                func_info = {
                    'name': node.id.name if hasattr(node, 'id') and node.id else '<anonymous>',
                    'async': getattr(node, 'async', False),
                    'generator': getattr(node, 'generator', False),
                    'params': len(node.params) if hasattr(node, 'params') else 0,
                }
                functions.append(func_info)
            
            # Recurse
            for key, value in node.__dict__.items():
                if isinstance(value, nodes.Node):
                    visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, nodes.Node):
                            visit(item)
        
        visit(ast)
        return functions
    
    def _extract_imports(self, ast) -> List[str]:
        """Extract import statements."""
        imports = []
        
        def visit(node):
            if isinstance(node, nodes.ImportDeclaration):
                if hasattr(node, 'source') and hasattr(node.source, 'value'):
                    imports.append(node.source.value)
            
            # Recurse
            for key, value in node.__dict__.items():
                if isinstance(value, nodes.Node):
                    visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, nodes.Node):
                            visit(item)
        
        visit(ast)
        return list(set(imports))
    
    def _extract_exports(self, ast) -> List[str]:
        """Extract export statements."""
        exports = []
        
        def visit(node):
            if isinstance(node, (nodes.ExportNamedDeclaration, nodes.ExportDefaultDeclaration)):
                if hasattr(node, 'declaration'):
                    if hasattr(node.declaration, 'id') and hasattr(node.declaration.id, 'name'):
                        exports.append(node.declaration.id.name)
            
            # Recurse
            for key, value in node.__dict__.items():
                if isinstance(value, nodes.Node):
                    visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, nodes.Node):
                            visit(item)
        
        visit(ast)
        return list(set(exports))
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect JavaScript features used in code.
        
        Args:
            code: JavaScript code
            
        Returns:
            List of feature names
        """
        features = []
        
        # Parse AST
        try:
            try:
                ast = esprima.parseScript(code, {'tolerant': True, 'jsx': True})
            except Exception:
                ast = esprima.parseModule(code, {'tolerant': True, 'jsx': True})
            
            # Feature detection via AST
            def visit(node):
                # Classes
                if isinstance(node, nodes.ClassDeclaration) and 'classes' not in features:
                    features.append('classes')
                
                # Arrow functions
                if isinstance(node, nodes.ArrowFunctionExpression) and 'arrow_functions' not in features:
                    features.append('arrow_functions')
                
                # Async/await
                if isinstance(node, (nodes.FunctionDeclaration, nodes.FunctionExpression, nodes.ArrowFunctionExpression)):
                    if getattr(node, 'async', False) and 'async' not in features:
                        features.append('async')
                
                # Await
                if isinstance(node, nodes.AwaitExpression) and 'await' not in features:
                    features.append('await')
                
                # Generators
                if isinstance(node, (nodes.FunctionDeclaration, nodes.FunctionExpression)):
                    if getattr(node, 'generator', False) and 'generators' not in features:
                        features.append('generators')
                
                # Template literals
                if isinstance(node, nodes.TemplateLiteral) and 'template_literals' not in features:
                    features.append('template_literals')
                
                # Destructuring
                if isinstance(node, (nodes.ArrayPattern, nodes.ObjectPattern)) and 'destructuring' not in features:
                    features.append('destructuring')
                
                # Spread operator
                if isinstance(node, nodes.SpreadElement) and 'spread' not in features:
                    features.append('spread')
                
                # Promises
                if isinstance(node, nodes.NewExpression):
                    if hasattr(node.callee, 'name') and node.callee.name == 'Promise' and 'promises' not in features:
                        features.append('promises')
                
                # Recurse
                for key, value in node.__dict__.items():
                    if isinstance(value, nodes.Node):
                        visit(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, nodes.Node):
                                visit(item)
            
            visit(ast)
            
        except Exception as e:
            logger.debug(f"AST parsing failed, using regex fallback: {e}")
            # Regex fallback
            if re.search(r'\bclass\s+\w+', code):
                features.append('classes')
            if re.search(r'=>', code):
                features.append('arrow_functions')
            if re.search(r'\basync\s+function', code):  # More specific pattern
                features.append('async')
            if re.search(r'\bawait\s+', code):
                features.append('await')
        
        # Additional regex-based features (check even if AST worked)
        if re.search(r'\basync\s+', code) and 'async' not in features:  # Catch all async
            features.append('async')
        
        if re.search(r'\.then\(', code) and 'promises' not in features:
            features.append('promises')

        if re.search(r'\bimport\s+', code) and 'modules' not in features:
            features.append('modules')
        
        if re.search(r'\bexport\s+', code) and 'exports' not in features:
            features.append('exports')
        
        logger.debug(f"Detected JavaScript features: {features}")
        
        return features
    
    def format_code(self, code: str) -> str:
        """
        Format JavaScript code (basic).
        
        Args:
            code: JavaScript code
            
        Returns:
            Formatted code
        """
        # Remove trailing whitespace
        lines = [line.rstrip() for line in code.splitlines()]
        
        # Remove multiple blank lines
        formatted_lines = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            
            if is_blank and prev_blank:
                continue
            
            formatted_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(formatted_lines)