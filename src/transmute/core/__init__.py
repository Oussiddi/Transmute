"""Core modules for Transmute."""

from transmute.core.config import (
    load_yaml,
    merge_configs,
    LLMConfig,
    RAGConfig,
    TransmuteConfig,
)
from transmute.core.state import (
    RepositoryMetadata,
    LanguageInfo,
    FeatureProfile,
    FeatureType,
    TranslationUnit,
    TranslationStatus,
    TranslationStrategy,
    StrategyType,
    ValidationResult,
    MigrationPlan,
    TransmuteState,
)

__all__ = [
    # Config
    "load_yaml",
    "merge_configs",
    "LLMConfig",
    "RAGConfig",
    "TransmuteConfig",
    # State
    "RepositoryMetadata",
    "LanguageInfo",
    "FeatureProfile",
    "FeatureType",
    "TranslationUnit",
    "TranslationStatus",
    "TranslationStrategy",
    "StrategyType",
    "ValidationResult",
    "MigrationPlan",
    "TransmuteState",
]