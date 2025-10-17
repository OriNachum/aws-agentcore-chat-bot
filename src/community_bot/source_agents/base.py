"""Base class for all source agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .document import Document


class SourceAgent(ABC):
    """Base class for all source agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Type of agent (database, browser, mcp, script, etc.)."""
        pass
    
    @abstractmethod
    async def collect(self) -> List[Document]:
        """Collect data and return structured documents."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the agent is healthy and can collect data."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata (schedule, dependencies, etc.)."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "version": "1.0.0",
        }
