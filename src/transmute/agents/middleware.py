"""
Middleware system for agent processing pipelines.

Allows pre/post processing hooks and transformation chains.
"""

from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod

from transmute.core.state import TransmuteState, TranslationUnit
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class Middleware(ABC):
    """
    Base middleware class.
    
    Middleware can process data before/after agent execution.
    """
    
    def __init__(self, name: str):
        """
        Initialize middleware.
        
        Args:
            name: Middleware name
        """
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def process(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Process data.
        
        Args:
            data: Data to process
            context: Optional context information
            
        Returns:
            Processed data
        """
        pass
    
    def __call__(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Make middleware callable."""
        if not self.enabled:
            return data
        
        return self.process(data, context)


class CodeNormalizationMiddleware(Middleware):
    """
    Normalizes code formatting before translation.
    
    - Removes trailing whitespace
    - Normalizes line endings
    - Removes multiple blank lines
    """
    
    def __init__(self):
        """Initialize code normalization middleware."""
        super().__init__("CodeNormalization")
    
    def process(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Normalize code formatting.
        
        Args:
            data: Source code
            context: Optional context
            
        Returns:
            Normalized code
        """
        if not isinstance(data, str):
            return data
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in data.splitlines()]
        
        # Remove multiple blank lines
        normalized = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            
            if is_blank and prev_blank:
                continue
            
            normalized.append(line)
            prev_blank = is_blank
        
        return '\n'.join(normalized)


class CommentPreservationMiddleware(Middleware):
    """
    Preserves important comments during translation.
    
    - Extracts comments
    - Tags them for preservation
    - Re-inserts after translation
    """
    
    def __init__(self):
        """Initialize comment preservation middleware."""
        super().__init__("CommentPreservation")
        self.comment_map: Dict[str, List[str]] = {}
    
    def process(
        self,
        data: TranslationUnit,
        context: Optional[Dict[str, Any]] = None
    ) -> TranslationUnit:
        """
        Extract and preserve comments.
        
        Args:
            data: Translation unit
            context: Optional context
            
        Returns:
            Modified translation unit
        """
        if not data.source_code:
            return data
        
        # Extract comments (simple implementation)
        comments = []
        lines = data.source_code.splitlines()
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                comments.append({
                    'line': i,
                    'text': stripped
                })
        
        # Store in metadata
        if comments:
            data.metadata['preserved_comments'] = comments
            logger.debug(f"Preserved {len(comments)} comments from {data.source_path}")
        
        return data


class QualityCheckMiddleware(Middleware):
    """
    Performs quality checks on translations.
    
    - Checks for syntax errors
    - Validates structure
    - Scores quality
    """
    
    def __init__(self, min_quality: float = 0.5):
        """
        Initialize quality check middleware.
        
        Args:
            min_quality: Minimum quality score (0.0-1.0)
        """
        super().__init__("QualityCheck")
        self.min_quality = min_quality
    
    def process(
        self,
        data: TranslationUnit,
        context: Optional[Dict[str, Any]] = None
    ) -> TranslationUnit:
        """
        Check translation quality.
        
        Args:
            data: Translation unit
            context: Optional context
            
        Returns:
            Translation unit with quality score
        """
        if not data.translated_code:
            return data
        
        quality_score = self._calculate_quality(data)
        
        data.metadata['quality_score'] = quality_score
        
        if quality_score < self.min_quality:
            logger.warning(
                f"Low quality translation: {data.source_path} "
                f"(score: {quality_score:.2f})"
            )
            data.metadata['needs_review'] = True
        
        return data
    
    def _calculate_quality(self, unit: TranslationUnit) -> float:
        """Calculate quality score (0.0-1.0)."""
        score = 1.0
        
        code = unit.translated_code
        
        # Check for obvious issues
        if not code or len(code) < 10:
            score -= 0.5
        
        # Check for balanced braces/parens
        if code.count('{') != code.count('}'):
            score -= 0.2
        
        if code.count('(') != code.count(')'):
            score -= 0.2
        
        # Check for TODO/FIXME (bigger penalty)
        if 'TODO' in code or 'FIXME' in code:
            score -= 0.3  # Changed from 0.1 to 0.3
        
        # Check if code is very short (might be incomplete)
        if len(code.strip()) < 50:
            score -= 0.2
        
        return max(0.0, min(1.0, score))


class MiddlewarePipeline:
    """
    Pipeline for executing multiple middleware in sequence.
    
    Allows building complex processing chains.
    """
    
    def __init__(self, name: str = "Pipeline"):
        """
        Initialize middleware pipeline.
        
        Args:
            name: Pipeline name
        """
        self.name = name
        self.middlewares: List[Middleware] = []
        
        logger.info(f"MiddlewarePipeline '{name}' initialized")
    
    def add(self, middleware: Middleware) -> 'MiddlewarePipeline':
        """
        Add middleware to pipeline.
        
        Args:
            middleware: Middleware to add
            
        Returns:
            Self for chaining
            
        Example:
            >>> pipeline.add(CodeNormalizationMiddleware())
            ...         .add(QualityCheckMiddleware())
        """
        self.middlewares.append(middleware)
        logger.debug(f"Added middleware: {middleware.name}")
        
        return self
    
    def remove(self, name: str) -> bool:
        """
        Remove middleware by name.
        
        Args:
            name: Middleware name
            
        Returns:
            True if removed
            
        Example:
            >>> pipeline.remove("QualityCheck")
        """
        for i, middleware in enumerate(self.middlewares):
            if middleware.name == name:
                self.middlewares.pop(i)
                logger.debug(f"Removed middleware: {name}")
                return True
        
        return False
    
    def process(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Process data through all middleware.
        
        Args:
            data: Data to process
            context: Optional context
            
        Returns:
            Processed data
            
        Example:
            >>> processed = pipeline.process(unit)
        """
        result = data
        
        for middleware in self.middlewares:
            if not middleware.enabled:
                continue
            
            try:
                result = middleware(result, context)
            except Exception as e:
                logger.error(
                    f"Middleware {middleware.name} failed: {e}"
                )
                # Continue with unprocessed data
        
        return result
    
    def enable_all(self) -> None:
        """Enable all middleware in pipeline."""
        for middleware in self.middlewares:
            middleware.enabled = True
        
        logger.debug("Enabled all middleware")
    
    def disable_all(self) -> None:
        """Disable all middleware in pipeline."""
        for middleware in self.middlewares:
            middleware.enabled = False
        
        logger.debug("Disabled all middleware")
    
    def get_enabled(self) -> List[str]:
        """
        Get list of enabled middleware names.
        
        Returns:
            List of middleware names
            
        Example:
            >>> enabled = pipeline.get_enabled()
            >>> print(f"Active: {', '.join(enabled)}")
        """
        return [
            m.name for m in self.middlewares
            if m.enabled
        ]