"""
Analysis agent for repository analysis.

Analyzes repositories to detect languages, features, and prepare for translation.
"""

from typing import Dict, Any, List  # Add List here
from pathlib import Path

from transmute.agents.base import BaseAgent
from transmute.core.state import TransmuteState
from transmute.analysis.repository_analyzer import RepositoryAnalyzer
from transmute.analysis.feature_detector import FeatureDetector
from transmute.languages.registry import LanguageRegistry
from transmute.git.repository import GitRepository


class AnalysisAgent(BaseAgent):
    """
    Analyzes repositories to extract metadata and features.
    
    This agent:
    1. Clones the repository (if URL provided)
    2. Detects languages used
    3. Analyzes code features
    4. Generates feature profiles
    5. Updates state with analysis results
    """
    
    def __init__(
        self,
        language_registry: LanguageRegistry,
        work_dir: Path = Path("/tmp/transmute")
    ):
        """
        Initialize analysis agent.
        
        Args:
            language_registry: Registry with language plugins
            work_dir: Working directory for cloning repos
        """
        super().__init__("AnalysisAgent")
        
        self.language_registry = language_registry
        self.work_dir = work_dir
        
        self.repository_analyzer = RepositoryAnalyzer(language_registry)
        self.feature_detector = FeatureDetector(language_registry)
    
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Process repository analysis.
        
        Args:
            state: Current state
            
        Returns:
            State updates with analysis results
        """
        self.log_info("Starting repository analysis")
        
        # Get repository URL from metadata or state
        repo_url = None
        if state.repository and state.repository.url:
            repo_url = state.repository.url
        elif state.metadata.get('repository_url'):
            repo_url = state.metadata['repository_url']
        
        if not repo_url:
            self.log_error("No repository URL provided")
            return {
                "errors": state.errors + ["No repository URL provided"],
                "current_step": "error"
            }
        
        try:
            # Analyze repository
            self.log_info(f"Analyzing repository: {repo_url}")
            
            analysis_results = self.repository_analyzer.analyze_repository(
                url=repo_url,
                target_dir=self.work_dir
            )
            
            # Build feature profile
            self.log_info("Building feature profile")
            
            feature_profile = self.feature_detector.build_feature_profile(
                git_repo=GitRepository(repo_url, analysis_results['clone_path']),
                file_map=analysis_results['file_map'],
                primary_language=analysis_results['primary_language']
            )
            
            # Generate reports
            repo_report = analysis_results['report']
            
            analysis = self.feature_detector.analyze_feature_usage(feature_profile)
            feature_report = self.feature_detector.generate_feature_report(
                feature_profile, analysis
            )
            
            self.log_info(f"Analysis complete: {analysis_results['primary_language']} repository")
            
            # Update state
            return {
                "repository": analysis_results['metadata'],
                "source_language": analysis_results['languages'][0] if analysis_results['languages'] else None,
                "feature_profile": feature_profile,
                "metadata": {
                    **state.metadata,
                    "clone_path": str(analysis_results['clone_path']),
                    "file_map": {k: [str(p) for p in v] for k, v in analysis_results['file_map'].items()},
                    "analysis_report": repo_report,
                    "feature_report": feature_report,
                },
                "current_step": "planning",
            }
            
        except Exception as e:
            self.log_error(f"Analysis failed: {e}")
            raise
    def get_file_statistics(self, file_map: Dict[str, List]) -> Dict[str, Any]:
        """
        Get detailed file statistics.
        
        Args:
            file_map: Map of languages to files
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_files': sum(len(files) for files in file_map.values()),
            'languages': {},
        }
        
        for lang, files in file_map.items():
            stats['languages'][lang] = {
                'file_count': len(files),
                'extensions': list(set(Path(f).suffix for f in files))
            }
        
        return stats
    
    def estimate_analysis_time(self, file_count: int) -> float:
        """
        Estimate analysis time in seconds.
        
        Args:
            file_count: Number of files
            
        Returns:
            Estimated seconds
        """
        # Rough estimate: 0.1 seconds per file
        return file_count * 0.1
    
    def validate_repository(self, repo_url: str) -> bool:
        """
        Validate repository URL before analysis.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            True if valid
        """
        if not repo_url:
            return False
        
        # Basic URL validation
        valid_prefixes = ['http://', 'https://', 'git@']
        return any(repo_url.startswith(prefix) for prefix in valid_prefixes)