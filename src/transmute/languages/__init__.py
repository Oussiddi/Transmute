"""Language plugin system for Transmute."""

from transmute.languages.base import LanguagePlugin, LanguageConfig
from transmute.languages.registry import LanguageRegistry

__all__ = [
    "LanguagePlugin",
    "LanguageConfig",
    "LanguageRegistry",
]