"""
Refactoring translation strategy.

Major restructuring for complex translations with paradigm shifts.
"""

from typing import Dict, Any, Optional, List

from transmute.strategies.base import TranslationStrategy
from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class RefactorStrategy(TranslationStrategy):
    """
    Refactoring translation strategy.
    
    Best for:
    - High complexity code
    - Paradigm shifts (functional → OOP, dynamic → static)
    - Significant architectural changes needed
    
    Example: Python (dynamic, duck-typed) → Java (static, type-safe)
    """
    
    def __init__(self):
        """Initialize refactor strategy."""
        super().__init__("refactor")
    
    def can_handle(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> bool:
        """
        Check if refactor strategy can handle translation.
        
        Refactor strategy works when:
        - Complexity is high
        - Features need significant restructuring
        - Major paradigm differences
        """
        # Check complexity
        if feature_profile and feature_profile.complexity_score < 0.5:
            return False  # Too simple for refactoring
        
        # Check feature mappings for hard translations
        if feature_profile and feature_profile.features_used:
            features = list(feature_profile.features_used.keys())
            mappings = self.get_applicable_features(
                source_language,
                target_language,
                features
            )
            
            if mappings:
                hard_count = sum(
                    1 for m in mappings
                    if m['difficulty'] in ['hard', 'very_hard']
                )
                # Need refactoring if many hard features
                return hard_count / len(mappings) > 0.3
        
        return True  # Can handle if no other info
    
    def estimate_difficulty(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Estimate difficulty for refactoring translation.
        
        Returns higher difficulty for complex refactoring.
        """
        difficulty = 0.6  # Base difficulty for refactoring
        
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
                    # Hard features increase difficulty
                    difficulty_map = {
                        'trivial': 0.1,
                        'easy': 0.2,
                        'moderate': 0.4,
                        'hard': 0.7,
                        'very_hard': 0.9,
                        'impossible': 1.0
                    }
                    
                    avg_mapping_difficulty = sum(
                        difficulty_map.get(m['difficulty'], 0.5)
                        for m in mappings
                    ) / len(mappings)
                    
                    difficulty = (difficulty + avg_mapping_difficulty) / 2
        
        return min(difficulty, 1.0)
    
    def prepare_context(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for refactoring translation.
        
        Provides:
        - Restructuring guidelines
        - Paradigm shift mappings
        - Architecture recommendations
        """
        context = {
            'strategy': 'refactor',
            'approach': 'Refactor and restructure for target language paradigms',
            'instructions': [
                f'Translate from {source_language} to {target_language} with refactoring',
                'Restructure code to fit target language paradigms',
                'Add necessary type annotations, interfaces, or abstractions',
                'Consider design patterns appropriate for target language',
                'Maintain functional equivalence while improving structure'
            ],
            'complexity': 'high',
            'use_rag': True,
            'allow_restructuring': True
        }
        
        # Add language-specific guidance
        features = list(feature_profile.features_used.keys()) if feature_profile and feature_profile.features_used else []
        compatibility = self.language_mapper.calculate_compatibility_score(
            source_language,
            target_language,
            features
        )
        
        context['compatibility_score'] = compatibility
        
        if compatibility < 0.5:
            context['warnings'] = [
                'Low language compatibility - significant changes needed',
                'Consider major architectural restructuring',
                'May require additional helper classes or utilities'
            ]
        
        # Add feature mappings with alternatives
        if feature_profile and feature_profile.features_used:
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
                        'difficulty': m['difficulty'],
                        'notes': m.get('notes', ''),
                        'alternatives': m.get('alternatives', [])
                    }
                    for m in mappings
                ]
        
        # Add detected patterns for guidance
        if feature_profile and feature_profile.patterns_detected:
            context['design_patterns'] = feature_profile.patterns_detected
            context['pattern_guidance'] = 'Consider how these patterns translate to target language'
        
        return context