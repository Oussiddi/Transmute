"""
Pattern-based translation strategy.

Uses similar code patterns from RAG for informed translation.
"""

from typing import Dict, Any, Optional, List

from transmute.strategies.base import TranslationStrategy
from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class PatternStrategy(TranslationStrategy):
    """
    Pattern-based translation strategy.
    
    Best for:
    - Medium complexity code
    - Common patterns and idioms
    - When similar translations exist
    
    Leverages RAG to find similar code patterns and use them as examples.
    """
    
    def __init__(self):
        """Initialize pattern strategy."""
        super().__init__("pattern")
    
    def can_handle(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> bool:
        """
        Check if pattern strategy can handle translation.
        
        Pattern strategy works when:
        - Complexity is low-to-medium
        - Code uses common patterns
        - Features have moderate mappings
        """
        # Check complexity
        if feature_profile and feature_profile.complexity_score > 0.7:
            return False
        
        # Pattern strategy is good for most cases
        return True
    
    def estimate_difficulty(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Estimate difficulty for pattern-based translation.
        
        Returns moderate difficulty.
        """
        difficulty = 0.4  # Base difficulty for pattern
        
        if feature_profile:
            # Add complexity factor
            difficulty += feature_profile.complexity_score * 0.4
            
            # Patterns help reduce difficulty
            if feature_profile.patterns_detected:
                # Each detected pattern reduces difficulty slightly
                pattern_factor = min(len(feature_profile.patterns_detected) * 0.05, 0.2)
                difficulty -= pattern_factor
        
        return max(0.1, min(difficulty, 1.0))
    
    def prepare_context(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for pattern-based translation.
        
        Provides:
        - Pattern examples from RAG
        - Feature mappings
        - Idiom translations
        """
        context = {
            'strategy': 'pattern',
            'approach': 'Pattern-based translation using similar code examples',
            'instructions': [
                f'Translate from {source_language} to {target_language}',
                'Follow patterns from similar code examples',
                'Use idiomatic constructs that match the patterns',
                'Adapt patterns to fit the specific code structure'
            ],
            'complexity': 'medium',
            'use_rag': True  # Signal to use RAG patterns
        }
        
        # Add detected patterns
        if feature_profile:
            if feature_profile.patterns_detected:
                context['detected_patterns'] = feature_profile.patterns_detected
            
            if feature_profile.features_used:
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
                            'notes': m.get('notes', ''),
                            'example': m.get('example_target', '')
                        }
                        for m in mappings[:10]  # Top 10 most relevant
                    ]
        
        return context