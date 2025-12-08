from typing import Optional
from pathlib import Path
from loguru import logger
import sys


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """
    Configure Loguru logger for the entire application.
    
    This function should be called once at application startup.
    It configures:
    - Log level
    - Output format
    - Optional file logging with rotation
    - Color-coded console output
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs. If None, only console logging.
        rotation: When to rotate log file (e.g., "10 MB", "1 day")
        retention: How long to keep old log files (e.g., "1 week", "10 days")
        
    Returns:
        None (configures global logger)
        
    Raises:
        ValueError: If invalid log level provided
        
    Example:
        >>> setup_logger("DEBUG", "logs/transmute.log")
        >>> setup_logger("INFO")  # Console only
    """
    # Validate log level
    valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    if level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log level: {level}. Must be one of {valid_levels}"
        )
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stderr,
        level=level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            level=level.upper(),
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            rotation=rotation,
            retention=retention,
            compression="zip",  # Compress rotated files
        )
        
        logger.info(f"Logging to file: {log_path}")
    
    logger.info(f"Logger initialized with level: {level.upper()}")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.
    
    Note: This is just a convenience wrapper around loguru's logger.
    Loguru uses a single global logger, but we can bind context to it.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance bound to the module name
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
    """
    return logger.bind(name=name)