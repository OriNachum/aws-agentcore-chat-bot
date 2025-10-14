"""AWS Bedrock Nova-Pro model implementation."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional, Dict, Any
import asyncio

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .logging_config import get_logger

logger = get_logger("community_bot.nova_model")


class NovaModel:
    """AWS Bedrock Nova-Pro model with streaming support."""
    
    def __init__(
        self,
        model_id: str = "us.amazon.nova-pro-v1:0",
        region: str = "us-east-1",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.9,
    ):
        """Initialize Nova-Pro model.
        
        Args:
            model_id: Bedrock model identifier
            region: AWS region
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
        """
        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        
        # Configure boto3 client with retries
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.client = boto3.client('bedrock-runtime', config=config)
        logger.info(f"Initialized Nova model: {model_id} in {region}")
    
    async def generate_streaming(
        self,
        messages: list[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Nova-Pro.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            
        Yields:
            Text chunks from the model
        """
        logger.debug(f"Generating streaming response with {len(messages)} messages")
        
        # Build Nova request body
        body = {
            "messages": self._format_messages(messages),
            "inferenceConfig": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_tokens,
                "topP": self.top_p,
            }
        }
        
        if system_prompt:
            body["system"] = [{"text": system_prompt}]
        
        try:
            # Invoke model with streaming
            response = await asyncio.to_thread(
                self.client.invoke_model_with_response_stream,
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            # Process streaming response
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # Extract text from the chunk
                        if 'contentBlockDelta' in chunk_data:
                            delta = chunk_data['contentBlockDelta'].get('delta', {})
                            if 'text' in delta:
                                text = delta['text']
                                logger.debug(f"Yielding chunk: {len(text)} chars")
                                yield text
                        
                        # Handle errors in stream
                        if 'error' in chunk_data:
                            error_msg = chunk_data['error'].get('message', 'Unknown error')
                            logger.error(f"Error in stream: {error_msg}")
                            raise RuntimeError(f"Nova streaming error: {error_msg}")
                                
        except ClientError as e:
            logger.error(f"AWS client error during Nova streaming: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error during Nova streaming: {e}", exc_info=True)
            raise
    
    def _format_messages(self, messages: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Format messages for Nova API.
        
        Args:
            messages: Raw message list
            
        Returns:
            Formatted messages for Nova
        """
        formatted = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            formatted.append({
                "role": role,
                "content": [{"text": content}]
            })
        
        return formatted
