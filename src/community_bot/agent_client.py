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


class AgentClient:
    """Entry point for the LocalAgent framework with backward compatibility."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize LocalAgent components
        if settings.backend_mode == "ollama":
            self.model = OllamaModel(settings)
            self.memory = ConversationMemory(max_messages=settings.memory_max_messages)
            self.agent = LocalAgent(self.model, self.memory, system_prompt=settings.system_prompt)
        elif settings.backend_mode == "agentcore":
            if boto3 is None:
                raise RuntimeError("boto3 is required for AgentCore backend mode")
            # For AgentCore mode, we'll still use the legacy implementation
            # This maintains backward compatibility while the new architecture is being developed
            self.agent = None
        else:
            raise ValueError(f"Unknown backend mode: {settings.backend_mode}")

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent using the configured backend."""
        if self.settings.backend_mode == "ollama" and self.agent:
            # Use new LocalAgent framework
            async for chunk in self.agent.chat(user_message):
                yield chunk
        elif self.settings.backend_mode == "agentcore":
            # Use legacy AgentCore implementation
            async for chunk in self._chat_agentcore(user_message):
                yield chunk
        else:
            raise RuntimeError("Invalid backend configuration")

    async def _chat_agentcore(self, user_message: str) -> AsyncGenerator[str, None]:
        """Legacy AgentCore implementation for backward compatibility."""
        # Placeholder implementation; AWS AgentCore Python SDK specifics may differ.
        # We'll call Bedrock runtime / AgentRuntime via boto3's bedrock-agent-runtime client.
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(None, self._invoke_agent_sync, user_message)
        yield response_text

    def _invoke_agent_sync(self, user_message: str) -> str:
        """Synchronous AgentCore invocation for legacy support."""
        client = boto3.client("bedrock-agent-runtime", region_name=self.settings.aws_region)
        # Basic invocation; adjust per actual AgentCore API (pseudo example based on docs pattern)
        kwargs = {
            "agentId": self.settings.agent_id,
            "agentAliasId": self.settings.agent_alias_id,
            "sessionId": "discord-session",  # for simplicity; could map per channel/user
            "inputText": user_message,
        }
        # Knowledge base is attached to agent configuration; no need to pass explicitly unless using direct KB query.
        resp = client.invoke_agent(**kwargs)
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
        if self.agent and hasattr(self.agent, 'clear_memory'):
            self.agent.clear_memory()
    
    def get_memory_size(self) -> int:
        """Get current memory size if using LocalAgent."""
        if self.agent and hasattr(self.agent, 'get_memory_size'):
            return self.agent.get_memory_size()
        return 0


async def collect_response(client: AgentClient, user_message: str, max_chars: int) -> str:
    parts = []
    async for chunk in client.chat(user_message):
        parts.append(chunk)
        if sum(len(p) for p in parts) >= max_chars:
            break
    return "".join(parts)[:max_chars]
