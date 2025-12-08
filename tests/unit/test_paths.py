"""
Tests for path utilities.
"""

import pytest
from pathlib import Path
import tempfile
import os
import shutil
import time

from transmute.utils.paths import ensure_dir, get_temp_dir, clean_temp_dirs


class TestEnsureDir:
    """Tests for ensure_dir function."""
    
    def test_ensure_dir_creates_new_directory(self):
        """Test that ensure_dir creates a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "test_dir"
            
            # Directory doesn't exist yet
            assert not new_dir.exists()
            
            # Create it
            result = ensure_dir(new_dir)
            
            # Should exist now
            assert new_dir.exists()
            assert new_dir.is_dir()
            
            # Should return Path object
            assert isinstance(result, Path)
            assert result == new_dir
    
    def test_ensure_dir_with_existing_directory(self):
        """Test that ensure_dir works with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_dir = Path(tmpdir)
            
            # Directory already exists
            assert existing_dir.exists()
            
            # Should not raise error
            result = ensure_dir(existing_dir)
            
            # Should still exist
            assert existing_dir.exists()
            assert result == existing_dir
    
    def test_ensure_dir_creates_parent_directories(self):
        """Test that ensure_dir creates nested parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "level1" / "level2" / "level3"
            
            # None of the levels exist
            assert not (Path(tmpdir) / "level1").exists()
            
            # Create nested directory
            result = ensure_dir(nested_dir)
            
            # All levels should exist
            assert (Path(tmpdir) / "level1").exists()
            assert (Path(tmpdir) / "level1" / "level2").exists()
            assert nested_dir.exists()
            assert result == nested_dir
    
    def test_ensure_dir_with_string_path(self):
        """Test that ensure_dir accepts string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "string_path")
            
            # Pass as string
            result = ensure_dir(new_dir)
            
            # Should be converted to Path
            assert isinstance(result, Path)
            assert result.exists()
            assert str(result) == new_dir
    
    def test_ensure_dir_with_path_object(self):
        """Test that ensure_dir accepts Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "path_object"
            
            # Pass as Path
            result = ensure_dir(new_dir)
            
            # Should remain Path
            assert isinstance(result, Path)
            assert result.exists()
    
    def test_ensure_dir_raises_error_if_file_exists(self):
        """Test that ensure_dir raises error if path is a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file
            file_path = Path(tmpdir) / "test_file.txt"
            file_path.write_text("test")
            
            # Try to create directory with same name
            with pytest.raises(OSError, match="not a directory"):
                ensure_dir(file_path)
    
    def test_ensure_dir_with_relative_path(self):
        """Test that ensure_dir works with relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Use relative path
                result = ensure_dir("relative/path/test")
                
                # Should exist
                assert result.exists()
                assert result.is_dir()
                
            finally:
                # Change back to original directory
                os.chdir(original_dir)
    
    def test_ensure_dir_idempotent(self):
        """Test that calling ensure_dir multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "idempotent_test"
            
            # Create multiple times
            result1 = ensure_dir(test_dir)
            result2 = ensure_dir(test_dir)
            result3 = ensure_dir(test_dir)
            
            # All should succeed and return same path
            assert result1 == result2 == result3
            assert test_dir.exists()

class TestGetTempDir:
    """Tests for get_temp_dir function."""
    
    def test_get_temp_dir_creates_directory(self):
        """Test that get_temp_dir creates a directory."""
        temp_dir = get_temp_dir()
        
        try:
            # Should exist
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            
            # Should be a Path object
            assert isinstance(temp_dir, Path)
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_get_temp_dir_with_custom_prefix(self):
        """Test that get_temp_dir uses custom prefix."""
        prefix = "test_migration"
        temp_dir = get_temp_dir(prefix=prefix)
        
        try:
            # Directory name should contain prefix
            assert prefix in temp_dir.name
            assert temp_dir.exists()
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_get_temp_dir_default_prefix(self):
        """Test that get_temp_dir uses default prefix."""
        temp_dir = get_temp_dir()
        
        try:
            # Directory name should contain 'transmute'
            assert "transmute" in temp_dir.name
            assert temp_dir.exists()
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_get_temp_dir_creates_unique_directories(self):
        """Test that get_temp_dir creates unique directories each time."""
        temp_dir1 = get_temp_dir("unique_test")
        temp_dir2 = get_temp_dir("unique_test")
        
        try:
            # Should be different directories
            assert temp_dir1 != temp_dir2
            
            # Both should exist
            assert temp_dir1.exists()
            assert temp_dir2.exists()
            
        finally:
            # Clean up
            if temp_dir1.exists():
                shutil.rmtree(temp_dir1)
            if temp_dir2.exists():
                shutil.rmtree(temp_dir2)
    
    def test_get_temp_dir_in_system_temp(self):
        """Test that get_temp_dir creates directory in system temp."""
        temp_dir = get_temp_dir()
        
        try:
            # Should be in system temp directory
            system_temp = Path(tempfile.gettempdir())
            assert temp_dir.parent == system_temp or system_temp in temp_dir.parents
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_get_temp_dir_has_timestamp(self):
        """Test that get_temp_dir includes timestamp in name."""
        temp_dir = get_temp_dir()
        
        try:
            # Should have timestamp format YYYYMMDD_HHMMSS
            # Name format: prefix_YYYYMMDD_HHMMSS_randomsuffix
            import re
            pattern = r'\d{8}_\d{6}'  # YYYYMMDD_HHMMSS
            assert re.search(pattern, temp_dir.name) is not None
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_get_temp_dir_is_writable(self):
        """Test that created temp directory is writable."""
        temp_dir = get_temp_dir()
        
        try:
            # Try to create a file in it
            test_file = temp_dir / "test.txt"
            test_file.write_text("test content")
            
            # Should succeed
            assert test_file.exists()
            assert test_file.read_text() == "test content"
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

