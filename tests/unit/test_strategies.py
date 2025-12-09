"""
Tests for translation strategies.

Tests strategy selection, difficulty estimation, and context preparation.
"""

import pytest
from pathlib import Path

from transmute.strategies import (
    TranslationStrategy,
    DirectStrategy,
    PatternStrategy,
    RefactorStrategy,
    HybridStrategy,
    StrategySelector,
    StrategyRecommendation
)
from transmute.core.state import TranslationUnit, FeatureProfile


@pytest.fixture
def simple_unit():
    """Create simple translation unit."""
    return TranslationUnit(
        unit_id="simple",
        source_path=Path("simple.py"),
        source_code="def hello():\n    print('Hello')"
    )


@pytest.fixture
def complex_unit():
    """Create complex translation unit."""
    return TranslationUnit(
        unit_id="complex",
        source_path=Path("complex.py"),
        source_code="""
class DataProcessor:
    def __init__(self):
        self.data = []
    
    @property
    def size(self):
        return len(self.data)
    
    def process(self, items):
        return [x**2 for x in items if x > 0]
"""
    )


@pytest.fixture
def low_complexity_profile():
    """Create low complexity feature profile."""
    return FeatureProfile(
        language="python",
        features_used={'functions': 5, 'variables': 10},
        complexity_score=0.2,
        patterns_detected=[],
        external_dependencies=[]
    )



@pytest.fixture
def medium_complexity_profile():
    """Create medium complexity feature profile."""
    return FeatureProfile(
        language="python",
        features_used={'classes': 3, 'functions': 8, 'list_comprehensions': 2},
        complexity_score=0.5,
        patterns_detected=['singleton'],
        external_dependencies=['pytest']
    )


@pytest.fixture
def high_complexity_profile():
    """Create high complexity feature profile."""
    return FeatureProfile(
        language="python",
        features_used={'classes': 5, 'decorators': 3, 'generators': 2, 'metaclasses': 1},
        complexity_score=0.8,
        patterns_detected=['factory', 'observer'],
        external_dependencies=['asyncio']
    )


