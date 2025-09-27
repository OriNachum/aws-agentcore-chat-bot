from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any, Awaitable, List, Tuple, cast

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
            await self._prepare_thread(message.channel)
            thinking_msg = await message.channel.send("Processing... 🤖")
        else:
            # We're in the main channel - create (or reuse) a thread for the response
            logger.debug("Message is in main channel - will create (or reuse) thread")
            thread_name = f"Chat with {message.author.display_name}"
            if len(message.content) > 50:
                thread_name = f"Re: {message.content[:50]}..."

            existing_thread = await self._resolve_existing_thread(message)
            if existing_thread:
                response_channel = existing_thread
                logger.info(
                    "Reusing existing thread for message",
                    extra={"thread_id": existing_thread.id, "message_id": message.id},
                )
            else:
                try:
                    response_channel = await message.create_thread(name=thread_name)
                    logger.debug(f"Created thread: {thread_name}")
                except discord.HTTPException as exc:
                    if exc.code == 160004:
                        logger.info(
                            "Thread already exists; attempting to reuse",
                            extra={"message_id": message.id},
                        )
                        response_channel = await self._resolve_existing_thread(message)
                        if not response_channel:
                            logger.error(
                                "Thread already existed but could not be resolved",
                                extra={"message_id": message.id},
                                exc_info=True,
                            )
                            await message.reply(
                                "I already have a thread for this message but couldn't reopen it."
                                " Please continue in the existing thread."
                            )
                            return
                    else:
                        logger.error(
                            f"Failed to create thread: {exc}",
                            extra={"message_id": message.id},
                            exc_info=True,
                        )
                        await message.reply(
                            "Sorry, I couldn't start a thread for this conversation."
                            " Please try again in a moment."
                        )
                        return

            await self._prepare_thread(response_channel)
            thinking_msg = await response_channel.send("Processing... 🤖")
        
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
        chunks = self._split_response(response_text)
        if not chunks:
            logger.warning("Split response returned no chunks; falling back to empty response")
            chunks = [""]

        logger.info(
            "Dispatching response", extra={
                "total_chunks": len(chunks),
                "total_characters": sum(len(chunk) for chunk in chunks),
            }
        )

        await thinking_msg.edit(content=chunks[0])
        logger.debug(
            "Updated placeholder message with first chunk",
            extra={"chunk_index": 1, "chunk_size": len(chunks[0])},
        )

        for idx, chunk in enumerate(chunks[1:], start=2):
            await response_channel.send(chunk)
            logger.debug(
                "Sent follow-up chunk",
                extra={"chunk_index": idx, "chunk_size": len(chunk)},
            )

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

    def _split_response(self, text: str) -> List[str]:
        limit = self.settings.max_response_chars
        if limit <= 0:
            logger.error("Max response chars must be positive to split responses")
            return [text]

        if len(text) <= limit:
            logger.debug(
                "Response within single-chunk limit",
                extra={"length": len(text), "limit": limit},
            )
            return [text]

        logger.debug(
            "Splitting response into chunks",
            extra={"total_length": len(text), "limit": limit},
        )

        chunks: List[str] = []
        start: int = 0
        in_code_block = False
        code_block_lang: str = ""
        pending_reopen: str | None = None

        while start < len(text):
            prefix = "" if not chunks else "</ continuing>\n"
            reopen = ""
            if pending_reopen is not None:
                reopen = f"```{pending_reopen}\n" if pending_reopen else "```\n"
                logger.debug(
                    "Reopening code block for continued chunk",
                    extra={"language": pending_reopen or "plain"},
                )

            available = limit - len(prefix) - len(reopen)
            if available <= 0:
                logger.error(
                    "Insufficient space for additional chunk",
                    extra={"limit": limit, "prefix_len": len(prefix), "reopen_len": len(reopen)},
                )
                chunks.append(prefix + reopen)
                break

            max_offset = min(len(text) - start, available)
            sub_text = text[start : start + max_offset]
            candidate_offsets = [pos for pos, char in enumerate(sub_text, start=1) if char == "\n"]
            if max_offset > 0:
                candidate_offsets.append(max_offset)

            chosen_chunk: str | None = None
            chosen_end: int = start
            chosen_pending: str | None = None
            chosen_transitions: List[Tuple[str, str, int]] = []
            chosen_state: Tuple[bool, str] = (in_code_block, code_block_lang)

            for offset in reversed(candidate_offsets):
                if offset <= 0:
                    continue

                end = start + offset
                segment = text[start:end]
                state, transitions = self._process_code_fences(
                    segment, start, in_code_block, code_block_lang
                )
                segment_in_code, segment_lang = state

                closing = ""
                pending = None
                if end < len(text) and segment_in_code:
                    closing = "```" if segment.endswith("\n") else "\n```"
                    pending = segment_lang

                payload_len = len(segment) + len(closing)
                if payload_len <= available:
                    chosen_chunk = prefix + reopen + segment + closing
                    chosen_end = end
                    chosen_pending = pending
                    chosen_transitions = transitions
                    chosen_state = (segment_in_code, segment_lang)
                    break

            if chosen_chunk is None:
                fallback_offset = max_offset
                while fallback_offset > 0:
                    end = start + fallback_offset
                    segment = text[start:end]
                    state, transitions = self._process_code_fences(
                        segment, start, in_code_block, code_block_lang
                    )
                    segment_in_code, segment_lang = state
                    closing = ""
                    pending = None
                    if end < len(text) and segment_in_code:
                        closing = "```" if segment.endswith("\n") else "\n```"
                        pending = segment_lang

                    payload_len = len(segment) + len(closing)
                    if payload_len <= available:
                        chosen_chunk = prefix + reopen + segment + closing
                        chosen_end = end
                        chosen_pending = pending
                        chosen_transitions = transitions
                        chosen_state = (segment_in_code, segment_lang)
                        break

                    fallback_offset -= 1

                if chosen_chunk is None:
                    chosen_chunk = prefix + reopen

            if chosen_chunk is None:
                chosen_chunk = prefix + reopen

            chunks.append(chosen_chunk)
            logger.debug(
                "Prepared response chunk",
                extra={
                    "chunk_index": len(chunks),
                    "chunk_size": len(chosen_chunk),
                    "starts_with_prefix": bool(prefix),
                    "reopens_code_block": bool(reopen),
                    "pending_code_block": bool(chosen_pending),
                },
            )

            for transition_type, language, abs_pos in chosen_transitions:
                logger.debug(
                    "Code block state transition",
                    extra={
                        "transition": transition_type,
                        "language": language or "plain",
                        "char_offset": abs_pos,
                        "chunk_index": len(chunks),
                    },
                )

            start = chosen_end
            in_code_block, code_block_lang = chosen_state
            pending_reopen = chosen_pending

        logger.debug(
            "Completed response splitting",
            extra={"chunks": len(chunks), "limit": limit},
        )
        return chunks

    def _process_code_fences(
        self,
        segment: str,
        absolute_start: int,
        in_code_block: bool,
        code_block_lang: str,
    ) -> Tuple[Tuple[bool, str], List[Tuple[str, str, int]]]:
        transitions: List[Tuple[str, str, int]] = []
        idx = 0
        state_in_code = in_code_block
        state_lang = code_block_lang

        while True:
            fence_idx = segment.find("```", idx)
            if fence_idx == -1:
                break

            lang_start = fence_idx + 3
            lang_end = lang_start
            while lang_end < len(segment) and segment[lang_end] not in {"\n", "\r"}:
                lang_end += 1
            language = segment[lang_start:lang_end].strip()

            absolute_pos = absolute_start + fence_idx
            if not state_in_code:
                state_in_code = True
                state_lang = language
                transitions.append(("open", language, absolute_pos))
            else:
                transitions.append(("close", state_lang, absolute_pos))
                state_in_code = False
                state_lang = ""

            if lang_end < len(segment) and segment[lang_end] == "\r":
                lang_end += 1
            if lang_end < len(segment) and segment[lang_end] == "\n":
                lang_end += 1

            idx = lang_end

        return (state_in_code, state_lang), transitions

    def _truncate(self, text: str) -> str:
        chunks = self._split_response(text)
        if len(chunks) == 1:
            return chunks[0]

        logger.warning(
            "_truncate called on multi-chunk response; returning first chunk for compatibility",
            extra={"chunks": len(chunks)},
        )
        return chunks[0]

    async def _prepare_thread(self, thread: discord.Thread) -> None:
        if thread is None:
            return

        if getattr(thread, "archived", False):
            try:
                await thread.edit(archived=False)
                logger.debug(
                    "Unarchived thread for response",
                    extra={"thread_id": thread.id},
                )
            except discord.Forbidden:
                logger.warning(
                    "Insufficient permissions to unarchive thread",
                    extra={"thread_id": getattr(thread, "id", "unknown")},
                )
            except discord.HTTPException as exc:
                logger.warning(
                    "Failed to unarchive thread",
                    extra={"thread_id": getattr(thread, "id", "unknown")},
                    exc_info=True,
                )

        join_method = getattr(thread, "join", None)
        if callable(join_method):
            with suppress(discord.HTTPException, discord.Forbidden):
                await cast(Awaitable[Any], join_method())

    async def _resolve_existing_thread(self, message: discord.Message) -> discord.Thread | None:
        thread = getattr(message, "thread", None)
        if thread:
            return thread

        channel = message.channel
        fetch_message = getattr(channel, "fetch_message", None)
        if callable(fetch_message):
            try:
                refreshed = await cast(Awaitable[Any], fetch_message(message.id))
            except (discord.HTTPException, discord.NotFound):
                logger.debug(
                    "Unable to fetch message while resolving thread",
                    extra={"message_id": message.id},
                )
            else:
                return getattr(refreshed, "thread", None)

        return None
