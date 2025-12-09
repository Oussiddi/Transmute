"""
Direct translation strategy.

Simple 1:1 feature mapping for straightforward translations.
"""

from typing import Dict, Any, Optional, List

from transmute.strategies.base import TranslationStrategy
from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class DirectStrategy(TranslationStrategy):
    """
    Direct translation strategy.
    
    Best for:
    - Simple code with well-mapped features
    - Low complexity translations
    - Languages with similar paradigms
    
    Example: Python → JavaScript (both dynamic, similar syntax)
    """
    
    def __init__(self):
        """Initialize direct strategy."""
        super().__init__("direct")
    
    def can_handle(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> bool:
        """
        Check if direct strategy can handle translation.
        
        Direct strategy works when:
        - Complexity is low
        - Features have trivial/easy mappings
        - No major paradigm shifts needed
        """
        # Check complexity
        if feature_profile and feature_profile.complexity_score > 0.5:
            return False
        
        # Check if we have feature info
        if not feature_profile or not feature_profile.features_used:
            return True  # Assume simple if no features detected
        
        # Check feature mappings
        features = list(feature_profile.features_used.keys())
        mappings = self.get_applicable_features(
            source_language,
            target_language,
            features
        )
        
        # Can handle if most features are easy to map
        if mappings:
            easy_count = sum(
                1 for m in mappings
                if m['difficulty'] in ['trivial', 'easy']
            )
            return easy_count / len(mappings) > 0.7
        
        return True
    
    def estimate_difficulty(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Estimate difficulty for direct translation.
        
        Returns lower difficulty for simple mappings.
        """
        difficulty = 0.2  # Base difficulty for direct
        
        if feature_profile:
            # Add complexity factor
            difficulty += feature_profile.complexity_score * 0.3
            
            # Check feature mappings
            if feature_profile.features_used:
                features = list(feature_profile.features_used.keys())
                mappings = self.get_applicable_features(
                    source_language,
                    target_language,
                    features
                )
                
                if mappings:
                    # Calculate average mapping difficulty
                    difficulty_map = {
                        'trivial': 0.1,
                        'easy': 0.2,
                        'moderate': 0.4,
                        'hard': 0.6,
                        'very_hard': 0.8,
                        'impossible': 1.0
                    }
                    
                    avg_mapping_difficulty = sum(
                        difficulty_map.get(m['difficulty'], 0.5)
                        for m in mappings
                    ) / len(mappings)
                    
                    difficulty += avg_mapping_difficulty * 0.5
        
        return min(difficulty, 1.0)
    
    def prepare_context(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for direct translation.
        
        Provides:
        - Simple instructions
        - Feature mappings
        - Direct conversion rules
        """
        context = {
            'strategy': 'direct',
            'approach': 'Direct 1:1 translation with minimal changes',
            'instructions': [
                f'Translate from {source_language} to {target_language}',
                'Maintain the same structure and logic',
                'Use idiomatic constructs for the target language',
                'Preserve comments and documentation'
            ],
            'complexity': 'low'
        }
        
        # Add feature mappings
        if feature_profile and feature_profile.features_used:
            features = list(feature_profile.features_used.keys())
            mappings = self.get_applicable_features(
                source_language,
                target_language,
                features
            )
            
            if mappings:
                context['feature_mappings'] = [
                    {
                        'source': m['source_feature'],
                        'target': m['target_feature'],
                        'example': m.get('example_target', '')
                    }
                    for m in mappings[:5]  # Top 5 most relevant
                ]
        
        return context