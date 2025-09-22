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
        user_id = self.user.id if self.user else "Unknown"
        user_name = str(self.user) if self.user else "Unknown"
        logger.info(f"Bot successfully logged in as {user_name} (ID: {user_id})")
        logger.info(f"Bot is connected to {len(self.guilds)} guild(s)")
        logger.info(f"Monitoring channel ID: {self.settings.discord_channel_id}")
        print(f"Logged in as {user_name} (ID: {user_id})")

    async def on_message(self, message: discord.Message):
        logger.debug(f"Received message from {message.author} in channel {message.channel.id}: {message.content[:100]}...")
        
        # Check if message is from a bot
        if message.author.bot:
            logger.debug(f"Ignoring bot message from {message.author}")
            return
            
        # Check if message is in the correct channel or a thread from the correct channel
        is_target_channel = message.channel.id == self.settings.discord_channel_id
        is_thread_from_target = (
            isinstance(message.channel, discord.Thread) and 
            message.channel.parent_id == self.settings.discord_channel_id
        )
        
        if not (is_target_channel or is_thread_from_target):
            logger.debug(f"Ignoring message from non-monitored channel/thread {message.channel.id}")
            return

        logger.info(f"Processing message from {message.author} ({message.author.id}): {message.content[:100]}...")
        
        # Determine response context and location
        response_channel = message.channel
        thread_history = ""
        
        if isinstance(message.channel, discord.Thread):
            # We're in a thread - collect history and respond in the same thread
            logger.debug(f"Message is in thread: {message.channel.name}")
            thread_history = await self._get_thread_history(message.channel)
            thinking_msg = await message.channel.send("Processing... 🤖")
        else:
            # We're in the main channel - create a new thread for the response
            logger.debug("Message is in main channel - will create thread")
            thread_name = f"Chat with {message.author.display_name}"
            if len(message.content) > 50:
                thread_name = f"Re: {message.content[:50]}..."
            
            # Create thread from the user's message
            response_channel = await message.create_thread(name=thread_name)
            thinking_msg = await response_channel.send("Processing... 🤖")
            logger.debug(f"Created thread: {thread_name}")
        
        try:
            logger.debug("Calling agent client to process message")
            # Include thread history if available
            context_message = message.content
            if thread_history:
                context_message = f"Previous conversation:\n{thread_history}\n\nNew message: {message.content}"
                logger.debug(f"Including thread history: {len(thread_history)} characters")
            
            response_text = await collect_response(
                self.agent_client, context_message, self.settings.max_response_chars
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

    async def _get_thread_history(self, thread: discord.Thread, max_messages: int = 10) -> str:
        """Collect recent messages from a thread to provide context."""
        try:
            logger.debug(f"Collecting thread history from {thread.name} (max {max_messages} messages)")
            messages = []
            
            # Get recent messages from the thread (excluding bot messages)
            async for msg in thread.history(limit=max_messages, oldest_first=True):
                if not msg.author.bot and msg.content.strip():
                    timestamp = msg.created_at.strftime("%H:%M")
                    messages.append(f"[{timestamp}] {msg.author.display_name}: {msg.content}")
            
            if messages:
                history = "\n".join(messages)
                logger.debug(f"Collected {len(messages)} messages from thread history")
                return history
            else:
                logger.debug("No relevant messages found in thread history")
                return ""
                
        except Exception as e:
            logger.error(f"Error collecting thread history: {e}")
            return ""

    def _truncate(self, text: str) -> str:
        limit = self.settings.max_response_chars
        if len(text) <= limit:
            logger.debug(f"Response within limit: {len(text)}/{limit} characters")
            return text
        else:
            truncated = text[: limit - 10] + "… (truncated)"
            logger.warning(f"Response truncated: {len(text)} -> {len(truncated)} characters")
            return truncated
