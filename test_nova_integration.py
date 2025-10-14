"""Integration tests for Nova backend."""

import asyncio
import os
from dotenv import load_dotenv

from src.community_bot.config import load_settings
from src.community_bot.agent_client import AgentClient
from src.community_bot.logging_config import setup_logging, get_logger


async def test_nova_integration():
    """Test complete Nova integration."""
    # Load settings
    load_dotenv()
    
    # Override environment to use Nova
    os.environ["BACKEND_MODE"] = "nova"
    
    settings = load_settings()
    
    setup_logging(settings.log_level)
    logger = get_logger("test_nova_integration")
    
    logger.info("=" * 80)
    logger.info("Testing Nova Integration")
    logger.info("=" * 80)
    
    # Initialize agent client
    client = AgentClient(settings)
    
    # Test messages
    test_messages = [
        "Hello, can you introduce yourself?",
        "What is the capital of France?",
        "Tell me a short joke.",
    ]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\nTest {i}/{len(test_messages)}: {message}")
        logger.info("-" * 40)
        
        response = ""
        async for chunk in client.chat(message):
            response += chunk
            print(chunk, end="", flush=True)
        
        print("\n")
        logger.info(f"Response length: {len(response)} characters")
        
        assert len(response) > 0, "Response should not be empty"
    
    logger.info("=" * 80)
    logger.info("✅ All Nova integration tests passed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_nova_integration())
