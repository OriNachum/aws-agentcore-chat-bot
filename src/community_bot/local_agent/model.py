"""Ollama model wrapper for LocalAgent framework."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Dict, List

import aiohttp

from ..config import Settings
from ..logging_config import get_logger

logger = get_logger("community_bot.model.ollama")


class OllamaModel:
    """A dedicated wrapper for the Ollama API."""
    
    def __init__(self, settings: Settings):
        """Initialize the Ollama model with application settings.
        
        Args:
            settings: Application settings containing Ollama configuration
        """
        self.settings = settings
        self.base_url = settings.ollama_base_url
        self.model_name = settings.ollama_model
        
        logger.info(f"Initializing OllamaModel")
        logger.debug(f"Base URL: {self.base_url}")
        logger.debug(f"Model name: {self.model_name}")
        
        if not self.model_name:
            error_msg = "OLLAMA_MODEL must be specified in settings"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("OllamaModel initialization complete")
    
    async def chat(self, history: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Send conversation history to Ollama and stream the response.
        
        Args:
            history: List of message dictionaries with 'role' and 'content' keys
            
        Yields:
            String chunks of the model's response
            
        Raises:
            aiohttp.ClientError: If there's an error communicating with Ollama
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": history,
            "stream": True,
        }
        
        logger.debug(f"Starting chat request to {url}")
        logger.debug(f"History length: {len(history)} messages")
        logger.debug(f"Model: {self.model_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Making HTTP POST request to Ollama")
                async with session.post(url, json=payload) as resp:
                    logger.debug(f"Ollama response status: {resp.status}")
                    resp.raise_for_status()
                    
                    chunk_count = 0
                    total_content = ""
                    
                    async for line_bytes in resp.content:
                        if not line_bytes:
                            continue
                        
                        try:
                            line = line_bytes.decode("utf-8").strip()
                            if not line:
                                continue
                            
                            data = json.loads(line)
                            
                            # Check if streaming is complete
                            if data.get("done"):
                                logger.debug("Ollama streaming completed")
                                break
                            
                            # Extract content from the message
                            message = data.get("message", {})
                            content = message.get("content")
                            
                            if content:
                                chunk_count += 1
                                total_content += content
                                logger.debug(f"Received chunk {chunk_count}: {len(content)} characters")
                                yield content
                                
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            logger.warning(f"Skipping malformed line: {e}")
                            # Skip malformed lines
                            continue
                    
                    logger.info(f"Chat stream completed: {chunk_count} chunks, {len(total_content)} total characters")
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error communicating with Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Ollama chat: {e}", exc_info=True)
            raise
    
    async def chat_complete(self, history: List[Dict[str, str]]) -> str:
        """Get a complete response from the model (non-streaming).
        
        Args:
            history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Complete response string from the model
        """
        logger.debug("Starting complete chat request")
        chunks = []
        async for chunk in self.chat(history):
            chunks.append(chunk)
        response = "".join(chunks)
        logger.info(f"Complete chat finished: {len(response)} characters")
        return response
