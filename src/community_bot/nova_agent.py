"""Nova-based agent with conversation memory and KB integration."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from .config import Settings
from .nova_model import NovaModel
from .logging_config import get_logger
from .prompt_loader import PromptBundle

logger = get_logger("community_bot.nova_agent")


class ConversationMemory:
    """Simple conversation memory for Nova agent."""
    
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.messages: list[dict] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to memory."""
        self.messages.append({"role": role, "content": content})
        
        # Keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            logger.debug(f"Trimmed memory to {self.max_messages} messages")
    
    def get_context(self) -> list[dict]:
        """Get conversation history."""
        return self.messages.copy()
    
    def clear(self):
        """Clear conversation history."""
        self.messages.clear()
        logger.info("Conversation memory cleared")


class NovaAgent:
    """Agent implementation using AWS Bedrock Nova-Pro."""
    
    def __init__(
        self,
        settings: Settings,
        prompt_bundle: PromptBundle,
    ):
        """Initialize Nova agent.
        
        Args:
            settings: Application settings
            prompt_bundle: Loaded prompt bundle
        """
        self.settings = settings
        self.prompt_bundle = prompt_bundle
        
        # Initialize Nova model
        self.model = NovaModel(
            model_id=settings.nova_model_id,
            region=settings.aws_region or "us-east-1",
            temperature=settings.nova_temperature,
            max_tokens=settings.nova_max_tokens,
            top_p=settings.nova_top_p,
        )
        
        # Initialize conversation memory
        self.memory = ConversationMemory(max_messages=settings.memory_max_messages)
        
        logger.info("Nova agent initialized successfully")
    
    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process user message and stream response.
        
        Args:
            user_message: The user's message
            
        Yields:
            Response chunks from Nova
        """
        logger.info(f"[NOVA AGENT] Processing message: {user_message[:100]}...")
        
        # Add user message to memory
        self.memory.add_message("user", user_message)
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Get conversation context
        messages = self.memory.get_context()
        
        logger.debug(f"[NOVA AGENT] System prompt length: {len(system_prompt)} chars")
        logger.debug(f"[NOVA AGENT] Message count: {len(messages)}")
        
        # Stream response from Nova
        response_text = ""
        async for chunk in self.model.generate_streaming(messages, system_prompt):
            response_text += chunk
            yield chunk
        
        # Add assistant response to memory
        self.memory.add_message("assistant", response_text)
        
        logger.info(f"[NOVA AGENT] Response complete: {len(response_text)} characters")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from prompt bundle.
        
        Returns:
            Complete system prompt
        """
        sections = []
        
        # Add system prompt from bundle
        if self.prompt_bundle.system:
            sections.append(self.prompt_bundle.system)
        
        # Add custom system prompt override if provided
        if self.settings.system_prompt:
            sections.append(self.settings.system_prompt)
        
        # Add user primer if available
        if self.prompt_bundle.user:
            sections.append(f"User context:\n{self.prompt_bundle.user}")
        
        # Add extras if available
        if self.prompt_bundle.extras:
            for key, value in self.prompt_bundle.extras.items():
                sections.append(f"{key}:\n{value}")
        
        return "\n\n".join(sections)
    
    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.memory.clear()
    
    def get_memory_size(self) -> int:
        """Get current memory size."""
        return len(self.memory.messages)
