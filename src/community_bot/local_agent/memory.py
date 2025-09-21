"""Conversation memory management for LocalAgent framework."""

from __future__ import annotations

from typing import Dict, List
from ..logging_config import get_logger

logger = get_logger("community_bot.memory")


class ConversationMemory:
    """Manages the conversational context and history."""
    
    def __init__(self, max_messages: int = 50):
        """Initialize empty conversation history.
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self._history: List[Dict[str, str]] = []
        self.max_messages = max_messages
        
        logger.info(f"Initializing ConversationMemory with max_messages: {max_messages}")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user', 'assistant', 'system')
            content: The content of the message
        """
        logger.debug(f"Adding {role} message: {content[:100]}...")
        
        self._history.append({
            "role": role,
            "content": content
        })
        
        old_size = len(self._history)
        
        # Trim history if it exceeds max_messages, but always keep system message
        if len(self._history) > self.max_messages:
            logger.debug(f"Trimming memory: {old_size} messages exceed limit of {self.max_messages}")
            
            # Find system messages to preserve
            system_messages = [msg for msg in self._history if msg["role"] == "system"]
            non_system_messages = [msg for msg in self._history if msg["role"] != "system"]
            
            # Keep the most recent non-system messages
            keep_count = self.max_messages - len(system_messages)
            if keep_count > 0:
                recent_messages = non_system_messages[-keep_count:]
                self._history = system_messages + recent_messages
                logger.info(f"Memory trimmed: {old_size} -> {len(self._history)} messages (kept {len(system_messages)} system + {len(recent_messages)} recent)")
            else:
                # If we have too many system messages, just keep the most recent ones
                self._history = system_messages[-self.max_messages:]
                logger.warning(f"Too many system messages: kept only {len(self._history)} most recent")
        else:
            logger.debug(f"Memory size after addition: {len(self._history)}/{self.max_messages}")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Return the current conversation history.
        
        Returns:
            List of message dictionaries in format suitable for OllamaModel
        """
        logger.debug(f"Retrieving conversation history: {len(self._history)} messages")
        return self._history.copy()
    
    def clear(self) -> None:
        """Clear the conversation history."""
        old_size = len(self._history)
        self._history.clear()
        logger.info(f"Memory cleared: {old_size} -> 0 messages")
    
    def get_last_messages(self, count: int) -> List[Dict[str, str]]:
        """Get the last N messages from history.
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of the most recent message dictionaries
        """
        if count <= 0:
            logger.debug("Requested 0 or negative messages, returning empty list")
            return []
        
        result = self._history[-count:]
        logger.debug(f"Retrieved last {count} messages: got {len(result)} messages")
        return result
    
    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self._history)
