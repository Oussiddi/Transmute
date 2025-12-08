"""
C# language plugin with tree-sitter parsing.

Uses tree-sitter for C# code analysis.
"""

from typing import Dict, Any, List
from pathlib import Path
import re

from transmute.languages.base import LanguagePlugin
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class CSharpPlugin(LanguagePlugin):
    """
    C# language plugin with regex-based parsing.
    
    Note: Full AST parsing would require tree-sitter-c-sharp.
    """
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse C# file.
        
        Args:
            file_path: Path to C# file
            
        Returns:
            Dictionary with parsed information
        """
        logger.debug(f"Parsing C# file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            classes = self._extract_classes(code)
            interfaces = self._extract_interfaces(code)
            methods = self._extract_methods(code)
            properties = self._extract_properties(code)
            
            features_used = self.detect_features(code)
            line_count = len(code.splitlines())
            
            return {
                'classes': classes,
                'interfaces': interfaces,
                'methods': methods,
                'properties': properties,
                'features_used': features_used,
                'line_count': line_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {
                'classes': [],
                'interfaces': [],
                'methods': [],
                'properties': [],
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
    
    def _extract_methods(self, code: str) -> List[str]:
        """Extract method names."""
        # Matches: public/private/protected void/int/etc MethodName(
        pattern = r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?[\w<>\[\]]+\s+(\w+)\s*\('
        return re.findall(pattern, code)
    
    def _extract_properties(self, code: str) -> List[str]:
        """Extract property names."""
        # Matches: public Type PropertyName { get; set; }
        pattern = r'\b(?:public|private|protected|internal)\s+[\w<>\[\]]+\s+(\w+)\s*\{\s*(?:get|set)'
        return re.findall(pattern, code)
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect C# features.
        
        Args:
            code: C# code
            
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
        
        # Structs
        if re.search(r'\bstruct\s+\w+', code):
            features.append('structs')
        
        # Enums
        if re.search(r'\benum\s+\w+', code):
            features.append('enums')
        
        # Properties
        if re.search(r'\{\s*(?:get|set)\s*[;}]', code):
            features.append('properties')
        
        # Events
        if re.search(r'\bevent\s+', code):
            features.append('events')
        
        # Delegates
        if re.search(r'\bdelegate\s+', code):
            features.append('delegates')
        
        # Generics
        if re.search(r'<[A-Z]\w*(?:,\s*[A-Z]\w*)*>', code):
            features.append('generics')
        
        # Async/await
        if re.search(r'\basync\s+', code):
            features.append('async')
        
        if re.search(r'\bawait\s+', code):
            features.append('await')
        
        # LINQ
        if re.search(r'\bfrom\s+\w+\s+in\s+', code) or re.search(r'\.Where\(|\.Select\(', code):
            features.append('linq')
        
        # Lambdas
        if re.search(r'=>', code):
            features.append('lambdas')
        
        # Extension methods
        if re.search(r'\bthis\s+\w+', code):
            features.append('extension_methods')
        
        # Attributes
        if re.search(r'\[\w+.*\]', code):
            features.append('attributes')
        
        # Nullable types
        if re.search(r'\w+\?', code):
            features.append('nullable_types')
        
        # Pattern matching
        if re.search(r'\bis\s+\w+|\bswitch\s*\{', code):
            features.append('pattern_matching')
        
        # Records
        if re.search(r'\brecord\s+', code):
            features.append('records')
        
        # Init-only setters
        if re.search(r'\binit\s*;', code):
            features.append('init_only_setters')
        
        logger.debug(f"Detected C# features: {features}")
        
        return features
    
    def format_code(self, code: str) -> str:
        """Format C# code (basic)."""
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