"""LocalAgent - Central orchestrator for the local agent framework."""

from __future__ import annotations

from typing import AsyncGenerator

from .memory import ConversationMemory
from .model import OllamaModel


class LocalAgent:
    """The central orchestrator for the local agent framework.
    
    Manages conversation flow, interacts with the model, and uses memory
    to maintain context across interactions.
    """
    
    def __init__(self, model: OllamaModel, memory: ConversationMemory, system_prompt: str = None):
        """Initialize the agent with a model and memory.
        
        Args:
            model: OllamaModel instance for AI interactions
            memory: ConversationMemory instance for context management
            system_prompt: Optional custom system prompt
        """
        self.model = model
        self.memory = memory
        
        # Add system message if memory is empty
        if len(self.memory) == 0:
            default_prompt = (
                "You are a helpful assistant for a Discord community. "
                "Provide clear, concise, and friendly responses."
            )
            prompt = system_prompt or default_prompt
            self.memory.add_message("system", prompt)
    
    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process a user message and generate a streaming response.
        
        Args:
            user_message: The message from the user
            
        Yields:
            String chunks of the assistant's response
        """
        # Add user message to memory
        self.memory.add_message("user", user_message)
        
        # Get conversation history
        history = self.memory.get_history()
        
        # Stream response from model
        response_chunks = []
        async for chunk in self.model.chat(history):
            response_chunks.append(chunk)
            yield chunk
        
        # Add complete response to memory
        complete_response = "".join(response_chunks)
        if complete_response.strip():
            self.memory.add_message("assistant", complete_response)
    
    async def chat_complete(self, user_message: str) -> str:
        """Process a user message and return a complete response.
        
        Args:
            user_message: The message from the user
            
        Returns:
            Complete response string from the assistant
        """
        chunks = []
        async for chunk in self.chat(user_message):
            chunks.append(chunk)
        return "".join(chunks)
    
    def clear_memory(self, system_prompt: str = None) -> None:
        """Clear the conversation memory and reinitialize with system message.
        
        Args:
            system_prompt: Optional custom system prompt to use
        """
        self.memory.clear()
        default_prompt = (
            "You are a helpful assistant for a Discord community. "
            "Provide clear, concise, and friendly responses."
        )
        prompt = system_prompt or default_prompt
        self.memory.add_message("system", prompt)
    
    def get_memory_size(self) -> int:
        """Get the current number of messages in memory.
        
        Returns:
            Number of messages in conversation history
        """
        return len(self.memory)
