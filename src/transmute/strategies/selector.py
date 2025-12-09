"""
Strategy selector for choosing optimal translation strategy.

Analyzes code characteristics and selects best strategy.
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from transmute.strategies.base import TranslationStrategy
from transmute.strategies.direct import DirectStrategy
from transmute.strategies.pattern import PatternStrategy
from transmute.strategies.refactor import RefactorStrategy
from transmute.strategies.hybrid import HybridStrategy
from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyRecommendation(Enum):
    """Strategy recommendation levels."""
    PERFECT = "perfect"      # Ideal strategy
    GOOD = "good"           # Good fit
    ACCEPTABLE = "acceptable"  # Can work
    POOR = "poor"           # Not recommended


class StrategySelector:
    """
    Intelligent strategy selector.
    
    Analyzes code characteristics and recommends the best
    translation strategy based on:
    - Code complexity
    - Feature compatibility
    - Language paradigm differences
    - Available patterns
    """
    
    def __init__(self):
        """Initialize strategy selector."""
        self.strategies = {
            'direct': DirectStrategy(),
            'pattern': PatternStrategy(),
            'refactor': RefactorStrategy(),
            'hybrid': HybridStrategy()
        }
        
        logger.info("Initialized StrategySelector with 4 strategies")
    
    def select_strategy(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None,
        prefer_strategy: Optional[str] = None
    ) -> TranslationStrategy:
        """
        Select best translation strategy.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            prefer_strategy: Optional preferred strategy name
            
        Returns:
            Selected strategy instance
        """
        # If preference specified and valid, try to use it
        if prefer_strategy and prefer_strategy in self.strategies:
            strategy = self.strategies[prefer_strategy]
            
            if strategy.can_handle(unit, source_language, target_language, feature_profile):
                logger.info(f"Using preferred strategy: {prefer_strategy}")
                return strategy
            else:
                logger.warning(f"Preferred strategy '{prefer_strategy}' cannot handle unit, selecting alternative")
        
        # Score all strategies
        scores = self._score_strategies(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        # Select best strategy
        best_strategy = max(scores, key=scores.get)
        
        logger.info(
            f"Selected '{best_strategy}' strategy "
            f"(score: {scores[best_strategy]:.2f})"
        )
        
        return self.strategies[best_strategy]
    
    def _score_strategies(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, float]:
        """
        Score all strategies for this translation.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Dictionary mapping strategy names to scores (0-1)
        """
        scores = {}
        
        for name, strategy in self.strategies.items():
            # Check if can handle
            if not strategy.can_handle(unit, source_language, target_language, feature_profile):
                scores[name] = 0.0
                continue
            
            # Calculate score based on multiple factors
            score = self._calculate_strategy_score(
                strategy,
                unit,
                source_language,
                target_language,
                feature_profile
            )
            
            scores[name] = score
        
        return scores
    
    def _calculate_strategy_score(
        self,
        strategy: TranslationStrategy,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Calculate score for a specific strategy.
        
        Higher score = better fit
        
        Args:
            strategy: Strategy to score
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Score (0.0-1.0)
        """
        score = 0.5  # Base score
        
        # Get difficulty estimate
        difficulty = strategy.estimate_difficulty(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        # Lower difficulty = higher score
        score += (1.0 - difficulty) * 0.3
        
        # Consider complexity if available
        if feature_profile:
            complexity = feature_profile.complexity_score
            
            # Match strategy to complexity
            if strategy.name == 'direct':
                # Direct is best for low complexity
                score += (1.0 - complexity) * 0.3
            elif strategy.name == 'pattern':
                # Pattern is best for medium complexity
                if 0.3 <= complexity <= 0.7:
                    score += 0.3
                else:
                    score += 0.1
            elif strategy.name == 'refactor':
                # Refactor is best for high complexity
                score += complexity * 0.3
            elif strategy.name == 'hybrid':
                # Hybrid is always decent
                score += 0.2
            
            # Boost pattern strategy if patterns detected
            if strategy.name == 'pattern' and feature_profile.patterns_detected:
                score += min(len(feature_profile.patterns_detected) * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def recommend_strategy(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Get detailed strategy recommendation.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Recommendation dictionary with:
            - recommended: Best strategy name
            - alternatives: List of alternative strategies
            - reasoning: Explanation of recommendation
            - confidence: Confidence in recommendation (0-1)
        """
        # Score all strategies
        scores = self._score_strategies(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        # Sort by score
        sorted_strategies = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top strategy
        recommended, best_score = sorted_strategies[0]
        
        # Get alternatives (score > 0.3)
        alternatives = [
            name for name, score in sorted_strategies[1:]
            if score > 0.3
        ]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            recommended,
            best_score,
            feature_profile
        )
        
        # Calculate confidence
        if len(sorted_strategies) > 1:
            second_score = sorted_strategies[1][1]
            confidence = (best_score - second_score) / best_score if best_score > 0 else 0.5
        else:
            confidence = best_score
        
        return {
            'recommended': recommended,
            'alternatives': alternatives,
            'reasoning': reasoning,
            'confidence': min(confidence, 1.0),
            'scores': scores
        }
    
    def _generate_reasoning(
        self,
        strategy_name: str,
        score: float,
        feature_profile: Optional[FeatureProfile] = None
    ) -> str:
        """
        Generate human-readable reasoning for recommendation.
        
        Args:
            strategy_name: Recommended strategy name
            score: Strategy score
            feature_profile: Optional feature profile
            
        Returns:
            Reasoning string
        """
        reasons = []
        
        if feature_profile:
            complexity = feature_profile.complexity_score
            
            if strategy_name == 'direct':
                reasons.append("Code has low complexity")
                reasons.append("Features have straightforward mappings")
            elif strategy_name == 'pattern':
                reasons.append("Code has medium complexity")
                if feature_profile.patterns_detected:
                    reasons.append(f"Detected {len(feature_profile.patterns_detected)} design patterns")
                reasons.append("Can leverage similar code examples")
            elif strategy_name == 'refactor':
                reasons.append("Code has high complexity")
                reasons.append("Requires significant restructuring")
            elif strategy_name == 'hybrid':
                reasons.append("Mixed complexity across codebase")
                reasons.append("Benefits from multi-strategy approach")
        else:
            reasons.append(f"{strategy_name.capitalize()} strategy is most appropriate")
        
        if score < 0.5:
            reasons.append("⚠️ Translation may be challenging")
        elif score > 0.8:
            reasons.append("✓ High confidence in this approach")
        
        return "; ".join(reasons)
    
    def get_strategy_comparison(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> List[Dict[str, Any]]:
        """
        Get comparison of all strategies.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            List of strategy comparisons with scores and notes
        """
        scores = self._score_strategies(
            unit,
            source_language,
            target_language,
            feature_profile
        )
        
        comparisons = []
        
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            strategy = self.strategies[name]
            
            difficulty = strategy.estimate_difficulty(
                unit,
                source_language,
                target_language,
                feature_profile
            ) if score > 0 else 1.0
            
            can_handle = strategy.can_handle(
                unit,
                source_language,
                target_language,
                feature_profile
            )
            
            comparisons.append({
                'strategy': name,
                'score': score,
                'difficulty': difficulty,
                'can_handle': can_handle,
                'recommendation': self._get_recommendation_level(score)
            })
        
        return comparisons
    
    def _get_recommendation_level(self, score: float) -> str:
        """
        Get recommendation level from score.
        
        Args:
            score: Strategy score
            
        Returns:
            Recommendation level
        """
        if score >= 0.8:
            return StrategyRecommendation.PERFECT.value
        elif score >= 0.6:
            return StrategyRecommendation.GOOD.value
        elif score >= 0.4:
            return StrategyRecommendation.ACCEPTABLE.value
        else:
            return StrategyRecommendation.POOR.value