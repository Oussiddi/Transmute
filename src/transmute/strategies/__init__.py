"""Translation strategies for Transmute."""

from transmute.strategies.base import TranslationStrategy
from transmute.strategies.direct import DirectStrategy
from transmute.strategies.pattern import PatternStrategy
from transmute.strategies.refactor import RefactorStrategy
from transmute.strategies.hybrid import HybridStrategy
from transmute.strategies.selector import StrategySelector, StrategyRecommendation

__all__ = [
    "TranslationStrategy",
    "DirectStrategy",
    "PatternStrategy",
    "RefactorStrategy",
    "HybridStrategy",
    "StrategySelector",
    "StrategyRecommendation",
]