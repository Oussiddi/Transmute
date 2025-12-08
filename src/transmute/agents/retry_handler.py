"""
Retry handler for agent error recovery.

Implements retry logic with exponential backoff and error classification.
"""

from typing import Dict, Any, Optional, Callable
import time
from enum import Enum

from transmute.core.state import TransmuteState
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Transient errors, retry immediately
    MEDIUM = "medium"     # Recoverable errors, retry with backoff
    HIGH = "high"         # Serious errors, try alternative approach
    CRITICAL = "critical" # Unrecoverable errors, fail immediately


class RetryHandler:
    """
    Handles retries for failed operations.
    
    Features:
    - Exponential backoff
    - Error classification
    - Retry strategies
    - Fallback mechanisms
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        
        self.retry_count = 0
        self.error_history: list = []
        
        logger.info(f"RetryHandler initialized (max_retries={max_retries})")
    
    def classify_error(self, error: Exception) -> ErrorSeverity:
        """
        Classify error severity.
        
        Args:
            error: Exception to classify
            
        Returns:
            ErrorSeverity level
            
        Example:
            >>> severity = handler.classify_error(ValueError("Invalid input"))
            >>> print(severity)
            ErrorSeverity.LOW
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Critical errors (don't retry)
        if error_type in ['KeyboardInterrupt', 'SystemExit']:
            return ErrorSeverity.CRITICAL
        
        # API rate limits (retry with longer delay)
        if 'rate limit' in error_str or 'too many requests' in error_str:
            return ErrorSeverity.HIGH
        
        # Network errors (retry with backoff)
        if 'connection' in error_str or 'timeout' in error_str:
            return ErrorSeverity.MEDIUM
        
        # Validation errors (low priority)
        if error_type in ['ValueError', 'TypeError', 'KeyError']:
            return ErrorSeverity.LOW
        
        # Default to medium
        return ErrorSeverity.MEDIUM
    
    def calculate_delay(self, attempt: int, severity: ErrorSeverity) -> float:
        """
        Calculate delay before retry.
        
        Args:
            attempt: Current attempt number (0-indexed)
            severity: Error severity
            
        Returns:
            Delay in seconds
            
        Example:
            >>> delay = handler.calculate_delay(2, ErrorSeverity.MEDIUM)
            >>> print(f"Wait {delay}s")
        """
        # Base delay based on severity
        severity_multiplier = {
            ErrorSeverity.LOW: 0.5,
            ErrorSeverity.MEDIUM: 1.0,
            ErrorSeverity.HIGH: 2.0,
            ErrorSeverity.CRITICAL: 0.0  # No retry
        }
        
        if severity == ErrorSeverity.CRITICAL:
            return 0.0
        
        # Exponential backoff
        delay = self.base_delay * severity_multiplier[severity]
        delay *= (self.exponential_base ** attempt)
        
        # Cap at max_delay
        return min(delay, self.max_delay)
    
    def should_retry(
        self,
        error: Exception,
        attempt: int,
        severity: Optional[ErrorSeverity] = None
    ) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            error: Exception that occurred
            attempt: Current attempt number
            severity: Optional pre-classified severity
            
        Returns:
            True if should retry
            
        Example:
            >>> if handler.should_retry(error, 1):
            ...     # Retry the operation
        """
        if severity is None:
            severity = self.classify_error(error)
        
        # Never retry critical errors
        if severity == ErrorSeverity.CRITICAL:
            logger.error(f"Critical error, no retry: {error}")
            return False
        
        # Check max retries
        if attempt >= self.max_retries:
            logger.warning(f"Max retries ({self.max_retries}) reached")
            return False
        
        return True
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            fallback: Optional fallback function if all retries fail
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail and no fallback provided
            
        Example:
            >>> result = handler.execute_with_retry(
            ...     translate_code,
            ...     source_code,
            ...     fallback=simple_translate
            ... )
        """
        attempt = 0
        last_error = None
        
        while attempt <= self.max_retries:
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries + 1}")
                
                result = func(*args, **kwargs)
                
                # Success!
                if attempt > 0:
                    logger.info(f"Succeeded after {attempt} retries")
                
                return result
                
            except Exception as error:
                last_error = error
                severity = self.classify_error(error)
                
                # Log error
                self.error_history.append({
                    'attempt': attempt,
                    'error': str(error),
                    'severity': severity.value
                })
                
                logger.warning(
                    f"Attempt {attempt + 1} failed: {error} "
                    f"(severity: {severity.value})"
                )
                
                # Check if should retry
                if not self.should_retry(error, attempt, severity):
                    break
                
                # Calculate and wait
                delay = self.calculate_delay(attempt, severity)
                
                if delay > 0:
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                
                attempt += 1
        
        # All retries failed
        if fallback:
            logger.info("Attempting fallback function")
            try:
                return fallback(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
        
        # No fallback or fallback failed
        logger.error(f"All retries failed. Last error: {last_error}")
        raise last_error
    
    def get_error_history(self) -> list:
        """
        Get history of errors encountered.
        
        Returns:
            List of error records
            
        Example:
            >>> history = handler.get_error_history()
            >>> for error in history:
            ...     print(f"{error['attempt']}: {error['error']}")
        """
        return self.error_history.copy()
    
    def reset(self) -> None:
        """
        Reset retry handler state.
        
        Example:
            >>> handler.reset()
        """
        self.retry_count = 0
        self.error_history.clear()
        logger.debug("RetryHandler reset")