"""
Git repository operations.

Handles cloning repositories, extracting metadata, and analyzing code structure.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re
import shutil

from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError

from transmute.core.state import RepositoryMetadata
from transmute.utils.logger import get_logger
from transmute.utils.paths import ensure_dir

logger = get_logger(__name__)


def detect_platform(url: str) -> str:
    """
    Detect Git platform from URL.
    
    Args:
        url: Repository URL
        
    Returns:
        Platform name ('github', 'gitlab', 'bitbucket', or 'unknown')
        
    Example:
        >>> detect_platform("https://github.com/user/repo")
        'github'
        >>> detect_platform("https://gitlab.com/user/project")
        'gitlab'
    """
    url_lower = url.lower()
    
    if 'github.com' in url_lower:
        return 'github'
    elif 'gitlab.com' in url_lower:
        return 'gitlab'
    elif 'bitbucket.org' in url_lower:
        return 'bitbucket'
    else:
        logger.warning(f"Unknown Git platform for URL: {url}")
        return 'unknown'


class GitRepository:
    """
    Git repository handler.
    
    Manages cloning, metadata extraction, and file analysis for Git repositories.
    """
    
    def __init__(self, url: str, local_path: Optional[Path] = None):
        """
        Initialize repository handler.
        
        Args:
            url: Repository URL (HTTPS or SSH)
            local_path: Local path to clone/open repo (optional)
        """
        self.url = url
        self.platform = detect_platform(url)
        self.local_path = local_path
        self.repo: Optional[Repo] = None
        
        logger.info(f"Initialized GitRepository: {url}")
    
    def clone(
        self,
        target_dir: Path,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Path:
        """
        Clone repository to local directory.
        
        Args:
            target_dir: Directory to clone into
            branch: Specific branch to clone (optional)
            depth: Shallow clone depth (optional)
            
        Returns:
            Path to cloned repository
            
        Raises:
            GitCommandError: If clone fails
            
        Example:
            >>> repo = GitRepository("https://github.com/user/repo")
            >>> path = repo.clone(Path("/tmp/repos"))
            >>> print(path)
            /tmp/repos/repo
        """
        # Ensure target directory exists
        ensure_dir(target_dir)
        
        # Extract repo name from URL
        repo_name = self._extract_repo_name(self.url)
        clone_path = target_dir / repo_name
        
        # Remove if already exists
        if clone_path.exists():
            logger.warning(f"Directory exists, removing: {clone_path}")
            shutil.rmtree(clone_path)
        
        logger.info(f"Cloning {self.url} to {clone_path}")
        
        try:
            # Build clone options
            clone_kwargs = {}
            if branch:
                clone_kwargs['branch'] = branch
            if depth:
                clone_kwargs['depth'] = depth
            
            # Clone repository
            self.repo = Repo.clone_from(
                self.url,
                clone_path,
                **clone_kwargs
            )
            
            self.local_path = clone_path
            
            logger.info(f"Successfully cloned repository to {clone_path}")
            return clone_path
            
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def open(self, repo_path: Path) -> None:
        """
        Open existing local repository.
        
        Args:
            repo_path: Path to local repository
            
        Raises:
            InvalidGitRepositoryError: If path is not a valid Git repository
        """
        logger.info(f"Opening repository at {repo_path}")
        
        try:
            self.repo = Repo(repo_path)
            self.local_path = repo_path
            logger.info(f"Successfully opened repository")
            
        except InvalidGitRepositoryError as e:
            logger.error(f"Not a valid Git repository: {repo_path}")
            raise
    
    def get_metadata(self) -> RepositoryMetadata:
        """
        Extract repository metadata.
        
        Returns:
            RepositoryMetadata object
            
        Raises:
            ValueError: If repository not cloned/opened
            
        Example:
            >>> repo = GitRepository("https://github.com/user/repo")
            >>> repo.clone(Path("/tmp/repos"))
            >>> metadata = repo.get_metadata()
            >>> print(metadata.total_commits)
            150
        """
        if not self.repo or not self.local_path:
            raise ValueError("Repository not cloned or opened")
        
        logger.info("Extracting repository metadata")
        
        # Get default branch
        try:
            default_branch = self.repo.active_branch.name
        except Exception:
            default_branch = "main"
        
        # Count commits
        try:
            total_commits = len(list(self.repo.iter_commits()))
        except Exception:
            total_commits = 0
        
        # Count files
        file_tree = self.get_file_tree()
        total_files = len(file_tree)
        
        # Calculate total lines and size
        total_lines = 0
        total_size = 0
        
        for file_path in file_tree:
            try:
                full_path = self.local_path / file_path
                if full_path.is_file():
                    total_size += full_path.stat().st_size
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += sum(1 for _ in f)
            except Exception:
                continue
        
        size_mb = total_size / (1024 * 1024)
        
        metadata = RepositoryMetadata(
            url=self.url,
            platform=self.platform,
            local_path=self.local_path,
            default_branch=default_branch,
            total_commits=total_commits,
            total_files=total_files,
            total_lines=total_lines,
            size_mb=round(size_mb, 2)
        )
        
        logger.info(f"Extracted metadata: {total_commits} commits, "
                   f"{total_files} files, {total_lines} lines")
        
        return metadata
    
    def get_file_tree(
        self,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Get list of files in repository.
        
        Args:
            extensions: Filter by extensions (e.g., ['.py', '.java'])
            exclude_dirs: Directories to exclude (e.g., ['node_modules', '.git'])
            
        Returns:
            List of file paths relative to repository root
            
        Example:
            >>> repo = GitRepository("https://github.com/user/repo")
            >>> repo.open(Path("/tmp/repos/repo"))
            >>> files = repo.get_file_tree(extensions=['.py'])
            >>> print(files)
            [Path('main.py'), Path('src/utils.py')]
        """
        if not self.local_path:
            raise ValueError("Repository not cloned or opened")
        
        # Default exclusions
        if exclude_dirs is None:
            exclude_dirs = [
                '.git', '__pycache__', 'node_modules', '.venv',
                'venv', '.idea', '.vscode', 'target', 'build',
                'dist', '.pytest_cache', '.mypy_cache'
            ]
        
        files = []
        
        for item in self.local_path.rglob('*'):
            # Skip if in excluded directory
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue
            
            # Skip if not a file
            if not item.is_file():
                continue
            
            # Filter by extension if specified
            if extensions and item.suffix not in extensions:
                continue
            
            # Get relative path
            rel_path = item.relative_to(self.local_path)
            files.append(rel_path)
        
        logger.debug(f"Found {len(files)} files in repository")
        
        return files
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get repository statistics.
        
        Returns:
            Dictionary with statistics
            
        Example:
            >>> stats = repo.get_stats()
            >>> print(stats['language_distribution'])
            {'python': 80.5, 'yaml': 19.5}
        """
        if not self.local_path:
            raise ValueError("Repository not cloned or opened")
        
        logger.info("Calculating repository statistics")
        
        # Count files by extension
        extension_counts = {}
        extension_lines = {}
        
        for file_path in self.get_file_tree():
            ext = file_path.suffix or 'no_extension'
            
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
            
            # Count lines
            try:
                full_path = self.local_path / file_path
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                    extension_lines[ext] = extension_lines.get(ext, 0) + lines
            except Exception:
                continue
        
        # Calculate percentages
        total_lines = sum(extension_lines.values())
        language_distribution = {}
        
        # Map common extensions to languages
        ext_to_lang = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
        }
        
        for ext, lines in extension_lines.items():
            lang = ext_to_lang.get(ext, ext)
            percentage = (lines / total_lines * 100) if total_lines > 0 else 0
            if percentage > 0.1:  # Only include if > 0.1%
                language_distribution[lang] = round(percentage, 2)
        
        stats = {
            'extension_counts': extension_counts,
            'extension_lines': extension_lines,
            'language_distribution': language_distribution,
            'total_lines': total_lines,
        }
        
        logger.info(f"Calculated stats: {len(extension_counts)} file types")
        
        return stats
    
    def _extract_repo_name(self, url: str) -> str:
        """
        Extract repository name from URL.
        
        Args:
            url: Repository URL
            
        Returns:
            Repository name
        """
        # Remove .git suffix if present
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract last part of URL
        parts = url.split('/')
        return parts[-1] if parts else 'repo'
    
    def cleanup(self) -> None:
        """
        Clean up cloned repository.
        
        Removes the local repository directory.
        """
        if self.local_path and self.local_path.exists():
            logger.info(f"Cleaning up repository: {self.local_path}")
            shutil.rmtree(self.local_path)
            self.local_path = None
            self.repo = None
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<GitRepository: {self.url} @ {self.local_path}>"