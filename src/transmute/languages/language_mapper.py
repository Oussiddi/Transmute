"""
Language mapper for intelligent cross-language translation.

Orchestrates AST analysis, symbol tables, and equivalence mappings.
"""

from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from transmute.languages.equivalence_matrix import (
    EquivalenceMatrix,
    FeatureMapping,
    TranslationDifficulty
)
from transmute.languages.ast_analyzer import ASTAnalyzer, PythonASTAnalyzer
from transmute.languages.symbol_table import SymbolTable, SymbolKind
from transmute.languages.dependency_graph import DependencyGraph, DependencyType
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class LanguageMapper:
    """
    Intelligent cross-language mapping system.
    
    Combines:
    - AST analysis for structure
    - Symbol tables for identifiers
    - Dependency graphs for relationships
    - Equivalence matrix for mappings
    """
    
    def __init__(self):
        """Initialize language mapper."""
        self.equivalence_matrix = EquivalenceMatrix()
        self.ast_analyzers: Dict[str, ASTAnalyzer] = {
            'python': PythonASTAnalyzer()
        }
        
        logger.info("LanguageMapper initialized")
    
    def analyze_code(
        self,
        code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Deep analysis of code structure.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Comprehensive analysis
            
        Example:
            >>> analysis = mapper.analyze_code(python_code, "python")
            >>> print(analysis['features'])
        """
        result = {
            'language': language,
            'ast_available': False,
            'structure': {},
            'symbols': {},
            'metrics': {}
        }
        
        # AST analysis if available
        if language in self.ast_analyzers:
            try:
                analyzer = self.ast_analyzers[language]
                root = analyzer.parse(code)
                
                result['ast_available'] = True
                result['structure'] = analyzer.extract_structure(root)
                result['metrics'] = analyzer.get_complexity_metrics(root)
                
                logger.debug(f"AST analysis complete for {language}")
            except Exception as e:
                logger.warning(f"AST analysis failed: {e}")
        
        return result
    
    def get_translation_strategy(
        self,
        source_lang: str,
        target_lang: str,
        features: List[str]
    ) -> Dict[str, Any]:
        """
        Determine best translation strategy for features.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            features: Features used in source code
            
        Returns:
            Strategy recommendation
            
        Example:
            >>> strategy = mapper.get_translation_strategy(
            ...     "python", "java", ["comprehensions", "decorators"]
            ... )
            >>> print(strategy['approach'])
        """
        # Get difficulty analysis
        difficulty = self.equivalence_matrix.calculate_translation_difficulty(
            source_lang, target_lang, features
        )
        
        # Determine strategy based on difficulty
        avg_difficulty = difficulty['average_difficulty']
        
        if avg_difficulty <= 2:
            approach = "direct"
            description = "Direct translation with minimal changes"
        elif avg_difficulty <= 3:
            approach = "pattern"
            description = "Pattern-based translation with idiom mapping"
        elif avg_difficulty <= 5:
            approach = "refactor"
            description = "Significant refactoring needed"
        else:
            approach = "manual"
            description = "Manual intervention required"
        
        return {
            'approach': approach,
            'description': description,
            'difficulty_score': avg_difficulty,
            'is_feasible': difficulty['is_feasible'],
            'feature_analysis': difficulty['features'],
            'unsupported_features': difficulty['unsupported_features'],
            'recommendations': self._generate_recommendations(difficulty)
        }
    
    def _generate_recommendations(self, difficulty: Dict[str, Any]) -> List[str]:
        """Generate translation recommendations."""
        recommendations = []
        
        # Check for very difficult features
        hard_features = [
            f for f in difficulty['features']
            if f['score'] >= 4
        ]
        
        if hard_features:
            recommendations.append(
                f"Consider alternative approaches for: {', '.join(f['feature'] for f in hard_features)}"
            )
        
        # Check for unsupported features
        if difficulty['unsupported_features']:
            recommendations.append(
                f"No direct mapping for: {', '.join(difficulty['unsupported_features'])}"
            )
        
        # General recommendations
        if difficulty['average_difficulty'] > 3:
            recommendations.append("Consider architecture review before translation")
            recommendations.append("Plan for extensive testing")
        
        return recommendations
    
    def map_feature(
        self,
        source_lang: str,
        target_lang: str,
        feature: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed mapping for a specific feature.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            feature: Feature to map
            
        Returns:
            Mapping details with examples
            
        Example:
            >>> mapping = mapper.map_feature("python", "java", "comprehensions")
            >>> print(mapping['example_target'])
        """
        mapping = self.equivalence_matrix.get_mapping(
            source_lang, target_lang, feature
        )
        
        if not mapping:
            return None
        
        return {
            'source_feature': mapping.source_feature,
            'target_feature': mapping.target_feature,
            'difficulty': mapping.difficulty.value,
            'notes': mapping.notes,
            'example_source': mapping.example_source,
            'example_target': mapping.example_target,
            'alternatives': mapping.alternatives
        }
    
    def get_all_mappings(
        self,
        source_lang: str,
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """
        Get all available mappings between languages.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            List of all mappings
            
        Example:
            >>> mappings = mapper.get_all_mappings("python", "java")
            >>> for m in mappings:
            ...     print(f"{m['source_feature']} -> {m['target_feature']}")
        """
        mappings = self.equivalence_matrix.get_all_mappings(
            source_lang, target_lang
        )
        
        return [
            {
                'source_feature': m.source_feature,
                'target_feature': m.target_feature,
                'difficulty': m.difficulty.value,
                'notes': m.notes
            }
            for m in mappings
        ]
    
    def calculate_compatibility_score(
        self,
        source_lang: str,
        target_lang: str,
        features: List[str]
    ) -> float:
        """
        Calculate compatibility score (0.0-1.0) between languages for given features.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            features: Features to evaluate
            
        Returns:
            Compatibility score (higher is better)
            
        Example:
            >>> score = mapper.calculate_compatibility_score(
            ...     "python", "java", ["classes", "functions"]
            ... )
            >>> print(f"Compatibility: {score:.0%}")
        """
        if not features:
            return 1.0
        
        difficulty = self.equivalence_matrix.calculate_translation_difficulty(
            source_lang, target_lang, features
        )
        
        # Convert difficulty to compatibility (inverse)
        # Difficulty 1-2 = high compatibility (0.8-1.0)
        # Difficulty 3-5 = medium compatibility (0.4-0.7)
        # Difficulty 6+ = low compatibility (0.0-0.3)
        
        avg_difficulty = difficulty['average_difficulty']
        
        if avg_difficulty <= 2:
            score = 1.0 - (avg_difficulty - 1) * 0.1
        elif avg_difficulty <= 5:
            score = 0.7 - (avg_difficulty - 2) * 0.1
        else:
            score = max(0.0, 0.4 - (avg_difficulty - 5) * 0.1)
        
        # Penalize unsupported features
        unsupported_penalty = len(difficulty['unsupported_features']) * 0.1
        score = max(0.0, score - unsupported_penalty)
        
        return score
    
    def generate_migration_report(
        self,
        source_lang: str,
        target_lang: str,
        code_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable migration report.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            code_analysis: Analysis from analyze_code()
            
        Returns:
            Formatted report
            
        Example:
            >>> report = mapper.generate_migration_report("python", "java", analysis)
            >>> print(report)
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"MIGRATION REPORT: {source_lang.upper()} → {target_lang.upper()}")
        lines.append("=" * 60)
        lines.append("")
        
        # Code statistics
        if 'metrics' in code_analysis and code_analysis['metrics']:
            metrics = code_analysis['metrics']
            lines.append("CODE METRICS:")
            lines.append(f"  Functions: {metrics.get('function_count', 0)}")
            lines.append(f"  Classes: {metrics.get('class_count', 0)}")
            lines.append(f"  Complexity: {metrics.get('max_depth', 0)} levels deep")
            lines.append("")
        
        # Extract features from structure
        features = []
        if 'structure' in code_analysis:
            structure = code_analysis['structure']
            if structure.get('functions'):
                features.append('functions')
            if structure.get('classes'):
                features.append('classes')
        
        if features:
            # Get translation strategy
            strategy = self.get_translation_strategy(source_lang, target_lang, features)
            
            lines.append("TRANSLATION STRATEGY:")
            lines.append(f"  Approach: {strategy['approach'].upper()}")
            lines.append(f"  Description: {strategy['description']}")
            lines.append(f"  Difficulty Score: {strategy['difficulty_score']:.1f}/5.0")
            lines.append(f"  Feasible: {'Yes ✓' if strategy['is_feasible'] else 'No ✗'}")
            lines.append("")
            
            # Feature mappings
            if strategy['feature_analysis']:
                lines.append("FEATURE MAPPINGS:")
                for feature_info in strategy['feature_analysis']:
                    difficulty_icon = {
                        'trivial': '✓',
                        'easy': '✓',
                        'moderate': '⚠',
                        'hard': '⚠',
                        'very_hard': '✗',
                        'impossible': '✗'
                    }.get(feature_info['difficulty'], '?')
                    
                    lines.append(
                        f"  {difficulty_icon} {feature_info['feature']}: "
                        f"{feature_info['difficulty']}"
                    )
                lines.append("")
            
            # Recommendations
            if strategy['recommendations']:
                lines.append("RECOMMENDATIONS:")
                for rec in strategy['recommendations']:
                    lines.append(f"  • {rec}")
                lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_supported_language_pairs(self) -> List[tuple]:
        """
        Get all supported language pairs.
        
        Returns:
            List of (source, target) tuples
            
        Example:
            >>> pairs = mapper.get_supported_language_pairs()
            >>> for src, tgt in pairs:
            ...     print(f"{src} -> {tgt}")
        """
        return self.equivalence_matrix.get_supported_language_pairs()
    
    def add_custom_mapping(
        self,
        source_lang: str,
        target_lang: str,
        mapping: FeatureMapping
    ) -> None:
        """
        Add custom feature mapping.
        
        Args:
            source_lang: Source language
            target_lang: Target language
            mapping: Feature mapping
            
        Example:
            >>> custom = FeatureMapping(
            ...     source_feature="my_feature",
            ...     target_feature="target_feature",
            ...     difficulty=TranslationDifficulty.EASY
            ... )
            >>> mapper.add_custom_mapping("rust", "go", custom)
        """
        self.equivalence_matrix.add_mapping(source_lang, target_lang, mapping)
        logger.info(f"Added custom mapping: {source_lang} -> {target_lang}")