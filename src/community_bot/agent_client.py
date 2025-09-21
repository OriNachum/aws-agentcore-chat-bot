from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

import aiohttp
import backoff

try:
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - optional when using ollama only
    boto3 = None  # type: ignore

from .config import Settings
from .local_agent import LocalAgent, ConversationMemory, OllamaModel
from .logging_config import get_logger

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
            logger.info("Setting up AgentCore backend")
            if boto3 is None:
                error_msg = "boto3 is required for AgentCore backend mode"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.debug(f"AWS region: {settings.aws_region}")
            logger.debug(f"Agent ID: {settings.agent_id}")
            logger.debug(f"Agent alias ID: {settings.agent_alias_id}")
            
            # For AgentCore mode, we'll still use the legacy implementation
            # This maintains backward compatibility while the new architecture is being developed
            self.agent = None
            logger.info("AgentCore backend initialized successfully")
        else:
            error_msg = f"Unknown backend mode: {settings.backend_mode}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent using the configured backend."""
        logger.debug(f"Processing chat request: {user_message[:100]}...")
        
        if self.settings.backend_mode == "ollama" and self.agent:
            logger.debug("Using LocalAgent framework for Ollama backend")
            # Use new LocalAgent framework
            chunk_count = 0
            async for chunk in self.agent.chat(user_message):
                chunk_count += 1
                logger.debug(f"Received chunk {chunk_count}: {len(chunk)} characters")
                yield chunk
            logger.info(f"Ollama chat completed: {chunk_count} chunks received")
            
        elif self.settings.backend_mode == "agentcore":
            logger.debug("Using legacy AgentCore implementation")
            # Use legacy AgentCore implementation
            chunk_count = 0
            async for chunk in self._chat_agentcore(user_message):
                chunk_count += 1
                logger.debug(f"Received AgentCore chunk {chunk_count}: {len(chunk)} characters")
                yield chunk
            logger.info(f"AgentCore chat completed: {chunk_count} chunks received")
        else:
            error_msg = "Invalid backend configuration"
            logger.error(f"{error_msg}: mode={self.settings.backend_mode}, agent={self.agent}")
            raise RuntimeError(error_msg)

    async def _chat_agentcore(self, user_message: str) -> AsyncGenerator[str, None]:
        """Legacy AgentCore implementation for backward compatibility."""
        logger.debug("Starting AgentCore invocation")
        # Placeholder implementation; AWS AgentCore Python SDK specifics may differ.
        # We'll call Bedrock runtime / AgentRuntime via boto3's bedrock-agent-runtime client.
        loop = asyncio.get_event_loop()
        try:
            response_text = await loop.run_in_executor(None, self._invoke_agent_sync, user_message)
            logger.info(f"AgentCore response received: {len(response_text)} characters")
            yield response_text
        except Exception as e:
            logger.error(f"AgentCore invocation failed: {e}", exc_info=True)
            raise

    def _invoke_agent_sync(self, user_message: str) -> str:
        """Synchronous AgentCore invocation for legacy support."""
        logger.debug("Creating boto3 bedrock-agent-runtime client")
        
        if boto3 is None:
            error_msg = "boto3 is not available"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        client = boto3.client("bedrock-agent-runtime", region_name=self.settings.aws_region)
        
        # Basic invocation; adjust per actual AgentCore API (pseudo example based on docs pattern)
        kwargs = {
            "agentId": self.settings.agent_id,
            "agentAliasId": self.settings.agent_alias_id,
            "sessionId": "discord-session",  # for simplicity; could map per channel/user
            "inputText": user_message,
        }
        
        logger.debug(f"Invoking agent with ID: {self.settings.agent_id}")
        logger.debug(f"Agent alias ID: {self.settings.agent_alias_id}")
        
        # Knowledge base is attached to agent configuration; no need to pass explicitly unless using direct KB query.
        resp = client.invoke_agent(**kwargs)
        logger.debug("Agent invocation completed")
        
        # The response may be streaming; in full implementation we would parse the event stream.
        # For now assume 'completion' in a JSON body or text block.
        # If 'completion' not present, fallback to raw str.
        if "completion" in resp:
            return resp["completion"]
        body = resp.get("body")
        if body:
            try:
                raw = body.read().decode("utf-8")
                j = json.loads(raw)
                return j.get("completion") or raw
            except Exception:
                return str(body)
        return json.dumps(resp)[:4000]
    
    def clear_memory(self) -> None:
        """Clear conversation memory if using LocalAgent."""
        logger.debug("Clearing conversation memory")
        if self.agent and hasattr(self.agent, 'clear_memory'):
            self.agent.clear_memory()
            logger.info("Conversation memory cleared successfully")
        else:
            logger.debug("No memory to clear (AgentCore mode or no agent)")
    
    def get_memory_size(self) -> int:
        """Get current memory size if using LocalAgent."""
        if self.agent and hasattr(self.agent, 'get_memory_size'):
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
