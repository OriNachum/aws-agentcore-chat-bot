"""LocalAgent - Central orchestrator for the local agent framework."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from .memory import ConversationMemory
from .model import OllamaModel
from ..logging_config import get_logger

logger = get_logger("community_bot.agent.local")


class LocalAgent:
    """The central orchestrator for the local agent framework.
    
    Manages conversation flow, interacts with the model, and uses memory
    to maintain context across interactions.
    """
    
    def __init__(self, model: OllamaModel, memory: ConversationMemory, system_prompt: Optional[str] = None):
        """Initialize the agent with a model and memory.
        
        Args:
            model: OllamaModel instance for AI interactions
            memory: ConversationMemory instance for context management
            system_prompt: Optional custom system prompt
        """
        self.model = model
        self.memory = memory
        
        logger.info("Initializing LocalAgent")
        logger.debug(f"Memory max messages: {memory.max_messages}")
        
        # Add system message if memory is empty
        if len(self.memory) == 0:
            default_prompt = (
                "You are a helpful assistant for a Discord community. "
                "Provide clear, concise, and friendly responses."
            )
            prompt = system_prompt or default_prompt
            self.memory.add_message("system", prompt)
            logger.info(f"Added system message to empty memory: {prompt[:100]}...")
        else:
            logger.debug(f"Memory already contains {len(self.memory)} messages")
        
        logger.info("LocalAgent initialization complete")
    
    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process a user message and generate a streaming response.
        
        Args:
            user_message: The message from the user
            
        Yields:
            String chunks of the assistant's response
        """
        logger.debug(f"Processing user message: {user_message[:100]}...")
        
        # Add user message to memory
        self.memory.add_message("user", user_message)
        logger.debug(f"Added user message to memory. Memory size: {len(self.memory)}")
        
        # Get conversation history
        history = self.memory.get_history()
        logger.debug(f"Retrieved conversation history: {len(history)} messages")
        
        # Stream response from model
        response_chunks = []
        chunk_count = 0
        
        logger.debug("Starting model chat stream")
        async for chunk in self.model.chat(history):
            chunk_count += 1
            response_chunks.append(chunk)
            logger.debug(f"Received model chunk {chunk_count}: {len(chunk)} characters")
            yield chunk
        
        # Add complete response to memory
        complete_response = "".join(response_chunks)
        if complete_response.strip():
            self.memory.add_message("assistant", complete_response)
            logger.info(f"Chat completed: {len(complete_response)} characters in {chunk_count} chunks")
            logger.debug(f"Memory size after response: {len(self.memory)}")
        else:
            logger.warning("Empty response received from model")

    async def chat_complete(self, user_message: str) -> str:
        """Process a user message and return a complete response.
        
        Args:
            user_message: The message from the user
            
        Returns:
            Complete response string from the assistant
        """
        logger.debug(f"Processing complete chat request: {user_message[:100]}...")
        chunks = []
        async for chunk in self.chat(user_message):
            chunks.append(chunk)
        response = "".join(chunks)
        logger.info(f"Complete chat finished: {len(response)} characters")
        return response
    
    def clear_memory(self, system_prompt: Optional[str] = None) -> None:
        """Clear the conversation memory and reinitialize with system message.
        
        Args:
            system_prompt: Optional custom system prompt to use
        """
        logger.info("Clearing conversation memory")
        old_size = len(self.memory)
        self.memory.clear()
        
        default_prompt = (
            "You are a helpful assistant for a Discord community. "
            "Provide clear, concise, and friendly responses."
        )
        prompt = system_prompt or default_prompt
        self.memory.add_message("system", prompt)
        logger.info(f"Memory cleared: {old_size} -> {len(self.memory)} messages")
        logger.debug(f"New system prompt: {prompt[:100]}...")
    
    def get_memory_size(self) -> int:
        """Get the current number of messages in memory.
        
        Returns:
            Number of messages in conversation history
        """
        size = len(self.memory)
        logger.debug(f"Current memory size: {size} messages")
        return size
