"""
Agent orchestrator for coordinating multiple agents.

Manages agent lifecycle, communication, and error recovery.
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from transmute.agents.base import BaseAgent
from transmute.core.state import TransmuteState
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple agents in a workflow.
    
    Handles:
    - Agent execution order
    - Inter-agent communication
    - Error recovery
    - Progress tracking
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_order: List[str] = []
        self.callbacks: Dict[str, List[Callable]] = {
            'before_agent': [],
            'after_agent': [],
            'on_error': [],
            'on_complete': []
        }
        
        logger.info("AgentOrchestrator initialized")
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            name: Agent name/identifier
            agent: Agent instance
            
        Example:
            >>> orchestrator.register_agent("analysis", AnalysisAgent(registry))
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def set_execution_order(self, order: List[str]) -> None:
        """
        Set the order in which agents should execute.
        
        Args:
            order: List of agent names in execution order
            
        Example:
            >>> orchestrator.set_execution_order(["analysis", "planning", "translation"])
        """
        # Validate all agents exist
        for name in order:
            if name not in self.agents:
                raise ValueError(f"Agent not registered: {name}")
        
        self.execution_order = order
        logger.info(f"Execution order set: {' → '.join(order)}")
    
    def register_callback(
        self,
        event: str,
        callback: Callable[[str, TransmuteState], None]
    ) -> None:
        """
        Register a callback for agent events.
        
        Args:
            event: Event type ('before_agent', 'after_agent', 'on_error', 'on_complete')
            callback: Callback function(agent_name, state)
            
        Example:
            >>> def on_complete(name, state):
            ...     print(f"{name} completed!")
            >>> orchestrator.register_callback('after_agent', on_complete)
        """
        if event not in self.callbacks:
            raise ValueError(f"Unknown event: {event}")
        
        self.callbacks[event].append(callback)
        logger.debug(f"Registered callback for: {event}")
    
    def execute(
        self,
        initial_state: TransmuteState,
        stop_on_error: bool = False
    ) -> TransmuteState:
        """
        Execute all agents in order.
        
        Args:
            initial_state: Initial state
            stop_on_error: Whether to stop on first error
            
        Returns:
            Final state after all agents
            
        Example:
            >>> final_state = orchestrator.execute(initial_state)
        """
        logger.info("Starting agent orchestration")
        
        state = initial_state
        
        for agent_name in self.execution_order:
            agent = self.agents[agent_name]
            
            # Before callbacks
            for callback in self.callbacks['before_agent']:
                try:
                    callback(agent_name, state)
                except Exception as e:
                    logger.warning(f"Before callback failed: {e}")
            
            # Execute agent
            try:
                logger.info(f"Executing agent: {agent_name}")
                
                result = agent(state)
                
                # Update state
                for key, value in result.items():
                    setattr(state, key, value)
                
                # After callbacks
                for callback in self.callbacks['after_agent']:
                    try:
                        callback(agent_name, state)
                    except Exception as e:
                        logger.warning(f"After callback failed: {e}")
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                
                # Error callbacks
                for callback in self.callbacks['on_error']:
                    try:
                        callback(agent_name, state)
                    except Exception as callback_error:
                        logger.warning(f"Error callback failed: {callback_error}")
                
                # Add error to state
                state.add_error(f"Agent {agent_name} failed: {str(e)}")
                
                # Stop if configured to do so
                if stop_on_error:
                    logger.error("Stopping execution due to error")
                    break
            
            # Check if there were errors even if no exception was raised
            # (agent might have caught its own exception)
            if stop_on_error and state.errors:
                # Check if errors were added during this agent's execution
                logger.error("Stopping execution - errors detected")
                break
        
        # Complete callbacks
        for callback in self.callbacks['on_complete']:
            try:
                callback("orchestrator", state)
            except Exception as e:
                logger.warning(f"Complete callback failed: {e}")
        
        logger.info("Agent orchestration complete")
        
        return state
    
    def get_agent_status(self) -> Dict[str, str]:
        """
        Get status of all registered agents.
        
        Returns:
            Dictionary of agent name -> status
            
        Example:
            >>> status = orchestrator.get_agent_status()
            >>> print(status)
            {'analysis': 'ready', 'planning': 'ready'}
        """
        status = {}
        
        for name, agent in self.agents.items():
            status[name] = "ready"  # Could be enhanced with actual agent state
        
        return status