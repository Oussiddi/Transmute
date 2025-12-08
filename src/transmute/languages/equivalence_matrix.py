"""
Feature equivalence matrix for cross-language mapping.

Defines how features map between different programming languages.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class TranslationDifficulty(Enum):
    """Difficulty levels for feature translation."""
    TRIVIAL = "trivial"         # Direct 1:1 mapping
    EASY = "easy"               # Simple transformation
    MODERATE = "moderate"       # Requires pattern change
    HARD = "hard"               # Significant restructuring
    VERY_HARD = "very_hard"     # May require architecture change
    IMPOSSIBLE = "impossible"   # No direct equivalent


@dataclass
class FeatureMapping:
    """
    Represents how a feature maps from source to target language.
    """
    source_feature: str
    target_feature: str
    difficulty: TranslationDifficulty
    notes: str = ""
    example_source: str = ""
    example_target: str = ""
    alternatives: List[str] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class EquivalenceMatrix:
    """
    Matrix of feature equivalences between languages.
    
    Provides mappings and translation guidance for all supported features.
    """
    
    def __init__(self):
        """Initialize equivalence matrix."""
        self.mappings: Dict[tuple, FeatureMapping] = {}
        
        # Initialize with common mappings
        self._initialize_python_java()
        self._initialize_python_javascript()
        self._initialize_javascript_java()
        
        logger.debug("EquivalenceMatrix initialized")
    
    def add_mapping(
        self,
        source_lang: str,
        target_lang: str,
        mapping: FeatureMapping
    ) -> None:
        """
        Add a feature mapping.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            mapping: Feature mapping
        """
        key = (source_lang, target_lang, mapping.source_feature)
        self.mappings[key] = mapping
    
    def get_mapping(
        self,
        source_lang: str,
        target_lang: str,
        feature: str
    ) -> Optional[FeatureMapping]:
        """
        Get feature mapping between languages.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            feature: Feature name
            
        Returns:
            FeatureMapping if exists, None otherwise
            
        Example:
            >>> mapping = matrix.get_mapping("python", "java", "list_comprehensions")
            >>> print(mapping.difficulty)
        """
        key = (source_lang, target_lang, feature)
        return self.mappings.get(key)
    
    def get_all_mappings(
        self,
        source_lang: str,
        target_lang: str
    ) -> List[FeatureMapping]:
        """
        Get all mappings between two languages.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            List of all mappings
        """
        return [
            mapping for (src, tgt, _), mapping in self.mappings.items()
            if src == source_lang and tgt == target_lang
        ]
    
    def calculate_translation_difficulty(
        self,
        source_lang: str,
        target_lang: str,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate overall translation difficulty for a set of features.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            features: List of features in source code
            
        Returns:
            Difficulty analysis
            
        Example:
            >>> analysis = matrix.calculate_translation_difficulty(
            ...     "python", "java", ["comprehensions", "decorators"]
            ... )
        """
        difficulty_scores = {
            TranslationDifficulty.TRIVIAL: 1,
            TranslationDifficulty.EASY: 2,
            TranslationDifficulty.MODERATE: 3,
            TranslationDifficulty.HARD: 4,
            TranslationDifficulty.VERY_HARD: 5,
            TranslationDifficulty.IMPOSSIBLE: 10
        }
        
        feature_difficulties = []
        unsupported = []
        
        for feature in features:
            mapping = self.get_mapping(source_lang, target_lang, feature)
            
            if mapping:
                feature_difficulties.append({
                    'feature': feature,
                    'difficulty': mapping.difficulty.value,
                    'score': difficulty_scores[mapping.difficulty],
                    'notes': mapping.notes
                })
            else:
                unsupported.append(feature)
        
        if feature_difficulties:
            avg_score = sum(f['score'] for f in feature_difficulties) / len(feature_difficulties)
        else:
            avg_score = 0
        
        return {
            'average_difficulty': avg_score,
            'features': feature_difficulties,
            'unsupported_features': unsupported,
            'is_feasible': avg_score < 7 and len(unsupported) == 0
        }
    
    def _initialize_python_java(self):
        """Initialize Python -> Java mappings."""
        lang_pair = ("python", "java")
        
        mappings = [
            FeatureMapping(
                source_feature="classes",
                target_feature="classes",
                difficulty=TranslationDifficulty.EASY,
                notes="Python classes map well to Java classes. Need to add access modifiers.",
                example_source="class MyClass:\n    pass",
                example_target="public class MyClass {\n}"
            ),
            FeatureMapping(
                source_feature="functions",
                target_feature="methods",
                difficulty=TranslationDifficulty.EASY,
                notes="Functions become static methods or need wrapper class.",
                example_source="def hello():\n    pass",
                example_target="public static void hello() {}"
            ),
            FeatureMapping(
                source_feature="list_comprehensions",
                target_feature="streams",
                difficulty=TranslationDifficulty.MODERATE,
                notes="List comprehensions translate to Java Streams API.",
                example_source="[x*2 for x in items]",
                example_target="items.stream().map(x -> x*2).collect(Collectors.toList())"
            ),
            FeatureMapping(
                source_feature="decorators",
                target_feature="annotations",
                difficulty=TranslationDifficulty.HARD,
                notes="Decorators have no direct equivalent. Use annotations or wrapper patterns.",
                example_source="@decorator\ndef func(): pass",
                example_target="@CustomAnnotation\npublic void func() {}"
            ),
            FeatureMapping(
                source_feature="generators",
                target_feature="iterators",
                difficulty=TranslationDifficulty.HARD,
                notes="Generators need manual Iterator implementation.",
                example_source="yield x",
                example_target="implements Iterator<T>"
            ),
            FeatureMapping(
                source_feature="dynamic_typing",
                target_feature="static_typing",
                difficulty=TranslationDifficulty.HARD,
                notes="Need to infer types or use Object/generics.",
                example_source="x = 5\nx = 'hello'",
                example_target="Object x = 5;\nx = \"hello\";"
            ),
            FeatureMapping(
                source_feature="multiple_inheritance",
                target_feature="interfaces",
                difficulty=TranslationDifficulty.MODERATE,
                notes="Use interfaces for multiple inheritance.",
                example_source="class C(A, B): pass",
                example_target="class C extends A implements B {}"
            ),
            FeatureMapping(
                source_feature="async",
                target_feature="completablefuture",
                difficulty=TranslationDifficulty.MODERATE,
                notes="async/await maps to CompletableFuture.",
                example_source="async def fetch(): pass",
                example_target="CompletableFuture<Void> fetch() {}"
            ),
            FeatureMapping(
                source_feature="exceptions",
                target_feature="exceptions",
                difficulty=TranslationDifficulty.EASY,
                notes="Exception handling is similar.",
                example_source="try: pass\nexcept Exception: pass",
                example_target="try {} catch (Exception e) {}"
            ),
            FeatureMapping(
                source_feature="with_statement",
                target_feature="try_with_resources",
                difficulty=TranslationDifficulty.EASY,
                notes="Python 'with' maps to try-with-resources.",
                example_source="with open(f) as file:",
                example_target="try (FileReader file = new FileReader(f)) {}"
            ),
        ]
        
        for mapping in mappings:
            self.add_mapping(lang_pair[0], lang_pair[1], mapping)
    
    def _initialize_python_javascript(self):
        """Initialize Python -> JavaScript mappings."""
        lang_pair = ("python", "javascript")
        
        mappings = [
            FeatureMapping(
                source_feature="classes",
                target_feature="classes",
                difficulty=TranslationDifficulty.TRIVIAL,
                notes="ES6 classes are very similar to Python.",
                example_source="class MyClass:\n    pass",
                example_target="class MyClass {}"
            ),
            FeatureMapping(
                source_feature="list_comprehensions",
                target_feature="array_methods",
                difficulty=TranslationDifficulty.EASY,
                notes="Use map/filter/reduce.",
                example_source="[x*2 for x in items]",
                example_target="items.map(x => x*2)"
            ),
            FeatureMapping(
                source_feature="decorators",
                target_feature="higher_order_functions",
                difficulty=TranslationDifficulty.MODERATE,
                notes="Use function wrappers or decorator pattern.",
                example_source="@decorator\ndef func(): pass",
                example_target="const func = decorator(function() {})"
            ),
            FeatureMapping(
                source_feature="async",
                target_feature="async",
                difficulty=TranslationDifficulty.TRIVIAL,
                notes="async/await works the same way.",
                example_source="async def fetch(): pass",
                example_target="async function fetch() {}"
            ),
            FeatureMapping(
                source_feature="generators",
                target_feature="generators",
                difficulty=TranslationDifficulty.EASY,
                notes="JavaScript has generators with yield.",
                example_source="def gen():\n    yield x",
                example_target="function* gen() {\n    yield x;\n}"
            ),
        ]
        
        for mapping in mappings:
            self.add_mapping(lang_pair[0], lang_pair[1], mapping)
    
    def _initialize_javascript_java(self):
        """Initialize JavaScript -> Java mappings."""
        lang_pair = ("javascript", "java")
        
        mappings = [
            FeatureMapping(
                source_feature="arrow_functions",
                target_feature="lambdas",
                difficulty=TranslationDifficulty.EASY,
                notes="Arrow functions map to lambda expressions.",
                example_source="const add = (a, b) => a + b",
                example_target="BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b"
            ),
            FeatureMapping(
                source_feature="promises",
                target_feature="completablefuture",
                difficulty=TranslationDifficulty.MODERATE,
                notes="Promises map to CompletableFuture.",
                example_source="promise.then(x => x)",
                example_target="future.thenApply(x -> x)"
            ),
            FeatureMapping(
                source_feature="dynamic_typing",
                target_feature="static_typing",
                difficulty=TranslationDifficulty.VERY_HARD,
                notes="Need type inference or Object types.",
                example_source="let x = 5",
                example_target="Integer x = 5"
            ),
        ]
        
        for mapping in mappings:
            self.add_mapping(lang_pair[0], lang_pair[1], mapping)
    
    def get_supported_language_pairs(self) -> List[tuple]:
        """
        Get all supported language pairs.
        
        Returns:
            List of (source, target) tuples
        """
        pairs = set()
        
        for (src, tgt, _) in self.mappings.keys():
            pairs.add((src, tgt))
        
        return sorted(list(pairs))
    
    def export_matrix(self) -> Dict[str, Any]:
        """
        Export equivalence matrix to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = {}
        
        for (src, tgt, feature), mapping in self.mappings.items():
            key = f"{src}->{tgt}"
            
            if key not in result:
                result[key] = {}
            
            result[key][feature] = {
                'target_feature': mapping.target_feature,
                'difficulty': mapping.difficulty.value,
                'notes': mapping.notes,
                'example_source': mapping.example_source,
                'example_target': mapping.example_target
            }
        
        return result