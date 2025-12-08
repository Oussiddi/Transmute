"""
Repository analyzer for Transmute.

Analyzes Git repositories to detect languages, features, and prepare for translation.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

from transmute.git.repository import GitRepository
from transmute.languages.registry import LanguageRegistry
from transmute.core.state import RepositoryMetadata, LanguageInfo
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryAnalyzer:
    """
    Analyzes repositories for language detection and metrics.
    
    Combines Git operations with language plugins to provide comprehensive
    repository analysis.
    """
    
    def __init__(self, language_registry: LanguageRegistry):
        """
        Initialize repository analyzer.
        
        Args:
            language_registry: Registry with loaded language plugins
        """
        self.registry = language_registry
        logger.info("Initialized RepositoryAnalyzer")
    
    def analyze_repository(
        self,
        url: str,
        target_dir: Path,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform full repository analysis.
        
        Clones repository, detects languages, analyzes files, and generates report.
        
        Args:
            url: Repository URL
            target_dir: Directory to clone into
            branch: Specific branch to analyze (optional)
            
        Returns:
            Analysis results dictionary
            
        Example:
            >>> analyzer = RepositoryAnalyzer(registry)
            >>> results = analyzer.analyze_repository(
            ...     "https://github.com/user/repo",
            ...     Path("/tmp/analysis")
            ... )
            >>> print(results['primary_language'])
            'python'
        """
        logger.info(f"Starting repository analysis: {url}")
        
        # Clone repository
        git_repo = GitRepository(url)
        clone_path = git_repo.clone(target_dir, branch=branch, depth=1)
        
        try:
            # Extract metadata
            metadata = git_repo.get_metadata()
            
            # Detect languages
            languages = self.detect_languages(git_repo)
            
            # Build file map
            file_map = self.build_file_map(git_repo)
            
            # Calculate metrics
            metrics = self.calculate_metrics(git_repo, file_map)
            
            # Determine primary language
            primary_language = self.get_primary_language(languages)
            
            # Generate report
            report = self.generate_report(
                metadata, languages, metrics, primary_language
            )
            
            logger.info(f"Analysis complete: {primary_language} repository")
            
            return {
                'metadata': metadata,
                'languages': languages,
                'file_map': file_map,
                'metrics': metrics,
                'primary_language': primary_language,
                'report': report,
                'clone_path': clone_path,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            git_repo.cleanup()
            raise
    
    def detect_languages(self, git_repo: GitRepository) -> List[LanguageInfo]:
        """
        Detect all languages used in repository.
        
        Args:
            git_repo: GitRepository instance
            
        Returns:
            List of LanguageInfo objects for detected languages
            
        Example:
            >>> languages = analyzer.detect_languages(git_repo)
            >>> for lang in languages:
            ...     print(f"{lang.name}: {lang.percentage}%")
            python: 85.5%
            yaml: 14.5%
        """
        logger.info("Detecting languages in repository")
        
        # Get all files
        all_files = git_repo.get_file_tree()
        
        # Count files and lines by language
        language_files = defaultdict(int)
        language_lines = defaultdict(int)
        total_lines = 0
        
        for file_path in all_files:
            # Detect language from extension
            full_path = git_repo.local_path / file_path
            language = self.registry.detect_language(full_path)
            
            if language:
                language_files[language] += 1
                
                # Count lines
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        language_lines[language] += lines
                        total_lines += lines
                except Exception:
                    continue
        
        # Build LanguageInfo objects
        languages = []
        
        for lang_name, line_count in language_lines.items():
            plugin = self.registry.get_plugin(lang_name)
            
            if plugin:
                percentage = (line_count / total_lines * 100) if total_lines > 0 else 0
                
                lang_info = LanguageInfo(
                    name=lang_name,
                    version=plugin.config.version,
                    file_count=language_files[lang_name],
                    line_count=line_count,
                    percentage=round(percentage, 2),
                    extensions=plugin.config.extensions,
                )
                
                languages.append(lang_info)
        
        # Sort by percentage (descending)
        languages.sort(key=lambda x: x.percentage, reverse=True)
        
        logger.info(f"Detected {len(languages)} languages")
        
        return languages
    
    def build_file_map(
        self,
        git_repo: GitRepository
    ) -> Dict[str, List[Path]]:
        """
        Build map of languages to files.
        
        Args:
            git_repo: GitRepository instance
            
        Returns:
            Dictionary mapping language names to file paths
            
        Example:
            >>> file_map = analyzer.build_file_map(git_repo)
            >>> print(file_map['python'])
            [Path('main.py'), Path('src/utils.py')]
        """
        logger.info("Building file-to-language map")
        
        file_map = defaultdict(list)
        all_files = git_repo.get_file_tree()
        
        for file_path in all_files:
            full_path = git_repo.local_path / file_path
            language = self.registry.detect_language(full_path)
            
            if language:
                file_map[language].append(file_path)
        
        logger.debug(f"Mapped {len(all_files)} files to {len(file_map)} languages")
        
        return dict(file_map)
    
    def calculate_metrics(
        self,
        git_repo: GitRepository,
        file_map: Dict[str, List[Path]]
    ) -> Dict[str, Any]:
        """
        Calculate repository metrics.
        
        Args:
            git_repo: GitRepository instance
            file_map: Map of languages to files
            
        Returns:
            Dictionary with metrics
            
        Example:
            >>> metrics = analyzer.calculate_metrics(git_repo, file_map)
            >>> print(metrics['total_files'])
            150
        """
        logger.info("Calculating repository metrics")
        
        stats = git_repo.get_stats()
        
        metrics = {
            'total_files': sum(len(files) for files in file_map.values()),
            'total_languages': len(file_map),
            'language_file_counts': {
                lang: len(files) for lang, files in file_map.items()
            },
            'language_distribution': stats['language_distribution'],
            'total_lines': stats['total_lines'],
            'extension_counts': stats['extension_counts'],
        }
        
        logger.info(f"Calculated metrics: {metrics['total_files']} files, "
                   f"{metrics['total_languages']} languages")
        
        return metrics
    
    def get_primary_language(
        self,
        languages: List[LanguageInfo]
    ) -> Optional[str]:
        """
        Determine primary language from detected languages.
        
        Args:
            languages: List of LanguageInfo objects
            
        Returns:
            Name of primary language or None if no languages detected
            
        Example:
            >>> primary = analyzer.get_primary_language(languages)
            >>> print(primary)
            'python'
        """
        if not languages:
            logger.warning("No languages detected")
            return None
        
        # Primary language is the one with highest percentage
        primary = languages[0]
        
        logger.info(f"Primary language: {primary.name} ({primary.percentage}%)")
        
        return primary.name
    
    def generate_report(
        self,
        metadata: RepositoryMetadata,
        languages: List[LanguageInfo],
        metrics: Dict[str, Any],
        primary_language: Optional[str]
    ) -> str:
        """
        Generate analysis report.
        
        Args:
            metadata: Repository metadata
            languages: Detected languages
            metrics: Calculated metrics
            primary_language: Primary language name
            
        Returns:
            Formatted report string
            
        Example:
            >>> report = analyzer.generate_report(metadata, languages, metrics, "python")
            >>> print(report)
            Repository Analysis Report
            ==========================
            URL: https://github.com/user/repo
            ...
        """
        lines = [
            "Repository Analysis Report",
            "=" * 50,
            f"URL: {metadata.url}",
            f"Platform: {metadata.platform}",
            f"Branch: {metadata.default_branch}",
            "",
            "Statistics:",
            f"  Total Files: {metrics['total_files']}",
            f"  Total Lines: {metrics['total_lines']:,}",
            f"  Total Commits: {metadata.total_commits}",
            f"  Size: {metadata.size_mb} MB",
            "",
            "Languages Detected:",
        ]
        
        for lang in languages:
            lines.append(
                f"  {lang.name}: {lang.percentage}% "
                f"({lang.file_count} files, {lang.line_count:,} lines)"
            )
        
        if primary_language:
            lines.extend([
                "",
                f"Primary Language: {primary_language}",
            ])
        
        report = "\n".join(lines)
        
        logger.debug("Generated analysis report")
        
        return report
    
    def cleanup(self, analysis_result: Dict[str, Any]) -> None:
        """
        Clean up analysis resources.
        
        Args:
            analysis_result: Result from analyze_repository()
        """
        clone_path = analysis_result.get('clone_path')
        
        if clone_path:
            git_repo = GitRepository(
                analysis_result['metadata'].url,
                local_path=clone_path
            )
            git_repo.cleanup()
            logger.info("Cleaned up analysis resources")