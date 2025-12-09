"""
Base translation strategy.

Defines interface for all translation strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.languages import LanguageMapper, EquivalenceMatrix
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TranslationStrategy(ABC):
    """
    Abstract base class for translation strategies.
    
    Different strategies handle different translation scenarios:
    - Direct: Simple 1:1 feature mapping
    - Pattern: Uses similar code patterns from RAG
    - Refactor: Restructures code for target paradigm
    - Hybrid: Combines multiple strategies
    """
    
    def __init__(self, name: str):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
        """
        self.name = name
        self.language_mapper = LanguageMapper()
        self.equivalence_matrix = EquivalenceMatrix()
        
        logger.debug(f"Initialized {name} strategy")
    
    @abstractmethod
    def can_handle(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> bool:
        """
        Check if strategy can handle this translation.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            True if strategy can handle this translation
        """
        pass
    
    @abstractmethod
    def estimate_difficulty(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> float:
        """
        Estimate translation difficulty (0.0-1.0).
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Difficulty score (0=easy, 1=very hard)
        """
        pass
    
    @abstractmethod
    def prepare_context(
        self,
        unit: TranslationUnit,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None
    ) -> Dict[str, Any]:
        """
        Prepare translation context for LLM.
        
        Args:
            unit: Translation unit
            source_language: Source language
            target_language: Target language
            feature_profile: Optional feature profile
            
        Returns:
            Context dictionary for LLM prompt
        """
        pass
    
    def get_applicable_features(
        self,
        source_language: str,
        target_language: str,
        features: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get feature mappings for translation.
        
        Args:
            source_language: Source language
            target_language: Target language
            features: List of features to map
            
        Returns:
            List of feature mappings with difficulty
        """
        mappings = []
        
        for feature in features:
            mapping = self.language_mapper.map_feature(
                source_language,
                target_language,
                feature
            )
            
            if mapping:
                mappings.append(mapping)
        
        return mappings
    
    def calculate_confidence(
        self,
        difficulty: float,
        feature_mappings: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for translation.
        
        Args:
            difficulty: Difficulty score
            feature_mappings: Feature mappings used
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence from difficulty
        base_confidence = 1.0 - difficulty
        
        # Adjust based on feature mapping availability
        if feature_mappings:
            mapped_ratio = len([
                m for m in feature_mappings
                if m['difficulty'] in ['trivial', 'easy', 'moderate']
            ]) / len(feature_mappings)
            
            confidence = base_confidence * 0.7 + mapped_ratio * 0.3
        else:
            confidence = base_confidence
        
        return max(0.0, min(1.0, confidence))
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}: {self.name}>"