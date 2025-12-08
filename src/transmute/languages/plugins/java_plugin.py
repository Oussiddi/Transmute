"""
Java language plugin.

Handles Java-specific parsing, feature detection, and code formatting.
"""

from typing import List, Dict, Any
from pathlib import Path
import re

from transmute.languages.base import LanguagePlugin, LanguageConfig
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class JavaPlugin(LanguagePlugin):
    """
    Java language plugin.
    
    Provides Java-specific functionality. Uses regex-based parsing for now
    (tree-sitter would be better for production).
    """
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Java file.
        
        Args:
            file_path: Path to Java file
            
        Returns:
            Dictionary with parsed structure
        """
        logger.debug(f"Parsing Java file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = {
                'classes': self._extract_classes(code),
                'interfaces': self._extract_interfaces(code),
                'methods': self._extract_methods(code),
                'imports': self._extract_imports(code),
                'features_used': self.detect_features(code),
                'line_count': len(code.splitlines()),
            }
            
            logger.info(f"Parsed Java file: {len(result['classes'])} classes, "
                       f"{len(result['interfaces'])} interfaces")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect Java features used in code.
        
        Args:
            code: Java source code
            
        Returns:
            List of detected features
        """
        features = []
        
        # Classes
        if re.search(r'\bclass\s+\w+', code):
            features.append('classes')
        
        # Interfaces
        if re.search(r'\binterface\s+\w+', code):
            features.append('interfaces')
        
        # Inheritance
        if re.search(r'\bextends\s+\w+', code):
            features.append('inheritance')
        
        # Generics
        if re.search(r'<[A-Z]\w*(?:,\s*[A-Z]\w*)*>', code):
            features.append('generics')
        
        # Annotations
        if re.search(r'@\w+', code):
            features.append('annotations')
        
        # Lambdas
        if '->' in code:
            features.append('lambdas')
        
        # Streams
        if re.search(r'\.stream\(\)', code):
            features.append('streams')
        
        # Threads
        if re.search(r'\b(Thread|Runnable|ExecutorService)', code):
            features.append('threads')
        
        # Exceptions
        if re.search(r'\b(try|catch|finally|throws?)\b', code):
            features.append('exceptions')
        
        # Reflection
        if re.search(r'\b(Class\.forName|getClass|getDeclaredMethod)', code):
            features.append('reflection')
        
        # Enums
        if re.search(r'\benum\s+\w+', code):
            features.append('enums')
        
        # Records (Java 14+)
        if re.search(r'\brecord\s+\w+', code):
            features.append('records')
        
        logger.debug(f"Detected Java features: {features}")
        
        return features
    
    def format_code(self, code: str) -> str:
        """
        Format Java code (basic formatting).
        
        Args:
            code: Unformatted code
            
        Returns:
            Formatted code
        """
        # Basic formatting
        lines = code.splitlines()
        formatted_lines = [line.rstrip() for line in lines]
        
        return '\n'.join(formatted_lines)
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        
        # Match class declarations
        pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
        
        for match in re.finditer(pattern, code):
            classes.append({
                'name': match.group(1),
                'extends': match.group(2) if match.group(2) else None,
            })
        
        return classes
    
    def _extract_interfaces(self, code: str) -> List[str]:
        """Extract interface definitions."""
        interfaces = []
        
        pattern = r'(?:public\s+)?interface\s+(\w+)'
        
        for match in re.finditer(pattern, code):
            interfaces.append(match.group(1))
        
        return interfaces
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract method definitions."""
        methods = []
        
        # Simple method pattern
        pattern = r'(?:public|private|protected)\s+(?:static\s+)?(\w+)\s+(\w+)\s*\('
        
        for match in re.finditer(pattern, code):
            methods.append({
                'return_type': match.group(1),
                'name': match.group(2),
            })
        
        return methods
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements."""
        imports = []
        
        pattern = r'import\s+(?:static\s+)?([\w.]+);'
        
        for match in re.finditer(pattern, code):
            imports.append(match.group(1))
        
        return imports