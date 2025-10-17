from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from .config import Settings
from .local_agent import LocalAgent, ConversationMemory, OllamaModel
from .logging_config import get_logger
from .agentcore_app import chat_with_agent
from .prompt_loader import load_prompt_bundle

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
            self.prompt_bundle = load_prompt_bundle(settings)
            logger.info(
                "Loaded prompt profile '%s'%s",
                self.prompt_bundle.profile,
                " with user primer" if self.prompt_bundle.user else "",
            )
            if self.prompt_bundle.extras:
                logger.debug(
                    "Prompt extras discovered for profile '%s': %s",
                    self.prompt_bundle.profile,
                    ", ".join(sorted(self.prompt_bundle.extras.keys())),
                )

            self.agent = LocalAgent(
                self.model,
                self.memory,
                settings,
                prompt_bundle=self.prompt_bundle,
            )
            logger.info("Ollama backend initialized successfully")
            
        elif settings.backend_mode == "agentcore":
            logger.info("Setting up AgentCore backend with Strands framework")
            
            # Import here to set the provider for this session
            from .agentcore_app import set_provider
            
            # 
            set_provider()
            
            logger.debug(f"Ollama model: {settings.ollama_model}")
            logger.debug(f"Ollama base URL: {settings.ollama_base_url}")
            
            # Set agent to a special marker to indicate we're using agentcore
            self.agent = "agentcore"
            self.prompt_bundle = load_prompt_bundle(settings)
            logger.info(
                "Loaded prompt profile '%s'%s for AgentCore backend",
                self.prompt_bundle.profile,
                " with user primer" if self.prompt_bundle.user else "",
            )
            if self.prompt_bundle.extras:
                logger.debug(
                    "Prompt extras discovered for profile '%s': %s",
                    self.prompt_bundle.profile,
                    ", ".join(sorted(self.prompt_bundle.extras.keys())),
                )
            logger.info("AgentCore backend with Strands framework initialized successfully")
        else:
            error_msg = f"Unknown backend mode: {settings.backend_mode}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent using the configured backend."""
        logger.info("=" * 80)
        logger.debug(f"[AGENT CLIENT] Processing chat request: {user_message[:100]}...")
        logger.debug(f"[AGENT CLIENT] Backend mode: {self.settings.backend_mode}")
        
        if self.settings.backend_mode == "ollama" and isinstance(self.agent, LocalAgent):
            logger.debug("[AGENT CLIENT] Using LocalAgent framework for Ollama backend")
            # Use new LocalAgent framework
            chunk_count = 0
            async for chunk in self.agent.chat(user_message):
                chunk_count += 1
                logger.debug(f"[AGENT CLIENT] Received chunk {chunk_count}: {len(chunk)} characters")
                yield chunk
            logger.info(f"[AGENT CLIENT] Ollama chat completed: {chunk_count} chunks received")
            
        elif self.settings.backend_mode == "agentcore":
            logger.info("[AGENT CLIENT] Using AgentCore Strands framework")
            logger.info("=" * 80)
            # Use new AgentCore Strands framework
            try:
                logger.debug("[AGENT CLIENT] Calling chat_with_agent in thread...")
                response = await asyncio.to_thread(chat_with_agent, user_message)
                logger.info("=" * 80)
                logger.info(f"[AGENT CLIENT] ✅ AgentCore response received: {len(response)} characters")
                logger.debug(f"[AGENT CLIENT] Response preview: {response[:500]}...")
                
                if not response or not response.strip():
                    logger.error("[AGENT CLIENT] ❌ EMPTY RESPONSE from AgentCore!")
                    logger.error("[AGENT CLIENT] This is likely the issue - agent returned nothing")
                    yield "[Error: Agent returned empty response]"
                else:
                    yield response
            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"[AGENT CLIENT] ❌ AgentCore chat failed: {e}", exc_info=True)
                logger.error("=" * 80)
                raise
        else:
            error_msg = "Invalid backend configuration"
            logger.error(f"[AGENT CLIENT] {error_msg}: mode={self.settings.backend_mode}, agent={self.agent}")
            raise RuntimeError(error_msg)
        
        logger.info("=" * 80)

    def clear_memory(self) -> None:
        """Clear conversation memory if using LocalAgent."""
        logger.debug("Clearing conversation memory")
        if self.settings.backend_mode == "ollama" and isinstance(self.agent, LocalAgent):
            self.agent.clear_memory()
            self.prompt_bundle = self.agent.prompt_bundle
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

    def get_prompt_profile(self) -> str | None:
        """Return the active prompt profile for diagnostics."""
        if self.settings.backend_mode == "ollama":
            bundle = getattr(self, "prompt_bundle", None)
            return bundle.profile if bundle else None
        return None


async def collect_response(
    client: AgentClient, user_message: str, max_total_chars: int | None = None
) -> str:
    limit_text = f" (max chars: {max_total_chars})" if max_total_chars else ""
    logger.debug(
        f"Collecting response for message: {user_message[:100]}...{limit_text}"
    )

    parts: list[str] = []
    chunk_count = 0
    total_length = 0
    effective_limit = max_total_chars if max_total_chars and max_total_chars > 0 else None

    async for chunk in client.chat(user_message):
        chunk_count += 1
        parts.append(chunk)
        total_length += len(chunk)
        logger.debug(
            "Chunk %s: +%s chars, total: %s",
            chunk_count,
            len(chunk),
            total_length,
        )

        if effective_limit is not None and total_length >= effective_limit:
            logger.info(
                "Reached max total chars limit: %s/%s",
                total_length,
                effective_limit,
            )
            break

    response = "".join(parts)
    if effective_limit is not None and len(response) > effective_limit:
        response = response[:effective_limit]

    logger.info(
        "Response collection complete: %s characters from %s chunks",
        len(response),
        chunk_count,
    )
    return response
