"""Ollama model wrapper for LocalAgent framework."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Dict, List

import aiohttp

from ..config import Settings


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
        
        if not self.model_name:
            raise ValueError("OLLAMA_MODEL must be specified in settings")
    
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
                        
                        # Check if streaming is complete
                        if data.get("done"):
                            break
                        
                        # Extract content from the message
                        message = data.get("message", {})
                        content = message.get("content")
                        
                        if content:
                            yield content
                            
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Skip malformed lines
                        continue
    
    async def chat_complete(self, history: List[Dict[str, str]]) -> str:
        """Get a complete response from the model (non-streaming).
        
        Args:
            history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Complete response string from the model
        """
        chunks = []
        async for chunk in self.chat(history):
            chunks.append(chunk)
        return "".join(chunks)
