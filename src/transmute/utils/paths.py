"""
Path utilities for Transmute.

Handles directory creation, temporary directories, and path management.
"""

from pathlib import Path
from typing import Union
import tempfile
import shutil
import time

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Create directory if it doesn't exist.
    
    This function safely creates a directory and all parent directories
    if they don't exist. If the directory already exists, it does nothing.
    
    Args:
        path: Directory path to create (can be string or Path object)
        
    Returns:
        Path object of the created/existing directory
        
    Raises:
        PermissionError: If lacking permissions to create directory
        OSError: If path exists but is not a directory
        
    Example:
        >>> repo_dir = ensure_dir("/tmp/transmute/repos")
        >>> # Now /tmp/transmute/repos exists
        
        >>> ensure_dir("data/output")  # Relative paths work too
        PosixPath('data/output')
    """
    # Convert to Path object
    dir_path = Path(path)
    
    # Check if it already exists
    if dir_path.exists():
        if not dir_path.is_dir():
            raise OSError(
                f"Path exists but is not a directory: {dir_path}"
            )
        logger.debug(f"Directory already exists: {dir_path}")
        return dir_path
    
    # Create the directory (including parents)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
        return dir_path
        
    except PermissionError as e:
        logger.error(f"Permission denied creating directory: {dir_path}")
        raise PermissionError(
            f"Cannot create directory {dir_path}: {e}"
        ) from e
    
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        raise
def get_temp_dir(prefix: str = "transmute") -> Path:
    """
    Create a temporary directory for this session.
    
    Creates a unique temporary directory with a timestamp and optional prefix.
    The directory is created in the system's temp directory.
    All directories will start with "transmute_" for easy identification.
    
    Args:
        prefix: Additional prefix after "transmute_" (default: just "transmute")
        
    Returns:
        Path to the created temporary directory
        
    Example:
        >>> temp = get_temp_dir("migration_123")
        >>> print(temp)
        PosixPath('/tmp/transmute_migration_123_20251206_231545_abc123')
        
        >>> temp = get_temp_dir()
        >>> print(temp)
        PosixPath('/tmp/transmute_20251206_231545_xyz789')
    """
    # Get system temp directory
    system_temp = Path(tempfile.gettempdir())
    
    # Create timestamp for uniqueness
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Always start with "transmute_", then add custom prefix if provided
    if prefix == "transmute":
        temp_dir_name = f"transmute_{timestamp}_"
    else:
        temp_dir_name = f"transmute_{prefix}_{timestamp}_"
    
    # Use tempfile.mkdtemp to create unique directory
    temp_path = Path(
        tempfile.mkdtemp(prefix=temp_dir_name, dir=system_temp)
    )
    
    logger.info(f"Created temporary directory: {temp_path}")
    
    return temp_path

def clean_temp_dirs(
    prefix: str = "transmute",
    older_than_hours: int = 24
) -> int:
    """
    Clean up old temporary directories created by get_temp_dir.
    
    Removes temporary directories that match the prefix and are older
    than the specified number of hours. This helps prevent disk space
    from filling up with old migration artifacts.
    
    Args:
        prefix: Only clean directories with this prefix (default: "transmute")
        older_than_hours: Remove directories older than this many hours
        
    Returns:
        Number of directories removed
        
    Raises:
        PermissionError: If lacking permissions to delete directories
        
    Example:
        >>> # Remove transmute temp dirs older than 48 hours
        >>> count = clean_temp_dirs(older_than_hours=48)
        >>> print(f"Removed {count} old directories")
        
        >>> # Remove specific migration temp dirs older than 1 hour
        >>> count = clean_temp_dirs(prefix="transmute_migration", older_than_hours=1)
    """
    system_temp = Path(tempfile.gettempdir())
    removed_count = 0
    current_time = time.time()
    cutoff_time = current_time - (older_than_hours * 3600)  # Convert hours to seconds
    
    logger.debug(
        f"Cleaning temp directories with prefix '{prefix}' "
        f"older than {older_than_hours} hours"
    )
    
    # Find all directories in system temp matching the prefix
    try:
        for item in system_temp.iterdir():
            # Skip if not a directory
            if not item.is_dir():
                continue
            
            # Skip if doesn't match prefix
            if not item.name.startswith(prefix):
                continue
            
            # Check modification time
            try:
                mtime = item.stat().st_mtime
                
                # Skip if not old enough
                if mtime >= cutoff_time:
                    logger.debug(f"Skipping recent directory: {item.name}")
                    continue
                
                # Remove the directory
                logger.info(f"Removing old temp directory: {item.name}")
                shutil.rmtree(item)
                removed_count += 1
                
            except PermissionError:
                logger.warning(f"Permission denied removing directory: {item.name}")
                continue
                
            except Exception as e:
                logger.warning(f"Failed to remove directory {item.name}: {e}")
                continue
        
        logger.info(f"Cleaned up {removed_count} old temporary directories")
        return removed_count
        
    except PermissionError as e:
        logger.error(f"Permission denied accessing temp directory: {system_temp}")
        raise PermissionError(
            f"Cannot access temp directory {system_temp}: {e}"
        ) from e
    
    except Exception as e:
        logger.error(f"Error cleaning temp directories: {e}")
        raise