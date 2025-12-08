"""
Tests for Git operations.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from transmute.git.repository import GitRepository, detect_platform
from transmute.core.state import RepositoryMetadata


class TestDetectPlatform:
    """Tests for detect_platform function."""
    
    def test_detect_github(self):
        """Test detecting GitHub URLs."""
        assert detect_platform("https://github.com/user/repo") == "github"
        assert detect_platform("git@github.com:user/repo.git") == "github"
        assert detect_platform("https://GITHUB.COM/user/repo") == "github"
    
    def test_detect_gitlab(self):
        """Test detecting GitLab URLs."""
        assert detect_platform("https://gitlab.com/user/project") == "gitlab"
        assert detect_platform("git@gitlab.com:user/project.git") == "gitlab"
    
    def test_detect_bitbucket(self):
        """Test detecting Bitbucket URLs."""
        assert detect_platform("https://bitbucket.org/user/repo") == "bitbucket"
    
    def test_detect_unknown(self):
        """Test detecting unknown platforms."""
        assert detect_platform("https://example.com/repo.git") == "unknown"


class TestGitRepository:
    """Tests for GitRepository class."""
    
    def test_repository_initialization(self):
        """Test repository initialization."""
        repo = GitRepository("https://github.com/user/repo")
        
        assert repo.url == "https://github.com/user/repo"
        assert repo.platform == "github"
        assert repo.local_path is None
        assert repo.repo is None
    
    def test_repository_with_local_path(self):
        """Test repository with local path."""
        local_path = Path("/tmp/test_repo")
        repo = GitRepository(
            "https://github.com/user/repo",
            local_path=local_path
        )
        
        assert repo.local_path == local_path
    
    def test_extract_repo_name(self):
        """Test extracting repo name from URL."""
        repo = GitRepository("https://github.com/user/my-repo.git")
        
        name = repo._extract_repo_name(repo.url)
        assert name == "my-repo"
    
    def test_extract_repo_name_no_git_suffix(self):
        """Test extracting repo name without .git suffix."""
        repo = GitRepository("https://github.com/user/my-repo")
        
        name = repo._extract_repo_name(repo.url)
        assert name == "my-repo"
    
    def test_get_metadata_without_clone_raises_error(self):
        """Test that get_metadata raises error if not cloned."""
        repo = GitRepository("https://github.com/user/repo")
        
        with pytest.raises(ValueError, match="not cloned or opened"):
            repo.get_metadata()
    
    def test_get_file_tree_without_clone_raises_error(self):
        """Test that get_file_tree raises error if not cloned."""
        repo = GitRepository("https://github.com/user/repo")
        
        with pytest.raises(ValueError, match="not cloned or opened"):
            repo.get_file_tree()
    
    def test_repository_repr(self):
        """Test repository string representation."""
        repo = GitRepository("https://github.com/user/repo")
        
        repr_str = repr(repo)
        assert "GitRepository" in repr_str
        assert "github.com/user/repo" in repr_str


# Integration tests (commented out by default - uncomment to test with real repos)
"""
class TestGitRepositoryIntegration:
    '''Integration tests with actual Git repositories.'''
    
    def test_clone_small_public_repo(self):
        '''Test cloning a small public repository.'''
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            # Use a small, stable public repo
            repo = GitRepository("https://github.com/octocat/Hello-World")
            clone_path = repo.clone(target_dir, depth=1)
            
            assert clone_path.exists()
            assert (clone_path / ".git").exists()
            
            # Clean up
            repo.cleanup()
            assert not clone_path.exists()
    
    def test_get_metadata_from_cloned_repo(self):
        '''Test extracting metadata from cloned repo.'''
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            repo = GitRepository("https://github.com/octocat/Hello-World")
            repo.clone(target_dir, depth=1)
            
            metadata = repo.get_metadata()
            
            assert isinstance(metadata, RepositoryMetadata)
            assert metadata.platform == "github"
            assert metadata.total_files > 0
            
            repo.cleanup()
    
    def test_get_file_tree(self):
        '''Test getting file tree from repo.'''
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            repo = GitRepository("https://github.com/octocat/Hello-World")
            repo.clone(target_dir, depth=1)
            
            files = repo.get_file_tree()
            
            assert len(files) > 0
            assert all(isinstance(f, Path) for f in files)
            
            repo.cleanup()
    
    def test_get_stats(self):
        '''Test getting repository stats.'''
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            
            repo = GitRepository("https://github.com/octocat/Hello-World")
            repo.clone(target_dir, depth=1)
            
            stats = repo.get_stats()
            
            assert 'extension_counts' in stats
            assert 'language_distribution' in stats
            assert stats['total_lines'] > 0
            
            repo.cleanup()
"""