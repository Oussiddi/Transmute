"""
Tests for logging utilities.
"""

import pytest
from pathlib import Path
import tempfile
from loguru import logger

from transmute.utils.logger import setup_logger, get_logger


class TestSetupLogger:
    """Tests for setup_logger function."""
    
    def setup_method(self):
        """Run before each test - clean up logger."""
        logger.remove()  # Remove all handlers before each test
    
    def teardown_method(self):
        """Run after each test - clean up logger."""
        logger.remove()
    
    def test_setup_logger_default(self):
        """Test setup_logger with default parameters."""
        # Should not raise any exception
        setup_logger()
        
        # Logger should be configured
        # We can't directly check handlers, but we can log a message
        logger.info("Test message")
        # If we get here without exception, it works
    
    def test_setup_logger_custom_level(self):
        """Test setup_logger with custom log level."""
        setup_logger(level="DEBUG")
        logger.debug("Debug message")
        
        setup_logger(level="ERROR")
        logger.error("Error message")
    
    def test_setup_logger_invalid_level(self):
        """Test setup_logger with invalid log level."""
        with pytest.raises(ValueError, match="Invalid log level"):
            setup_logger(level="INVALID")
    
    def test_setup_logger_with_file(self):
        """Test setup_logger with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            setup_logger(level="INFO", log_file=str(log_file))
            
            # Log some messages
            logger.info("Test info message")
            logger.warning("Test warning message")
            
            # Check file was created
            assert log_file.exists()
            
            # Check content was written
            content = log_file.read_text()
            assert "Test info message" in content
            assert "Test warning message" in content
            
            # IMPORTANT: Close logger to release file handle on Windows
            logger.remove()
    
    def test_setup_logger_creates_log_directory(self):
        """Test that setup_logger creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "subdir" / "test.log"
            
            # Directory doesn't exist yet
            assert not log_file.parent.exists()
            
            setup_logger(log_file=str(log_file))
            
            # Directory should be created
            assert log_file.parent.exists()
            
            # Log a message
            logger.info("Test message")
            
            # File should exist
            assert log_file.exists()
            
            # IMPORTANT: Close logger to release file handle on Windows
            logger.remove()
    
    def test_setup_logger_case_insensitive_level(self):
        """Test that log level is case-insensitive."""
        setup_logger(level="info")  # lowercase
        logger.info("Test")
        
        setup_logger(level="DEBUG")  # uppercase
        logger.debug("Test")
        
        setup_logger(level="WaRnInG")  # mixed case
        logger.warning("Test")


class TestGetLogger:
    """Tests for get_logger function."""
    
    def setup_method(self):
        """Run before each test."""
        logger.remove()
        setup_logger()  # Initialize with default settings
    
    def teardown_method(self):
        """Run after each test."""
        logger.remove()
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        test_logger = get_logger(__name__)
        
        # Should be able to log
        test_logger.info("Test message")
    
    def test_get_logger_with_different_names(self):
        """Test get_logger with different module names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both should work
        logger1.info("Message from module1")
        logger2.info("Message from module2")
    
    def test_get_logger_inherits_global_config(self):
        """Test that loggers from get_logger use global configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Setup with file logging
            setup_logger(level="DEBUG", log_file=str(log_file))
            
            # Get a logger
            test_logger = get_logger("test_module")
            
            # Log a message
            test_logger.debug("Debug from test_module")
            
            # Should appear in file
            content = log_file.read_text()
            assert "Debug from test_module" in content
            
            # IMPORTANT: Close logger to release file handle on Windows
            logger.remove()