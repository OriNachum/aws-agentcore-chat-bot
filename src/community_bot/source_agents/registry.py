"""Central registry for all source agents."""

from typing import Any, Dict, List, Optional

from ..logging_config import get_logger
from .base import SourceAgent


class AgentRegistry:
    """Central registry for all source agents."""
    
    def __init__(self):
        self.agents: Dict[str, SourceAgent] = {}
        self.schedules: Dict[str, str] = {}  # agent_id -> cron expression
        self.logger = get_logger("agent_registry")
    
    def register(
        self, 
        agent: SourceAgent, 
        schedule: str = "0 */6 * * *"  # Default: every 6 hours
    ):
        """Register a new source agent."""
        agent_id = agent.agent_id
        
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} already registered, replacing")
        
        self.agents[agent_id] = agent
        self.schedules[agent_id] = schedule
        self.logger.info(f"Registered agent {agent_id} with schedule {schedule}")
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent by ID."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.schedules[agent_id]
            self.logger.info(f"Unregistered agent {agent_id}")
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[SourceAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their metadata."""
        return [
            {
                **agent.get_metadata(),
                "schedule": self.schedules.get(agent.agent_id),
            }
            for agent in self.agents.values()
        ]
