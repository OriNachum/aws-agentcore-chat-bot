from __future__ import annotations

import asyncio

import discord

from .config import Settings
from .agent_client import AgentClient, collect_response
from .logging_config import get_logger

logger = get_logger("community_bot.discord")


class CommunityBot(discord.Client):
    def __init__(self, settings: Settings, agent_client: AgentClient):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.agent_client = agent_client
        
        logger.info(f"Initializing Discord bot with channel ID: {settings.discord_channel_id}")
        logger.info(f"Backend mode: {settings.backend_mode}")
        logger.debug(f"Max response chars: {settings.max_response_chars}")

    async def on_ready(self):
        logger.info(f"Bot successfully logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is connected to {len(self.guilds)} guild(s)")
        logger.info(f"Monitoring channel ID: {self.settings.discord_channel_id}")
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        logger.debug(f"Received message from {message.author} in channel {message.channel.id}: {message.content[:100]}...")
        
        # Check if message is from a bot
        if message.author.bot:
            logger.debug(f"Ignoring bot message from {message.author}")
            return
            
        # Check if message is in the correct channel
        if message.channel.id != self.settings.discord_channel_id:
            logger.debug(f"Ignoring message from non-monitored channel {message.channel.id}")
            return

        logger.info(f"Processing message from {message.author} ({message.author.id}): {message.content[:100]}...")
        
        # Send thinking message
        thinking_msg = await message.channel.send("Processing... 🤖")
        logger.debug("Sent 'Processing...' message")
        
        try:
            logger.debug("Calling agent client to process message")
            response_text = await collect_response(
                self.agent_client, message.content, self.settings.max_response_chars
            )
            logger.info(f"Received response from agent: {len(response_text)} characters")
            logger.debug(f"Response preview: {response_text[:200]}...")
            
        except Exception as e:
            error_msg = f"Error contacting AI backend: {e}"
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            await thinking_msg.edit(content=error_msg)
            return

        # Send the response
        final_response = self._truncate(response_text)
        logger.debug(f"Sending final response: {len(final_response)} characters")
        await thinking_msg.edit(content=final_response)
        logger.info(f"Successfully responded to message from {message.author}")

    def _truncate(self, text: str) -> str:
        limit = self.settings.max_response_chars
        if len(text) <= limit:
            logger.debug(f"Response within limit: {len(text)}/{limit} characters")
            return text
        else:
            truncated = text[: limit - 10] + "… (truncated)"
            logger.warning(f"Response truncated: {len(text)} -> {len(truncated)} characters")
            return truncated
