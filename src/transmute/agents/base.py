"""
Base agent class for Transmute.

Defines the interface for all LangGraph agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from transmute.core.state import TransmuteState
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents are LangGraph nodes that process the TransmuteState and return
    updated state.
    """
    
    def __init__(self, name: str):
        """
        Initialize agent.
        
        Args:
            name: Agent name
        """
        self.name = name
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    def process(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Process state and return updates.
        
        Args:
            state: Current TransmuteState
            
        Returns:
            Dictionary of state updates
        """
        pass
    
    def __call__(self, state: TransmuteState) -> Dict[str, Any]:
        """
        Make agent callable for LangGraph.
        
        Args:
            state: Current state
            
        Returns:
            State updates
        """
        logger.info(f"Running {self.name} agent")
        
        try:
            updates = self.process(state)
            logger.info(f"{self.name} agent completed successfully")
            return updates
            
        except Exception as e:
            logger.error(f"{self.name} agent failed: {e}")
            return {
                "errors": state.errors + [f"{self.name} failed: {str(e)}"],
                "current_step": "error"
            }
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log error message."""
        logger.error(f"[{self.name}] {message}")
    
    def log_debug(self, message: str) -> None:
        """Log debug message."""
        logger.debug(f"[{self.name}] {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        logger.warning(f"[{self.name}] {message}")