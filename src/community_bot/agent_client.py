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


class AgentClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.backend_mode == "agentcore" and boto3 is None:
            raise RuntimeError("boto3 is required for AgentCore backend mode")

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        if self.settings.backend_mode == "agentcore":
            async for chunk in self._chat_agentcore(user_message):
                yield chunk
        else:
            async for chunk in self._chat_ollama(user_message):
                yield chunk

    async def _chat_ollama(self, user_message: str) -> AsyncGenerator[str, None]:
        url = f"{self.settings.ollama_base_url}/api/chat"
        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant for a Discord community."},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                async for line_bytes in resp.content:
                    if not line_bytes:
                        continue
                    try:
                        line = line_bytes.decode("utf-8").strip()
                        if not line:
                            continue
                        data = json.loads(line)
                        if data.get("done"):
                            break
                        message = data.get("message", {})
                        content = message.get("content")
                        if content:
                            yield content
                    except Exception:
                        continue

    async def _chat_agentcore(self, user_message: str) -> AsyncGenerator[str, None]:
        # Placeholder implementation; AWS AgentCore Python SDK specifics may differ.
        # We'll call Bedrock runtime / AgentRuntime via boto3's bedrock-agent-runtime client.
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(None, self._invoke_agent_sync, user_message)
        yield response_text

    def _invoke_agent_sync(self, user_message: str) -> str:
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


async def collect_response(client: AgentClient, user_message: str, max_chars: int) -> str:
    parts = []
    async for chunk in client.chat(user_message):
        parts.append(chunk)
        if sum(len(p) for p in parts) >= max_chars:
            break
    return "".join(parts)[:max_chars]
