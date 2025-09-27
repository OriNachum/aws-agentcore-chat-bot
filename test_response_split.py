#!/usr/bin/env python3
"""Unit tests for response splitting and message dispatch logic."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import discord

from community_bot.config import Settings
from community_bot.discord_bot import CommunityBot


def build_settings(max_chars: int = 120) -> Settings:
    return Settings(
        discord_token="test-token",
        discord_channel_id=12345,
        backend_mode="ollama",
        ollama_model="test-model",
        ollama_base_url="http://localhost:11434",
        max_response_chars=max_chars,
        memory_max_messages=5,
        system_prompt="Test system prompt",
        log_level="DEBUG",
    )


class SplitResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = CommunityBot(build_settings(), MagicMock())

    def test_single_chunk_returns_original_text(self):
        text = "Short response"
        chunks = self.bot._split_response(text)
        self.assertEqual(chunks, [text])

    def test_multichunk_prefers_newline_boundaries(self):
        bot = CommunityBot(build_settings(max_chars=40), MagicMock())
        text = "First paragraph.\nSecond paragraph that is quite a bit longer than the limit.\nThird line."
        chunks = bot._split_response(text)

        self.assertGreater(len(chunks), 1)
        # Ensure chunks respect limit and the second chunk starts with the continuation marker
        for chunk in chunks:
            self.assertLessEqual(len(chunk), bot.settings.max_response_chars)
        self.assertTrue(chunks[1].startswith("</ continuing>\n"))

    def test_hard_wrap_when_no_newline(self):
        bot = CommunityBot(build_settings(max_chars=30), MagicMock())
        text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunks = bot._split_response(text)

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), bot.settings.max_response_chars)
        # Reconstruct text without continuation markers to ensure full coverage
        reconstructed = chunks[0] + "".join(chunk.split("\n", 1)[1] if chunk.startswith("</ continuing>") else chunk for chunk in chunks[1:])
        self.assertEqual(reconstructed, text)

    def test_code_block_split_preserves_fences(self):
        bot = CommunityBot(build_settings(max_chars=80), MagicMock())
        text = (
            "Intro line.\n"
            "```python\n"
            "print('line one')\n"
            "print('line two with more characters')\n"
            "print('line three continues even further to force a split')\n"
            "```\n"
            "Outro line."
        )
        chunks = bot._split_response(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[0].rstrip().endswith("```"))
        self.assertTrue(chunks[1].startswith("</ continuing>\n```python"))
        for chunk in chunks:
            self.assertLessEqual(len(chunk), bot.settings.max_response_chars)

    def test_exact_limit_single_chunk(self):
        limit = 60
        bot = CommunityBot(build_settings(max_chars=limit), MagicMock())
        text = "x" * limit
        chunks = bot._split_response(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)


class MessageDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.settings = build_settings(max_chars=70)
        self.bot = CommunityBot(self.settings, MagicMock())

    async def asyncTearDown(self) -> None:
        await self.bot.close()

    @patch("community_bot.discord_bot.collect_response", new_callable=AsyncMock)
    async def test_on_message_sends_multiple_chunks(self, mock_collect_response: AsyncMock):
        long_response = (
            "Intro line that is slightly long to trigger splitting. "
            "```python\n"
            "print('first line of code')\n"
            "print('second line of code that continues beyond the limit for sure')\n"
            "print('third line still going strong')\n"
            "```\n"
            "And a final summary line to conclude."
        )
        mock_collect_response.return_value = long_response

        author = MagicMock()
        author.bot = False
        author.id = 999
        author.display_name = "Tester"

        channel = MagicMock()
        channel.id = self.settings.discord_channel_id

        message = MagicMock()
        message.author = author
        message.content = "Hello bot, please demonstrate splitting."
        message.channel = channel
        message.thread = None
        message.create_thread = AsyncMock()
        message.reply = AsyncMock()
        channel.fetch_message = AsyncMock(return_value=message)

        response_channel = MagicMock()
        response_channel.id = 99999
        response_channel.archived = False
        response_channel.join = AsyncMock()
        response_channel.edit = AsyncMock()
        thinking_message = MagicMock()
        thinking_message.edit = AsyncMock()
        response_channel.send = AsyncMock(return_value=thinking_message)
        message.create_thread.return_value = response_channel

        expected_chunks = self.bot._split_response(long_response)

        await self.bot.on_message(message)

        message.create_thread.assert_awaited_once()
        response_channel.join.assert_awaited_once()
        thinking_message.edit.assert_awaited_once_with(content=expected_chunks[0])

        # First send call is the placeholder, the rest should be follow-up chunks
        self.assertGreater(len(expected_chunks), 1)
        send_calls = response_channel.send.await_args_list
        self.assertEqual(send_calls[0].args[0], "Processing... 🤖")
        follow_up_payloads = [call.args[0] for call in send_calls[1:]]
        self.assertEqual(follow_up_payloads, expected_chunks[1:])

    # Ensure mock collect_response was invoked with the expected arguments
        mock_collect_response.assert_awaited_once()
        await_calls = mock_collect_response.await_args_list
        self.assertTrue(await_calls)
        self.assertEqual(await_calls[0].args[0], self.bot.agent_client)
        self.assertEqual(await_calls[0].args[1], message.content)
        self.assertEqual(len(await_calls[0].args), 2)
        channel.fetch_message.assert_awaited_once()
        message.reply.assert_not_awaited()

    @patch("community_bot.discord_bot.collect_response", new_callable=AsyncMock)
    async def test_on_message_reuses_existing_thread(self, mock_collect_response: AsyncMock):
        mock_collect_response.return_value = "Short response"

        author = MagicMock()
        author.bot = False
        author.id = 321
        author.display_name = "Tester"

        existing_thread = MagicMock(spec=discord.Thread)
        existing_thread.id = 555
        existing_thread.archived = False
        existing_thread.join = AsyncMock()
        existing_thread.edit = AsyncMock()

        placeholder_message = MagicMock()
        placeholder_message.edit = AsyncMock()
        existing_thread.send = AsyncMock(return_value=placeholder_message)

        channel = MagicMock()
        channel.id = self.settings.discord_channel_id
        channel.fetch_message = AsyncMock(return_value=MagicMock(thread=existing_thread))

        message = MagicMock()
        message.author = author
        message.content = "Hello again"
        message.channel = channel
        message.thread = existing_thread
        message.create_thread = AsyncMock()
        message.reply = AsyncMock()

        expected_chunks = self.bot._split_response("Short response")

        await self.bot.on_message(message)

        message.create_thread.assert_not_awaited()
        existing_thread.join.assert_awaited_once()
        existing_thread.send.assert_awaited_once_with("Processing... 🤖")
        placeholder_message.edit.assert_awaited_once_with(content=expected_chunks[0])
        mock_collect_response.assert_awaited_once()
        message.reply.assert_not_awaited()
        channel.fetch_message.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