class TestCleanTempDirs:
    """Tests for clean_temp_dirs function."""
    
    def test_clean_temp_dirs_removes_old_directories(self):
        """Test that clean_temp_dirs removes old directories."""
        # Create a temp directory
        temp_dir = get_temp_dir("cleanup_test")
        
        try:
            # Make it look old by modifying its timestamp
            old_time = time.time() - (48 * 3600)  # 48 hours ago
            os.utime(temp_dir, (old_time, old_time))
            
            # Clean up directories older than 24 hours
            count = clean_temp_dirs(prefix="transmute_cleanup_test", older_than_hours=24)
            
            # Should have removed our directory
            assert count >= 1
            assert not temp_dir.exists()
            
        except:
            # Clean up if test fails
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def test_clean_temp_dirs_preserves_recent_directories(self):
        """Test that clean_temp_dirs keeps recent directories."""
        # Create a temp directory
        temp_dir = get_temp_dir("preserve_test")
        
        try:
            # It's recent (just created)
            # Clean up directories older than 24 hours
            count = clean_temp_dirs(prefix="transmute_preserve_test", older_than_hours=24)
            
            # Should NOT have removed our directory
            assert temp_dir.exists()
            
        finally:
            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def test_clean_temp_dirs_respects_prefix(self):
        """Test that clean_temp_dirs only removes directories with matching prefix."""
        # Create temp directories with different prefixes
        temp_dir1 = get_temp_dir("prefix_test_a")
        temp_dir2 = get_temp_dir("prefix_test_b")
        
        try:
            # Make both old
            old_time = time.time() - (48 * 3600)
            os.utime(temp_dir1, (old_time, old_time))
            os.utime(temp_dir2, (old_time, old_time))
            
            # Clean only prefix_test_a
            count = clean_temp_dirs(prefix="transmute_prefix_test_a", older_than_hours=24)
            
            # temp_dir1 should be removed, temp_dir2 should remain
            assert not temp_dir1.exists()
            assert temp_dir2.exists()
            
        finally:
            # Clean up
            if temp_dir1.exists():
                shutil.rmtree(temp_dir1)
            if temp_dir2.exists():
                shutil.rmtree(temp_dir2)
    
    def test_clean_temp_dirs_returns_count(self):
        """Test that clean_temp_dirs returns correct count."""
        # Create multiple old temp directories
        temp_dirs = []
        for i in range(3):
            temp_dir = get_temp_dir(f"count_test_{i}")
            temp_dirs.append(temp_dir)
        
        try:
            # Make them all old
            old_time = time.time() - (48 * 3600)
            for temp_dir in temp_dirs:
                os.utime(temp_dir, (old_time, old_time))
            
            # Clean them up
            count = clean_temp_dirs(prefix="transmute_count_test", older_than_hours=24)
            
            # Should return 3
            assert count == 3
            
            # All should be removed
            for temp_dir in temp_dirs:
                assert not temp_dir.exists()
            
        except:
            # Clean up if test fails
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            raise
    
    def test_clean_temp_dirs_with_custom_age(self):
        """Test clean_temp_dirs with custom age threshold."""
        # Create a temp directory
        temp_dir = get_temp_dir("age_test")
        
        try:
            # Make it 2 hours old
            old_time = time.time() - (2 * 3600)
            os.utime(temp_dir, (old_time, old_time))
            
            # Try to clean directories older than 3 hours (should keep it)
            count1 = clean_temp_dirs(prefix="transmute_age_test", older_than_hours=3)
            assert temp_dir.exists()
            
            # Clean directories older than 1 hour (should remove it)
            count2 = clean_temp_dirs(prefix="transmute_age_test", older_than_hours=1)
            assert not temp_dir.exists()
            assert count2 >= 1
            
        except:
            # Clean up if test fails
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def test_clean_temp_dirs_handles_empty_result(self):
        """Test that clean_temp_dirs returns 0 when nothing to clean."""
        # Clean with a prefix that doesn't exist
        count = clean_temp_dirs(prefix="nonexistent_prefix_xyz123", older_than_hours=1)
        
        # Should return 0
        assert count == 0
    
    def test_clean_temp_dirs_with_default_prefix(self):
        """Test clean_temp_dirs with default 'transmute' prefix."""
        # Create a temp directory with default prefix
        temp_dir = get_temp_dir()  # Uses "transmute" prefix
        
        try:
            # Make it old
            old_time = time.time() - (48 * 3600)
            os.utime(temp_dir, (old_time, old_time))
            
            # Clean with default prefix
            count = clean_temp_dirs(older_than_hours=24)
            
            # Should have removed it
            assert count >= 1
            
        except:
            # Clean up if test fails
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise