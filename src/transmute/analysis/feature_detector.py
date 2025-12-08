"""
Feature detector for code analysis.

Detects features, patterns, and frameworks in source code to determine
translation complexity and strategy.
"""

from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from collections import defaultdict

from transmute.languages.registry import LanguageRegistry
from transmute.git.repository import GitRepository
from transmute.core.state import FeatureProfile, FeatureType
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureDetector:
    """
    Detects features in source code.
    
    Analyzes code to identify language features, design patterns, and frameworks
    to determine translation complexity.
    """
    
    # Complexity weights for different features
    FEATURE_COMPLEXITY = {
        'classes': 0.3,
        'interfaces': 0.4,
        'inheritance': 0.5,
        'generics': 0.6,
        'annotations': 0.4,
        'async': 0.7,
        'threads': 0.8,
        'exceptions': 0.3,
        'lambdas': 0.4,
        'decorators': 0.5,
        'reflection': 0.9,
        'metaprogramming': 0.9,
        'generators': 0.5,
        'comprehensions': 0.3,
        'context_managers': 0.4,
        'pattern_matching': 0.6,
        'streams': 0.5,
        'records': 0.3,
        'enums': 0.2,
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'python': {
            'django': ['django.', 'from django', 'models.Model'],
            'flask': ['from flask', 'Flask(', '@app.route'],
            'fastapi': ['from fastapi', 'FastAPI(', '@app.get'],
            'pytest': ['import pytest', 'def test_', '@pytest.'],
        },
        'java': {
            'spring': ['@SpringBootApplication', '@RestController', 'springframework'],
            'spring_boot': ['@SpringBootApplication', 'SpringApplication.run'],
            'hibernate': ['@Entity', '@Table', 'hibernate'],
            'junit': ['@Test', 'import org.junit'],
        },
    }
    
    def __init__(self, language_registry: LanguageRegistry):
        """
        Initialize feature detector.
        
        Args:
            language_registry: Registry with loaded language plugins
        """
        self.registry = language_registry
        logger.info("Initialized FeatureDetector")
    
    def detect_file_features(
        self,
        file_path: Path,
        language: str
    ) -> List[str]:
        """
        Detect features in a single file.
        
        Args:
            file_path: Path to source file
            language: Language name
            
        Returns:
            List of detected features
            
        Example:
            >>> detector = FeatureDetector(registry)
            >>> features = detector.detect_file_features(
            ...     Path("app.py"),
            ...     "python"
            ... )
            >>> print(features)
            ['classes', 'async', 'decorators']
        """
        plugin = self.registry.get_plugin(language)
        
        if not plugin:
            logger.warning(f"No plugin for language: {language}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            features = plugin.detect_features(code)
            
            logger.debug(f"Detected {len(features)} features in {file_path}")
            
            return features
            
        except Exception as e:
            logger.error(f"Error detecting features in {file_path}: {e}")
            return []
    
    def detect_repo_features(
        self,
        git_repo: GitRepository,
        file_map: Dict[str, List[Path]]
    ) -> Dict[str, int]:
        """
        Detect features across entire repository.
        
        Args:
            git_repo: GitRepository instance
            file_map: Map of languages to files
            
        Returns:
            Dictionary mapping features to usage counts
            
        Example:
            >>> features = detector.detect_repo_features(git_repo, file_map)
            >>> print(features)
            {'classes': 45, 'async': 12, 'decorators': 30}
        """
        logger.info("Detecting features across repository")
        
        feature_counts = defaultdict(int)
        
        for language, files in file_map.items():
            for file_path in files:
                full_path = git_repo.local_path / file_path
                
                features = self.detect_file_features(full_path, language)
                
                for feature in features:
                    feature_counts[feature] += 1
        
        logger.info(f"Detected {len(feature_counts)} unique features")
        
        return dict(feature_counts)
    
    def build_feature_profile(
        self,
        git_repo: GitRepository,
        file_map: Dict[str, List[Path]],
        primary_language: str
    ) -> FeatureProfile:
        """
        Build complete feature profile for repository.
        
        Args:
            git_repo: GitRepository instance
            file_map: Map of languages to files
            primary_language: Primary language name
            
        Returns:
            FeatureProfile object
            
        Example:
            >>> profile = detector.build_feature_profile(
            ...     git_repo, file_map, "python"
            ... )
            >>> print(profile.complexity_score)
            0.65
        """
        logger.info(f"Building feature profile for {primary_language} repository")
        
        # Detect features
        features_used = self.detect_repo_features(git_repo, file_map)
        
        # Calculate complexity
        complexity = self.calculate_complexity(features_used)
        
        # Detect patterns
        patterns = self.detect_patterns(git_repo, file_map, primary_language)
        
        # Detect frameworks
        frameworks = self.detect_frameworks(git_repo, file_map, primary_language)
        framework = frameworks[0] if frameworks else None
        
        # Get external dependencies (placeholder - would parse requirements.txt, pom.xml, etc.)
        dependencies = self._extract_dependencies(git_repo, primary_language)
        
        profile = FeatureProfile(
            language=primary_language,
            features_used=features_used,
            complexity_score=complexity,
            patterns_detected=patterns,
            external_dependencies=dependencies,
            framework_detected=framework,
        )
        
        logger.info(f"Built feature profile: complexity={complexity:.2f}, "
                   f"patterns={len(patterns)}, framework={framework}")
        
        return profile
    
    def calculate_complexity(self, features_used: Dict[str, int]) -> float:
        """
        Calculate complexity score based on features used.
        
        Args:
            features_used: Dictionary of features and counts
            
        Returns:
            Complexity score (0.0 = simple, 1.0 = complex)
            
        Example:
            >>> complexity = detector.calculate_complexity({
            ...     'classes': 10,
            ...     'async': 5,
            ...     'reflection': 2
            ... })
            >>> print(f"{complexity:.2f}")
            0.58
        """
        if not features_used:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for feature, count in features_used.items():
            weight = self.FEATURE_COMPLEXITY.get(feature, 0.5)
            
            # More usage = higher impact (with diminishing returns)
            import math
            impact = min(1.0, math.log(count + 1) / 5.0)
            
            total_score += weight * impact
            total_weight += impact
        
        complexity = total_score / total_weight if total_weight > 0 else 0.0
        
        # Normalize to 0.0-1.0
        complexity = min(1.0, max(0.0, complexity))
        
        logger.debug(f"Calculated complexity: {complexity:.2f}")
        
        return round(complexity, 2)
    
    def detect_patterns(
        self,
        git_repo: GitRepository,
        file_map: Dict[str, List[Path]],
        language: str
    ) -> List[str]:
        """
        Detect design patterns in code.
        
        Args:
            git_repo: GitRepository instance
            file_map: Map of languages to files
            language: Language name
            
        Returns:
            List of detected pattern names
            
        Example:
            >>> patterns = detector.detect_patterns(git_repo, file_map, "java")
            >>> print(patterns)
            ['Singleton', 'Factory', 'Observer']
        """
        logger.info("Detecting design patterns")
        
        patterns = []
        
        # Pattern detection heuristics
        pattern_signatures = {
            'Singleton': ['private.*constructor', 'static.*instance', 'getInstance'],
            'Factory': ['create[A-Z]', 'Factory', 'Builder'],
            'Observer': ['addListener', 'removeListener', 'notify', 'Observer'],
            'Strategy': ['Strategy', 'algorithm', 'setStrategy'],
            'Decorator': ['Decorator', 'wrap', 'component'],
            'Adapter': ['Adapter', 'adaptee', 'adapt'],
        }
        
        files = file_map.get(language, [])
        
        for file_path in files[:10]:  # Sample first 10 files
            full_path = git_repo.local_path / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern_name, signatures in pattern_signatures.items():
                    if pattern_name not in patterns:
                        for sig in signatures:
                            import re
                            if re.search(sig, content, re.IGNORECASE):
                                patterns.append(pattern_name)
                                break
                                
            except Exception:
                continue
        
        logger.info(f"Detected {len(patterns)} design patterns")
        
        return patterns
    
    def detect_frameworks(
        self,
        git_repo: GitRepository,
        file_map: Dict[str, List[Path]],
        language: str
    ) -> List[str]:
        """
        Detect frameworks used in repository.
        
        Args:
            git_repo: GitRepository instance
            file_map: Map of languages to files
            language: Language name
            
        Returns:
            List of detected framework names
            
        Example:
            >>> frameworks = detector.detect_frameworks(git_repo, file_map, "python")
            >>> print(frameworks)
            ['django', 'pytest']
        """
        logger.info(f"Detecting frameworks for {language}")
        
        frameworks = []
        
        patterns = self.FRAMEWORK_PATTERNS.get(language, {})
        files = file_map.get(language, [])
        
        # Check files for framework signatures
        for file_path in files[:20]:  # Sample first 20 files
            full_path = git_repo.local_path / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for framework, signatures in patterns.items():
                    if framework not in frameworks:
                        for sig in signatures:
                            if sig in content:
                                frameworks.append(framework)
                                break
                                
            except Exception:
                continue
        
        logger.info(f"Detected frameworks: {frameworks}")
        
        return frameworks
    
    def analyze_feature_usage(
        self,
        feature_profile: FeatureProfile
    ) -> Dict[str, Any]:
        """
        Analyze feature usage statistics.
        
        Args:
            feature_profile: FeatureProfile object
            
        Returns:
            Dictionary with usage analysis
            
        Example:
            >>> analysis = detector.analyze_feature_usage(profile)
            >>> print(analysis['most_used'])
            [('classes', 45), ('functions', 120)]
        """
        most_used = feature_profile.top_features(n=10)
        
        total_features = sum(feature_profile.features_used.values())
        
        analysis = {
            'total_feature_count': total_features,
            'unique_features': len(feature_profile.features_used),
            'most_used': most_used,
            'complexity_score': feature_profile.complexity_score,
            'has_patterns': len(feature_profile.patterns_detected) > 0,
            'has_framework': feature_profile.framework_detected is not None,
        }
        
        logger.debug(f"Analyzed feature usage: {analysis['unique_features']} unique features")
        
        return analysis
    
    def get_feature_dependencies(
        self,
        feature: str,
        language: str
    ) -> List[str]:
        """
        Get features that typically depend on a given feature.
        
        Args:
            feature: Feature name
            language: Language name
            
        Returns:
            List of dependent features
            
        Example:
            >>> deps = detector.get_feature_dependencies('async', 'python')
            >>> print(deps)
            ['generators', 'context_managers']
        """
        # Common feature dependencies
        dependencies = {
            'async': ['generators', 'context_managers'],
            'generics': ['classes', 'interfaces'],
            'decorators': ['functions'],
            'annotations': ['classes', 'functions'],
            'streams': ['lambdas', 'generics'],
        }
        
        return dependencies.get(feature, [])
    
    def estimate_translation_difficulty(
        self,
        feature_profile: FeatureProfile,
        target_language: str
    ) -> float:
        """
        Estimate difficulty of translating to target language.
        
        Args:
            feature_profile: FeatureProfile for source code
            target_language: Target language name
            
        Returns:
            Difficulty score (0.0 = easy, 1.0 = very hard)
            
        Example:
            >>> difficulty = detector.estimate_translation_difficulty(
            ...     profile, "javascript"
            ... )
            >>> print(f"{difficulty:.2f}")
            0.45
        """
        target_plugin = self.registry.get_plugin(target_language)
        
        if not target_plugin:
            logger.warning(f"Unknown target language: {target_language}")
            return 0.5
        
        # Base difficulty on complexity
        difficulty = feature_profile.complexity_score
        
        # Increase difficulty for features not supported in target
        unsupported_features = 0
        
        for feature in feature_profile.features_used.keys():
            if not target_plugin.supports_feature(feature):
                unsupported_features += 1
        
        if feature_profile.features_used:
            unsupported_ratio = unsupported_features / len(feature_profile.features_used)
            difficulty += unsupported_ratio * 0.3
        
        # Cap at 1.0
        difficulty = min(1.0, difficulty)
        
        logger.info(f"Translation difficulty to {target_language}: {difficulty:.2f}")
        
        return round(difficulty, 2)
    
    def generate_feature_report(
        self,
        feature_profile: FeatureProfile,
        analysis: Dict[str, Any]
    ) -> str:
        """
        Generate feature analysis report.
        
        Args:
            feature_profile: FeatureProfile object
            analysis: Feature usage analysis
            
        Returns:
            Formatted report string
            
        Example:
            >>> report = detector.generate_feature_report(profile, analysis)
            >>> print(report)
            Feature Analysis Report
            =======================
            ...
        """
        lines = [
            "Feature Analysis Report",
            "=" * 50,
            f"Language: {feature_profile.language}",
            f"Complexity Score: {feature_profile.complexity_score:.2f}",
            "",
            "Features Used:",
        ]
        
        for feature, count in analysis['most_used']:
            lines.append(f"  {feature}: {count} occurrences")
        
        if feature_profile.patterns_detected:
            lines.extend([
                "",
                "Design Patterns:",
            ])
            for pattern in feature_profile.patterns_detected:
                lines.append(f"  - {pattern}")
        
        if feature_profile.framework_detected:
            lines.extend([
                "",
                f"Framework: {feature_profile.framework_detected}",
            ])
        
        if feature_profile.external_dependencies:
            lines.extend([
                "",
                f"Dependencies: {len(feature_profile.external_dependencies)} external packages",
            ])
        
        report = "\n".join(lines)
        
        logger.debug("Generated feature report")
        
        return report
    
    def compare_languages(
        self,
        source_profile: FeatureProfile,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Compare source and target language capabilities.
        
        Args:
            source_profile: FeatureProfile for source code
            target_language: Target language name
            
        Returns:
            Comparison results
            
        Example:
            >>> comparison = detector.compare_languages(profile, "javascript")
            >>> print(comparison['compatible_features'])
            ['classes', 'async', 'lambdas']
        """
        target_plugin = self.registry.get_plugin(target_language)
        
        if not target_plugin:
            return {
                'error': f'Unknown target language: {target_language}',
                'compatible_features': [],
                'incompatible_features': [],
                'compatibility_score': 0.0,
            }
        
        compatible = []
        incompatible = []
        
        for feature in source_profile.features_used.keys():
            if target_plugin.supports_feature(feature):
                compatible.append(feature)
            else:
                incompatible.append(feature)
        
        total = len(compatible) + len(incompatible)
        compatibility = len(compatible) / total if total > 0 else 0.0
        
        comparison = {
            'source_language': source_profile.language,
            'target_language': target_language,
            'compatible_features': compatible,
            'incompatible_features': incompatible,
            'compatibility_score': round(compatibility, 2),
            'translation_difficulty': self.estimate_translation_difficulty(
                source_profile, target_language
            ),
        }
        
        logger.info(f"Language comparison: {compatibility:.0%} compatible")
        
        return comparison
    
    def _extract_dependencies(
        self,
        git_repo: GitRepository,
        language: str
    ) -> List[str]:
        """Extract external dependencies from project files."""
        dependencies = []
        
        # Language-specific dependency files
        dep_files = {
            'python': ['requirements.txt', 'Pipfile', 'pyproject.toml'],
            'java': ['pom.xml', 'build.gradle'],
            'javascript': ['package.json'],
        }
        
        files_to_check = dep_files.get(language, [])
        
        for dep_file in files_to_check:
            file_path = git_repo.local_path / dep_file
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Very basic extraction (would need proper parsing)
                        if language == 'python' and dep_file == 'requirements.txt':
                            for line in content.splitlines():
                                if line and not line.startswith('#'):
                                    pkg = line.split('==')[0].split('>=')[0].strip()
                                    if pkg:
                                        dependencies.append(pkg)
                except Exception:
                    continue
        
        return dependencies[:20]  # Limit to 20 dependencies