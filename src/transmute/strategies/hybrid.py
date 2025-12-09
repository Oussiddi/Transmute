"""
Hybrid translation strategy.

Combines multiple strategies for optimal translation.
"""

from typing import Dict, Any, Optional, List

from transmute.strategies.base import TranslationStrategy
from transmute.strategies.direct import DirectStrategy
from transmute.strategies.pattern import PatternStrategy
from transmute.strategies.refactor import RefactorStrategy
from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class HybridStrategy(TranslationStrategy):
    """
    Hybrid translation strategy.
    
    Combines multiple strategies:
    - Uses direct for simple parts
    - Uses pattern for medium complexity
    - Uses refactor for complex parts
    
    Best for: Mixed-complexity codebases
    """
    
    def __init__(self):
        """Initialize hybrid strategy."""
        super().__init__("hybrid")
        
        # Initialize sub-strategies
        self.direct = DirectStrategy()
        self.pattern = PatternStrategy()
        self.refactor = RefactorStrategy()
    
    def can_handle(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> bool:
        """
        Hybrid strategy can handle any translation.
        
        It adapts by choosing appropriate sub-strategies.
        """
        return True  # Always applicable
    
    def estimate_difficulty(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Estimate difficulty using best sub-strategy.
        
        Returns average of applicable strategies.
        """
        difficulties = []
        
        if self.direct.can_handle(unit, source_language, target_language, feature_profile):
            difficulties.append(
                self.direct.estimate_difficulty(unit, source_language, target_language, feature_profile)
            )
        
        if self.pattern.can_handle(unit, source_language, target_language, feature_profile):
            difficulties.append(
                self.pattern.estimate_difficulty(unit, source_language, target_language, feature_profile)
            )
        
        if self.refactor.can_handle(unit, source_language, target_language, feature_profile):
            difficulties.append(
                self.refactor.estimate_difficulty(unit, source_language, target_language, feature_profile)
            )
        
        # Return average, or default if none applicable
        return sum(difficulties) / len(difficulties) if difficulties else 0.5
    
    def _select_primary_strategy(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> TranslationStrategy:
        """
        Select primary strategy based on characteristics.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Best strategy for this translation
        """
        # Check complexity
        complexity = feature_profile.complexity_score if feature_profile else 0.5
        
        if complexity < 0.3:
            logger.debug("Selected direct strategy (low complexity)")
            return self.direct
        elif complexity < 0.6:
            logger.debug("Selected pattern strategy (medium complexity)")
            return self.pattern
        else:
            logger.debug("Selected refactor strategy (high complexity)")
            return self.refactor
    
    def prepare_context(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Prepare context using hybrid approach.
        
        Combines contexts from multiple strategies.
        """
        # Select primary strategy
        primary = self._select_primary_strategy(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        # Get primary context
        context = primary.prepare_context(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        # Override strategy name
        context['strategy'] = 'hybrid'
        context['primary_strategy'] = primary.name
        context['approach'] = f'Hybrid approach (primary: {primary.name})'
        
        # Add guidance from other strategies
        context['additional_guidance'] = []
        
        # Add direct strategy tips if not primary
        if primary.name != 'direct' and self.direct.can_handle(unit, source_language, target_language, feature_profile):
            context['additional_guidance'].append(
                'Use direct mappings where possible for simplicity'
            )
        
        # Add pattern strategy tips if not primary
        if primary.name != 'pattern':
            context['additional_guidance'].append(
                'Leverage common patterns when available'
            )
        
        # Add refactor strategy tips if not primary
        if primary.name != 'refactor' and self.refactor.can_handle(unit, source_language, target_language, feature_profile):
            context['additional_guidance'].append(
                'Consider refactoring if direct translation is awkward'
            )
        
        return context