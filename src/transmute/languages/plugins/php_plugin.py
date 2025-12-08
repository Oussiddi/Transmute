"""
PHP language plugin with regex-based parsing.

Uses regex patterns for PHP code analysis.
"""

from typing import Dict, Any, List
from pathlib import Path
import re

from transmute.languages.base import LanguagePlugin
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class PHPPlugin(LanguagePlugin):
    """
    PHP language plugin.
    
    Uses regex-based parsing for PHP code analysis.
    """
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse PHP file.
        
        Args:
            file_path: Path to PHP file
            
        Returns:
            Dictionary with parsed information
        """
        logger.debug(f"Parsing PHP file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            classes = self._extract_classes(code)
            interfaces = self._extract_interfaces(code)
            traits = self._extract_traits(code)
            functions = self._extract_functions(code)
            
            features_used = self.detect_features(code)
            line_count = len(code.splitlines())
            
            return {
                'classes': classes,
                'interfaces': interfaces,
                'traits': traits,
                'functions': functions,
                'features_used': features_used,
                'line_count': line_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {
                'classes': [],
                'interfaces': [],
                'traits': [],
                'functions': [],
                'features_used': [],
                'line_count': 0,
                'error': str(e)
            }
    
    def _extract_classes(self, code: str) -> List[str]:
        """Extract class names."""
        pattern = r'\bclass\s+(\w+)'
        return re.findall(pattern, code)
    
    def _extract_interfaces(self, code: str) -> List[str]:
        """Extract interface names."""
        pattern = r'\binterface\s+(\w+)'
        return re.findall(pattern, code)
    
    def _extract_traits(self, code: str) -> List[str]:
        """Extract trait names."""
        pattern = r'\btrait\s+(\w+)'
        return re.findall(pattern, code)
    
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function names."""
        pattern = r'\bfunction\s+(\w+)\s*\('
        return re.findall(pattern, code)
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect PHP features.
        
        Args:
            code: PHP code
            
        Returns:
            List of feature names
        """
        features = []
        
        # Classes
        if re.search(r'\bclass\s+\w+', code):
            features.append('classes')
        
        # Interfaces
        if re.search(r'\binterface\s+\w+', code):
            features.append('interfaces')
        
        # Traits
        if re.search(r'\btrait\s+\w+', code):
            features.append('traits')
        
        # Namespaces
        if re.search(r'\bnamespace\s+', code):
            features.append('namespaces')
        
        # Functions
        if re.search(r'\bfunction\s+\w+', code):
            features.append('functions')
        
        # Closures/Anonymous functions
        if re.search(r'\bfunction\s*\(', code):
            features.append('closures')
        
        # Generators
        if re.search(r'\byield\s+', code):
            features.append('generators')
        
        # Attributes (PHP 8+)
        if re.search(r'#\[\w+', code):
            features.append('attributes')
        
        # Enums (PHP 8.1+)
        if re.search(r'\benum\s+\w+', code):
            features.append('enums')
        
        # Type hints
        if re.search(r':\s*\??\w+', code):
            features.append('type_hints')
        
        # Return types
        if re.search(r'\):\s*\??\w+', code):
            features.append('return_types')
        
        # Nullable types
        if re.search(r'\?\w+', code):
            features.append('nullable_types')
        
        # Union types (PHP 8+)
        if re.search(r':\s*\w+\|\w+', code):
            features.append('union_types')
        
        # Named arguments (PHP 8+)
        if re.search(r'\w+:\s*', code):
            features.append('named_arguments')
        
        # Match expression (PHP 8+)
        if re.search(r'\bmatch\s*\(', code):
            features.append('match_expression')
        
        # Arrow functions (PHP 7.4+)
        if re.search(r'\bfn\s*\(', code):
            features.append('arrow_functions')
        
        # Nullsafe operator (PHP 8+)
        if re.search(r'\?\->', code):
            features.append('nullsafe_operator')
        
        # Visibility modifiers
        if re.search(r'\b(public|private|protected)\s+', code):
            features.append('visibility')
        
        # Static
        if re.search(r'\bstatic\s+', code):
            features.append('static')
        
        # Abstract
        if re.search(r'\babstract\s+', code):
            features.append('abstract')
        
        # Final
        if re.search(r'\bfinal\s+', code):
            features.append('final')
        
        logger.debug(f"Detected PHP features: {features}")
        
        return features
    
    def format_code(self, code: str) -> str:
        """Format PHP code (basic)."""
        lines = [line.rstrip() for line in code.splitlines()]
        
        formatted_lines = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            
            if is_blank and prev_blank:
                continue
            
            formatted_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(formatted_lines)