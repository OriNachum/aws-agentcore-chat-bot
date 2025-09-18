from __future__ import annotations

import asyncio

import discord

from .config import Settings
from .agent_client import AgentClient, collect_response


class CommunityBot(discord.Client):
    def __init__(self, settings: Settings, agent_client: AgentClient):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.agent_client = agent_client

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id != self.settings.discord_channel_id:
            return

        thinking_msg = await message.channel.send("Processing... 🤖")
        try:
            response_text = await collect_response(
                self.agent_client, message.content, self.settings.max_response_chars
            )
        except Exception as e:
            await thinking_msg.edit(content=f"Error contacting AI backend: {e}")
            return

        await thinking_msg.edit(content=self._truncate(response_text))

    def _truncate(self, text: str) -> str:
        limit = self.settings.max_response_chars
        return text if len(text) <= limit else text[: limit - 10] + "… (truncated)"
