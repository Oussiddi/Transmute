"""
Language registry for managing language plugins.

Discovers, loads, and provides access to language plugins.
"""

from typing import Dict, List, Optional, Type
from pathlib import Path
import importlib
import pkgutil

from transmute.languages.base import LanguagePlugin, LanguageConfig
from transmute.core.config import load_yaml
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class LanguageRegistry:
    """
    Registry for managing language plugins.
    
    Discovers plugins, loads configurations, and provides access to language
    implementations.
    """
    
    def __init__(self, config_dir: Path = Path("config/languages")):
        """
        Initialize registry.
        
        Args:
            config_dir: Directory containing language YAML configs
        """
        self.config_dir = config_dir
        self._plugins: Dict[str, LanguagePlugin] = {}
        self._configs: Dict[str, LanguageConfig] = {}
        
        logger.info(f"Initialized LanguageRegistry with config dir: {config_dir}")
    
    def load_language_config(self, language_name: str) -> LanguageConfig:
        """
        Load language configuration from YAML.
        
        Args:
            language_name: Name of language (e.g., 'python')
            
        Returns:
            LanguageConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_path = self.config_dir / f"{language_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Language config not found: {config_path}"
            )
        
        logger.debug(f"Loading language config: {config_path}")
        
        config_data = load_yaml(config_path)
        config = LanguageConfig(**config_data)
        
        self._configs[language_name] = config
        logger.info(f"Loaded config for {config.display_name}")
        
        return config
    
    def register_plugin(
        self,
        language_name: str,
        plugin_class: Type[LanguagePlugin]
    ) -> None:
        """
        Register a language plugin.
        
        Args:
            language_name: Name of language
            plugin_class: Plugin class (subclass of LanguagePlugin)
            
        Raises:
            ValueError: If plugin is already registered
        """
        if language_name in self._plugins:
            raise ValueError(
                f"Plugin already registered for language: {language_name}"
            )
        
        # Load config if not already loaded
        if language_name not in self._configs:
            self.load_language_config(language_name)
        
        # Instantiate plugin with config
        config = self._configs[language_name]
        plugin = plugin_class(config)
        
        self._plugins[language_name] = plugin
        logger.info(f"Registered plugin: {plugin}")
    
    def get_plugin(self, language_name: str) -> Optional[LanguagePlugin]:
        """
        Get plugin for a language.
        
        Args:
            language_name: Name of language
            
        Returns:
            LanguagePlugin instance or None if not found
        """
        return self._plugins.get(language_name)
    
    def get_all_plugins(self) -> Dict[str, LanguagePlugin]:
        """
        Get all registered plugins.
        
        Returns:
            Dictionary mapping language names to plugins
        """
        return self._plugins.copy()
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language names.
        
        Returns:
            List of language names
        """
        return list(self._plugins.keys())
    
    def detect_language(self, file_path: Path) -> Optional[str]:
        """
        Detect language from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Language name or None if not detected
        """
        for name, plugin in self._plugins.items():
            if plugin.is_source_file(file_path):
                logger.debug(f"Detected {name} from file: {file_path}")
                return name
        
        logger.warning(f"Could not detect language for file: {file_path}")
        return None
    
    def is_supported(self, language_name: str) -> bool:
        """
        Check if language is supported.
        
        Args:
            language_name: Name of language
            
        Returns:
            True if language plugin is registered
        """
        return language_name in self._plugins
    
    def __repr__(self) -> str:
        """String representation."""
        langs = ', '.join(self.get_supported_languages())
        return f"<LanguageRegistry: {len(self._plugins)} languages ({langs})>"