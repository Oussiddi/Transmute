"""
TypeScript language plugin.

Extends JavaScript plugin with TypeScript-specific features.
"""

from typing import Dict, Any, List
from pathlib import Path
import re

from transmute.languages.plugins.javascript_plugin import JavaScriptPlugin
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TypeScriptPlugin(JavaScriptPlugin):
    """
    TypeScript language plugin.
    
    Extends JavaScript plugin with TypeScript-specific features.
    """
    
    def detect_features(self, code: str) -> List[str]:
        """
        Detect TypeScript features.
        
        Args:
            code: TypeScript code
            
        Returns:
            List of feature names
        """
        # Get base JavaScript features
        features = super().detect_features(code)
        
        # TypeScript-specific features
        
        # Interfaces
        if re.search(r'\binterface\s+\w+', code):
            features.append('interfaces')
        
        # Type annotations
        if re.search(r':\s*\w+(\[\])?(\s*\|\s*\w+)*', code):
            features.append('type_annotations')
        
        # Generics
        if re.search(r'<[A-Z]\w*(?:,\s*[A-Z]\w*)*>', code):
            features.append('generics')
        
        # Enums
        if re.search(r'\benum\s+\w+', code):
            features.append('enums')
        
        # Type aliases
        if re.search(r'\btype\s+\w+\s*=', code):
            features.append('type_aliases')
        
        # Decorators
        if re.search(r'@\w+', code):
            features.append('decorators')
        
        # Namespaces
        if re.search(r'\bnamespace\s+\w+', code):
            features.append('namespaces')
        
        # Abstract classes
        if re.search(r'\babstract\s+class', code):
            features.append('abstract_classes')
        
        # Readonly
        if re.search(r'\breadonly\s+', code):
            features.append('readonly')
        
        # Access modifiers
        if re.search(r'\b(public|private|protected)\s+', code):
            features.append('access_modifiers')
        
        logger.debug(f"Detected TypeScript features: {features}")
        
        return features