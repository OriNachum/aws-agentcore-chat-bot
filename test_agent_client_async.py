#!/usr/bin/env python3
"""Tests ensuring AgentClient handles blocking AgentCore calls asynchronously."""

import sys
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from community_bot.config import Settings
from community_bot.agent_client import AgentClient, chat_with_agent, collect_response


def build_agentcore_settings() -> Settings:
    return Settings(
        discord_token="token",
        discord_channel_id=1,
        backend_mode="agentcore",
        aws_region="us-east-1",
        agent_id="agent",
        agent_alias_id="alias",
        knowledge_base_id=None,
        ollama_model="mini",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1200,
        memory_max_messages=10,
        system_prompt=None,
        log_level="DEBUG",
    )


class AgentCoreChatAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_runs_in_background_thread(self):
        settings = build_agentcore_settings()

        # Patch provider setup to avoid touching external services during instantiation
        with patch("community_bot.agentcore_app.set_provider"):
            client = AgentClient(settings)

        async def fake_to_thread(func, *args, **kwargs):
            self.assertIs(func, chat_with_agent)
            self.assertEqual(args, ("hello",))
            return "agentcore-response"

        with patch("community_bot.agent_client.asyncio.to_thread", new=AsyncMock(side_effect=fake_to_thread)) as mock_to_thread:
            chunks = []
            async for chunk in client.chat("hello"):
                chunks.append(chunk)

        self.assertEqual(chunks, ["agentcore-response"])
        mock_to_thread.assert_awaited_once()


class CollectResponseTests(unittest.IsolatedAsyncioTestCase):
    class _DummyClient:
        def __init__(self, chunks):
            self._chunks = chunks

        async def chat(self, user_message):  # type: ignore[override]
            for chunk in self._chunks:
                yield chunk

    async def test_collect_response_accumulates_all_chunks_without_limit(self):
        chunks = ["first ", "second ", "third"]
        client = self._DummyClient(chunks)
        response = await collect_response(cast(AgentClient, client), "prompt")
        self.assertEqual(response, "".join(chunks))

    async def test_collect_response_honors_total_limit(self):
        chunks = ["alpha", "beta", "gamma"]
        client = self._DummyClient(chunks)
        response = await collect_response(
            cast(AgentClient, client),
            "prompt",
            max_total_chars=7,
        )
        self.assertEqual(response, "alphabet"[:7])


if __name__ == "__main__":
    unittest.main()
