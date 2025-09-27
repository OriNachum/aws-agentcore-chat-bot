"""LocalAgent - Central orchestrator for the local agent framework."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from .memory import ConversationMemory
from .model import OllamaModel
from ..logging_config import get_logger
from ..config import Settings
from ..prompt_loader import PromptBundle, load_prompt_bundle

logger = get_logger("community_bot.agent.local")


class LocalAgent:
    """The central orchestrator for the local agent framework.
    
    Manages conversation flow, interacts with the model, and uses memory
    to maintain context across interactions.
    """
    
    def __init__(
        self,
        model: OllamaModel,
        memory: ConversationMemory,
        settings: Settings,
        prompt_bundle: Optional[PromptBundle] = None,
    ):
        """Initialize the agent with a model and memory.
        
        Args:
            model: OllamaModel instance for AI interactions
            memory: ConversationMemory instance for context management
            settings: Global application settings controlling prompt selection
            prompt_bundle: Optional pre-loaded prompt bundle to reuse
        """
        self.model = model
        self.memory = memory
        self.settings = settings
        self.prompt_user_role = (settings.prompt_user_role or "user").strip() or "user"
        self.prompt_bundle = prompt_bundle or load_prompt_bundle(settings)
        
        logger.info("Initializing LocalAgent")
        logger.debug(f"Memory max messages: {memory.max_messages}")
        
        if self.prompt_bundle.user and self.memory.max_messages < 3:
            logger.warning(
                "Memory may be too small (%s) to retain system prompt, primer, and user messages.",
                self.memory.max_messages,
            )

        self._initialize_memory()
        
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
    
    def clear_memory(self) -> None:
        """Clear the conversation memory and reinitialize with current prompts."""
        logger.info("Clearing conversation memory")
        old_size = len(self.memory)
        self.memory.clear()

        self.prompt_bundle = load_prompt_bundle(self.settings, refresh=True)
        logger.debug(
            "Reloaded prompt bundle for profile '%s' during memory clear",
            self.prompt_bundle.profile,
        )
        self._apply_prompt_bundle(self.prompt_bundle)
        logger.info(f"Memory cleared: {old_size} -> {len(self.memory)} messages")
    
    def get_memory_size(self) -> int:
        """Get the current number of messages in memory.
        
        Returns:
            Number of messages in conversation history
        """
        size = len(self.memory)
        logger.debug(f"Current memory size: {size} messages")
        return size

    def _initialize_memory(self) -> None:
        if len(self.memory) > 0:
            logger.debug(
                "Memory already contains %s messages; reinitializing with prompt bundle",
                len(self.memory),
            )
            self.memory.clear()

        self._apply_prompt_bundle(self.prompt_bundle)

    def _apply_prompt_bundle(self, bundle: PromptBundle) -> None:
        self.memory.add_message("system", bundle.system)
        logger.info("Added system message for profile '%s'", bundle.profile)

        if bundle.user:
            self.memory.add_message(self.prompt_user_role, bundle.user)
            logger.info(
                "Added user primer for profile '%s' with role '%s'",
                bundle.profile,
                self.prompt_user_role,
            )
        else:
            logger.debug("No user primer to add for profile '%s'", bundle.profile)