class TestDirectStrategy:
    """Tests for DirectStrategy."""
    
    def test_initialization(self):
        """Test direct strategy initialization."""
        strategy = DirectStrategy()
        
        assert strategy.name == "direct"
        assert strategy.language_mapper is not None
        assert strategy.equivalence_matrix is not None
    
    def test_can_handle_simple_code(self, simple_unit, low_complexity_profile):
        """Test direct strategy can handle simple code."""
        strategy = DirectStrategy()
        
        result = strategy.can_handle(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert result is True
    
    def test_cannot_handle_high_complexity(self, complex_unit, high_complexity_profile):
        """Test direct strategy rejects high complexity."""
        strategy = DirectStrategy()
        
        result = strategy.can_handle(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert result is False
    
    def test_estimate_difficulty_low(self, simple_unit, low_complexity_profile):
        """Test difficulty estimation for simple code."""
        strategy = DirectStrategy()
        
        difficulty = strategy.estimate_difficulty(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert 0.0 <= difficulty <= 0.5
    
    def test_prepare_context(self, simple_unit, low_complexity_profile):
        """Test context preparation."""
        strategy = DirectStrategy()
        
        context = strategy.prepare_context(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert context['strategy'] == 'direct'
        assert context['complexity'] == 'low'
        assert 'instructions' in context
        assert len(context['instructions']) > 0


class TestPatternStrategy:
    """Tests for PatternStrategy."""
    
    def test_initialization(self):
        """Test pattern strategy initialization."""
        strategy = PatternStrategy()
        
        assert strategy.name == "pattern"
    
    def test_can_handle_medium_complexity(self, complex_unit, medium_complexity_profile):
        """Test pattern strategy handles medium complexity."""
        strategy = PatternStrategy()
        
        result = strategy.can_handle(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert result is True
    
    def test_cannot_handle_very_high_complexity(self, complex_unit):
        """Test pattern strategy rejects very high complexity."""
        strategy = PatternStrategy()
        
        very_high = FeatureProfile(
            language="python",
            features_used={'metaclasses': 3},
            complexity_score=0.9,
            patterns_detected=[],
            external_dependencies=[]
        )
        
        result = strategy.can_handle(
            complex_unit,
            "python",
            "java",
            very_high
        )
        
        assert result is False
    
    def test_estimate_difficulty(self, complex_unit, medium_complexity_profile):
        """Test difficulty estimation."""
        strategy = PatternStrategy()
        
        difficulty = strategy.estimate_difficulty(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert 0.3 <= difficulty <= 0.7
    
    def test_prepare_context_includes_rag(self, complex_unit, medium_complexity_profile):
        """Test context includes RAG flag."""
        strategy = PatternStrategy()
        
        context = strategy.prepare_context(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert context['strategy'] == 'pattern'
        assert context['use_rag'] is True
        assert context['complexity'] == 'medium'


class TestRefactorStrategy:
    """Tests for RefactorStrategy."""
    
    def test_initialization(self):
        """Test refactor strategy initialization."""
        strategy = RefactorStrategy()
        
        assert strategy.name == "refactor"
    
    def test_can_handle_high_complexity(self, complex_unit, high_complexity_profile):
        """Test refactor strategy handles high complexity."""
        strategy = RefactorStrategy()
        
        result = strategy.can_handle(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert result is True
    
    def test_cannot_handle_low_complexity(self, simple_unit, low_complexity_profile):
        """Test refactor strategy rejects low complexity."""
        strategy = RefactorStrategy()
        
        result = strategy.can_handle(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert result is False
    
    def test_estimate_difficulty_high(self, complex_unit, high_complexity_profile):
        """Test difficulty estimation for complex code."""
        strategy = RefactorStrategy()
        
        difficulty = strategy.estimate_difficulty(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert 0.6 <= difficulty <= 1.0
    
    def test_prepare_context_includes_restructuring(self, complex_unit, high_complexity_profile):
        """Test context includes restructuring flag."""
        strategy = RefactorStrategy()
        
        context = strategy.prepare_context(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert context['strategy'] == 'refactor'
        assert context['allow_restructuring'] is True
        assert context['complexity'] == 'high'


class TestHybridStrategy:
    """Tests for HybridStrategy."""
    
    def test_initialization(self):
        """Test hybrid strategy initialization."""
        strategy = HybridStrategy()
        
        assert strategy.name == "hybrid"
        assert strategy.direct is not None
        assert strategy.pattern is not None
        assert strategy.refactor is not None
    
    def test_can_handle_any(self, simple_unit, complex_unit):
        """Test hybrid strategy handles any code."""
        strategy = HybridStrategy()
        
        # Should handle simple
        result1 = strategy.can_handle(simple_unit, "python", "java")
        assert result1 is True
        
        # Should handle complex
        result2 = strategy.can_handle(complex_unit, "python", "java")
        assert result2 is True
    
    def test_selects_direct_for_low_complexity(self, simple_unit, low_complexity_profile):
        """Test hybrid selects direct for low complexity."""
        strategy = HybridStrategy()
        
        selected = strategy._select_primary_strategy(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert selected.name == "direct"
    
    def test_selects_pattern_for_medium_complexity(self, complex_unit, medium_complexity_profile):
        """Test hybrid selects pattern for medium complexity."""
        strategy = HybridStrategy()
        
        selected = strategy._select_primary_strategy(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert selected.name == "pattern"
    
    def test_selects_refactor_for_high_complexity(self, complex_unit, high_complexity_profile):
        """Test hybrid selects refactor for high complexity."""
        strategy = HybridStrategy()
        
        selected = strategy._select_primary_strategy(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert selected.name == "refactor"
    
    def test_prepare_context_combines_strategies(self, complex_unit, medium_complexity_profile):
        """Test hybrid context combines guidance."""
        strategy = HybridStrategy()
        
        context = strategy.prepare_context(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert context['strategy'] == 'hybrid'
        assert 'primary_strategy' in context
        assert 'additional_guidance' in context


class TestStrategySelector:
    """Tests for StrategySelector."""
    
    def test_initialization(self):
        """Test selector initialization."""
        selector = StrategySelector()
        
        assert len(selector.strategies) == 4
        assert 'direct' in selector.strategies
        assert 'pattern' in selector.strategies
        assert 'refactor' in selector.strategies
        assert 'hybrid' in selector.strategies
    
    def test_select_direct_for_simple(self, simple_unit, low_complexity_profile):
        """Test selector chooses direct for simple code."""
        selector = StrategySelector()
        
        strategy = selector.select_strategy(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert strategy.name in ['direct', 'pattern', 'hybrid']
    
    def test_select_refactor_for_complex(self, complex_unit, high_complexity_profile):
        """Test selector chooses refactor for complex code."""
        selector = StrategySelector()
        
        strategy = selector.select_strategy(
            complex_unit,
            "python",
            "java",
            high_complexity_profile
        )
        
        assert strategy.name in ['refactor', 'hybrid']
    
    def test_prefer_strategy(self, simple_unit, low_complexity_profile):
        """Test preferred strategy is used if valid."""
        selector = StrategySelector()
        
        strategy = selector.select_strategy(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile,
            prefer_strategy='pattern'
        )
        
        # Should use pattern if it can handle
        assert strategy.name == 'pattern'
    
    def test_recommend_strategy(self, complex_unit, medium_complexity_profile):
        """Test strategy recommendation."""
        selector = StrategySelector()
        
        recommendation = selector.recommend_strategy(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert 'recommended' in recommendation
        assert 'alternatives' in recommendation
        assert 'reasoning' in recommendation
        assert 'confidence' in recommendation
        assert 'scores' in recommendation
        assert 0.0 <= recommendation['confidence'] <= 1.0
    
    def test_get_strategy_comparison(self, complex_unit, medium_complexity_profile):
        """Test strategy comparison."""
        selector = StrategySelector()
        
        comparisons = selector.get_strategy_comparison(
            complex_unit,
            "python",
            "java",
            medium_complexity_profile
        )
        
        assert len(comparisons) == 4
        
        for comp in comparisons:
            assert 'strategy' in comp
            assert 'score' in comp
            assert 'difficulty' in comp
            assert 'can_handle' in comp
            assert 'recommendation' in comp
    
    def test_score_strategies(self, simple_unit, low_complexity_profile):
        """Test scoring all strategies."""
        selector = StrategySelector()
        
        scores = selector._score_strategies(
            simple_unit,
            "python",
            "javascript",
            low_complexity_profile
        )
        
        assert len(scores) == 4
        
        for score in scores.values():
            assert 0.0 <= score <= 1.0


class TestStrategyBase:
    """Tests for base strategy functionality."""
    
    def test_get_applicable_features(self):
        """Test getting applicable features."""
        strategy = DirectStrategy()
        
        features = strategy.get_applicable_features(
            "python",
            "java",
            ["classes", "functions"]
        )
        
        # Should return some mappings
        assert isinstance(features, list)
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        strategy = DirectStrategy()
        
        # Low difficulty, good mappings
        confidence1 = strategy.calculate_confidence(
            difficulty=0.2,
            feature_mappings=[
                {'difficulty': 'easy'},
                {'difficulty': 'easy'}
            ]
        )
        
        assert 0.7 <= confidence1 <= 1.0
        
        # High difficulty, hard mappings
        confidence2 = strategy.calculate_confidence(
            difficulty=0.8,
            feature_mappings=[
                {'difficulty': 'hard'},
                {'difficulty': 'very_hard'}
            ]
        )
        
        assert 0.0 <= confidence2 <= 0.5