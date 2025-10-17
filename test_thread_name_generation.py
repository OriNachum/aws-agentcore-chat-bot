#!/usr/bin/env python3
"""Unit tests for AI-generated thread names."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from community_bot.config import Settings
from community_bot.discord_bot import CommunityBot
from community_bot.agent_client import AgentClient


def build_settings() -> Settings:
    return Settings(
        discord_token="test-token",
        discord_channel_id=12345,
        backend_mode="ollama",
        ollama_model="test-model",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=5,
        system_prompt="Test system prompt",
        log_level="DEBUG",
    )


class ThreadNameGenerationTests(unittest.IsolatedAsyncioTestCase):
    """Test the AI-powered thread name generation feature."""

    def setUp(self) -> None:
        self.settings = build_settings()
        self.agent_client = MagicMock(spec=AgentClient)
        self.bot = CommunityBot(self.settings, self.agent_client)

    async def test_generate_thread_name_basic(self):
        """Test basic thread name generation with a simple message."""
        # Mock the agent's response
        async def mock_chat(prompt):
            yield "Python Decorators Discussion"
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "Can you explain Python decorators?",
            "TestUser"
        )
        
        self.assertEqual(result, "Python Decorators Discussion")

    async def test_generate_thread_name_strips_quotes(self):
        """Test that generated names have quotes stripped."""
        async def mock_chat(prompt):
            yield '"Machine Learning Basics"'
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "What is machine learning?",
            "TestUser"
        )
        
        self.assertEqual(result, "Machine Learning Basics")

    async def test_generate_thread_name_truncates_long_names(self):
        """Test that thread names longer than 100 chars are truncated."""
        long_name = "A" * 105
        
        async def mock_chat(prompt):
            yield long_name
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "Some very long question...",
            "TestUser"
        )
        
        self.assertEqual(len(result), 100)
        self.assertTrue(result.endswith("..."))

    async def test_generate_thread_name_handles_empty_response(self):
        """Test fallback when agent returns empty response."""
        async def mock_chat(prompt):
            yield ""
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "Some question",
            "TestUser"
        )
        
        self.assertEqual(result, "Chat with TestUser")

    async def test_generate_thread_name_handles_exception(self):
        """Test fallback when agent throws an exception."""
        async def mock_chat(prompt):
            raise Exception("API Error")
            yield  # Make it a generator
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "Some question",
            "TestUser"
        )
        
        self.assertEqual(result, "Chat with TestUser")

    async def test_generate_thread_name_with_multiline_response(self):
        """Test that multiline responses are cleaned up properly."""
        async def mock_chat(prompt):
            yield "Deep Learning Concepts\n\nThis is a great topic!"
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "Tell me about deep learning",
            "TestUser"
        )
        
        # Should only take the first line
        self.assertEqual(result, "Deep Learning Concepts")

    async def test_generate_thread_name_handles_chunks(self):
        """Test that chunked responses are properly assembled."""
        async def mock_chat(prompt):
            yield "Neural"
            yield " Network"
            yield " Training"
        
        self.agent_client.chat = mock_chat
        
        result = await self.bot._generate_thread_name(
            "How to train neural networks?",
            "TestUser"
        )
        
        self.assertEqual(result, "Neural Network Training")


if __name__ == "__main__":
    unittest.main()
