from __future__ import annotations

from typing import AsyncGenerator

from .config import Settings
from .local_agent import LocalAgent, ConversationMemory, OllamaModel
from .logging_config import get_logger
from .agentcore_app import chat_with_agent

logger = get_logger("community_bot.agent")


class AgentClient:
    """Entry point for the LocalAgent framework with backward compatibility."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        logger.info(f"Initializing AgentClient with backend mode: {settings.backend_mode}")
        
        # Initialize LocalAgent components
        if settings.backend_mode == "ollama":
            logger.info("Setting up Ollama backend")
            logger.debug(f"Ollama model: {settings.ollama_model}")
            logger.debug(f"Ollama base URL: {settings.ollama_base_url}")
            logger.debug(f"Memory max messages: {settings.memory_max_messages}")
            
            self.model = OllamaModel(settings)
            self.memory = ConversationMemory(max_messages=settings.memory_max_messages)
            self.agent = LocalAgent(
                self.model, 
                self.memory, 
                system_prompt=settings.system_prompt or "You are a helpful Discord community assistant."
            )
            logger.info("Ollama backend initialized successfully")
            
        elif settings.backend_mode == "agentcore":
            logger.info("Setting up AgentCore backend with Strands framework")
            
            # Import here to set the provider for this session
            from .agentcore_app import set_provider
            
            # Force the agentcore_app to use Ollama with our settings
            set_provider("ollama")
            
            logger.debug(f"Ollama model: {settings.ollama_model}")
            logger.debug(f"Ollama base URL: {settings.ollama_base_url}")
            
            # Set agent to a special marker to indicate we're using agentcore
            self.agent = "agentcore"
            logger.info("AgentCore backend with Strands framework initialized successfully")
        else:
            error_msg = f"Unknown backend mode: {settings.backend_mode}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent using the configured backend."""
        logger.debug(f"Processing chat request: {user_message[:100]}...")
        
        if self.settings.backend_mode == "ollama" and isinstance(self.agent, LocalAgent):
            logger.debug("Using LocalAgent framework for Ollama backend")
            # Use new LocalAgent framework
            chunk_count = 0
            async for chunk in self.agent.chat(user_message):
                chunk_count += 1
                logger.debug(f"Received chunk {chunk_count}: {len(chunk)} characters")
                yield chunk
            logger.info(f"Ollama chat completed: {chunk_count} chunks received")
            
        elif self.settings.backend_mode == "agentcore":
            logger.debug("Using new AgentCore Strands framework")
            # Use new AgentCore Strands framework
            try:
                response = chat_with_agent(user_message)
                logger.info(f"AgentCore response received: {len(response)} characters")
                yield response
            except Exception as e:
                logger.error(f"AgentCore chat failed: {e}", exc_info=True)
                raise
        else:
            error_msg = "Invalid backend configuration"
            logger.error(f"{error_msg}: mode={self.settings.backend_mode}, agent={self.agent}")
            raise RuntimeError(error_msg)

    def clear_memory(self) -> None:
        """Clear conversation memory if using LocalAgent."""
        logger.debug("Clearing conversation memory")
        if self.settings.backend_mode == "ollama" and isinstance(self.agent, LocalAgent):
            self.agent.clear_memory()
            logger.info("Conversation memory cleared successfully")
        else:
            logger.debug("No memory to clear (AgentCore mode or no agent)")
    
    def get_memory_size(self) -> int:
        """Get current memory size if using LocalAgent."""
        if self.settings.backend_mode == "ollama" and isinstance(self.agent, LocalAgent):
            size = self.agent.get_memory_size()
            logger.debug(f"Current memory size: {size} messages")
            return size
        logger.debug("Memory size not available (AgentCore mode or no agent)")
        return 0


async def collect_response(client: AgentClient, user_message: str, max_chars: int) -> str:
    logger.debug(f"Collecting response for message: {user_message[:100]}... (max chars: {max_chars})")
    parts = []
    chunk_count = 0
    
    async for chunk in client.chat(user_message):
        chunk_count += 1
        parts.append(chunk)
        current_length = sum(len(p) for p in parts)
        logger.debug(f"Chunk {chunk_count}: +{len(chunk)} chars, total: {current_length}")
        
        if current_length >= max_chars:
            logger.info(f"Reached max chars limit: {current_length}/{max_chars}")
            break
    
    response = "".join(parts)[:max_chars]
    logger.info(f"Response collection complete: {len(response)} characters from {chunk_count} chunks")
    return response
