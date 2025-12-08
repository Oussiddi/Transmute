"""
Base classes for language plugins.

Defines the abstract interface that all language plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from pydantic import BaseModel, Field

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class LanguageConfig(BaseModel):
    """
    Configuration for a programming language.
    
    Loaded from YAML files in config/languages/
    """
    
    name: str = Field(
        description="Language name (e.g., 'python', 'java')"
    )
    
    display_name: str = Field(
        description="Display name (e.g., 'Python', 'Java')"
    )
    
    version: Optional[str] = Field(
        default=None,
        description="Default version (e.g., '3.11', '17')"
    )
    
    extensions: List[str] = Field(
        description="File extensions (e.g., ['.py', '.pyw'])"
    )
    
    features: List[str] = Field(
        default_factory=list,
        description="Supported language features"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Language keywords"
    )
    
    frameworks: List[str] = Field(
        default_factory=list,
        description="Common frameworks for this language"
    )
    
    build_tools: List[str] = Field(
        default_factory=list,
        description="Build tools (e.g., ['maven', 'gradle'])"
    )
    
    package_managers: List[str] = Field(
        default_factory=list,
        description="Package managers (e.g., ['pip', 'poetry'])"
    )
    
    syntax_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Syntax mappings to other languages"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class LanguagePlugin(ABC):
    """
    Abstract base class for language plugins.
    
    Each language (Python, Java, etc.) implements this interface to provide
    language-specific functionality like parsing, code generation, and analysis.
    """
    
    def __init__(self, config: LanguageConfig):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Language configuration from YAML
        """
        self.config = config
        self.name = config.name
        self.display_name = config.display_name
        logger.info(f"Initialized {self.display_name} language plugin")
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a source file and extract structure.
        
        Args:
            file_path: Path to source file
            
        Returns:
            Dictionary containing parsed AST and metadata
            
        Example:
            {
                "classes": [...],
                "functions": [...],
                "imports": [...],
                "features_used": [...]
            }
        """
        pass
    
    @abstractmethod
    def detect_features(self, code: str) -> List[str]:
        """
        Detect language features used in code.
        
        Args:
            code: Source code string
            
        Returns:
            List of feature names (e.g., ["classes", "async", "decorators"])
        """
        pass
    
    @abstractmethod
    def format_code(self, code: str) -> str:
        """
        Format code according to language conventions.
        
        Args:
            code: Unformatted code
            
        Returns:
            Formatted code
        """
        pass
    
    def is_source_file(self, file_path: Path) -> bool:
        """
        Check if file is a source file for this language.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file extension matches this language
        """
        return file_path.suffix in self.config.extensions
    
    def get_features(self) -> List[str]:
        """
        Get list of features supported by this language.
        
        Returns:
            List of feature names
        """
        return self.config.features
    
    def get_frameworks(self) -> List[str]:
        """
        Get list of common frameworks for this language.
        
        Returns:
            List of framework names
        """
        return self.config.frameworks
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if language supports a specific feature.
        
        Args:
            feature: Feature name (e.g., "async", "generics")
            
        Returns:
            True if feature is supported
        """
        return feature in self.config.features
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}: {self.display_name}>"