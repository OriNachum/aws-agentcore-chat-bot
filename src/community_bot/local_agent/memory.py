"""Conversation memory management for LocalAgent framework."""

from __future__ import annotations

from typing import Dict, List


class ConversationMemory:
    """Manages the conversational context and history."""
    
    def __init__(self, max_messages: int = 50):
        """Initialize empty conversation history.
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self._history: List[Dict[str, str]] = []
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user', 'assistant', 'system')
            content: The content of the message
        """
        self._history.append({
            "role": role,
            "content": content
        })
        
        # Trim history if it exceeds max_messages, but always keep system message
        if len(self._history) > self.max_messages:
            # Find system messages to preserve
            system_messages = [msg for msg in self._history if msg["role"] == "system"]
            non_system_messages = [msg for msg in self._history if msg["role"] != "system"]
            
            # Keep the most recent non-system messages
            keep_count = self.max_messages - len(system_messages)
            if keep_count > 0:
                recent_messages = non_system_messages[-keep_count:]
                self._history = system_messages + recent_messages
            else:
                # If we have too many system messages, just keep the most recent ones
                self._history = system_messages[-self.max_messages:]
    
    def get_history(self) -> List[Dict[str, str]]:
        """Return the current conversation history.
        
        Returns:
            List of message dictionaries in format suitable for OllamaModel
        """
        return self._history.copy()
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self._history.clear()
    
    def get_last_messages(self, count: int) -> List[Dict[str, str]]:
        """Get the last N messages from history.
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of the most recent message dictionaries
        """
        return self._history[-count:] if count > 0 else []
    
    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self._history)
