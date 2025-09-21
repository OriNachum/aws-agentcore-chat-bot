#!/usr/bin/env python3
"""
Test script to verify comprehensive logging functionality.

This script tests the logging at different levels to ensure that
debug information is properly captured to help diagnose Discord
message processing issues.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from community_bot.config import Settings
from community_bot.logging_config import setup_logging, get_logger
from community_bot.agent_client import AgentClient
from community_bot.local_agent import LocalAgent, ConversationMemory, OllamaModel


def test_logging_levels():
    """Test different logging levels to ensure proper output."""
    print("🔍 Testing Logging Levels")
    print("=" * 40)
    
    # Test with DEBUG level
    setup_logging("DEBUG")
    logger = get_logger("test_logging")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message") 
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("\n✅ Logging levels test completed")


async def test_message_flow_logging():
    """Test the complete message flow logging without actual Discord/Ollama."""
    print("\n🔄 Testing Message Flow Logging")
    print("=" * 40)
    
    # Create mock settings
    settings = Settings(
        discord_token="test_token",
        discord_channel_id=123456789,
        backend_mode="ollama",
        ollama_model="test_model",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=10,
        system_prompt="Test system prompt",
        log_level="DEBUG"
    )
    
    setup_logging(settings.log_level)
    logger = get_logger("test_flow")
    
    logger.info("🚀 Starting message flow test")
    
    try:
        # Test memory logging
        logger.info("Testing ConversationMemory logging")
        memory = ConversationMemory(max_messages=3)
        memory.add_message("system", "You are a test assistant")
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")
        
        # Test memory overflow
        memory.add_message("user", "How are you?")
        memory.add_message("assistant", "I'm doing well!")
        
        # This should trigger memory trimming
        memory.add_message("user", "What's the weather?")
        
        logger.info(f"Final memory size: {len(memory)}")
        
        # Test model initialization (will fail without Ollama, but that's expected)
        logger.info("Testing OllamaModel initialization")
        try:
            model = OllamaModel(settings)
            logger.info("OllamaModel initialized successfully")
        except Exception as e:
            logger.info(f"OllamaModel initialization failed as expected: {e}")
        
        # Test agent client initialization
        logger.info("Testing AgentClient initialization")
        try:
            # This will fail because Ollama isn't running, but we can test the logging
            agent_client = AgentClient(settings)
            logger.info("AgentClient initialized successfully")
        except Exception as e:
            logger.info(f"AgentClient initialization failed as expected: {e}")
        
        logger.info("✅ Message flow logging test completed")
        
    except Exception as e:
        logger.error(f"❌ Message flow test failed: {e}", exc_info=True)


def test_discord_channel_validation():
    """Test logging for Discord channel ID validation."""
    print("\n📱 Testing Discord Channel Validation Logging")
    print("=" * 50)
    
    setup_logging("DEBUG")
    logger = get_logger("test_discord")
    
    # Simulate the channel filtering logic with logging
    target_channel_id = 123456789
    
    # Test messages from different channels
    test_cases = [
        {"channel_id": 123456789, "author": "user1", "content": "Hello!", "is_bot": False},
        {"channel_id": 987654321, "author": "user2", "content": "Hi there!", "is_bot": False},
        {"channel_id": 123456789, "author": "bot", "content": "Bot message", "is_bot": True},
    ]
    
    for i, case in enumerate(test_cases, 1):
        logger.info(f"Test case {i}: Processing message simulation")
        logger.debug(f"Channel ID: {case['channel_id']}, Author: {case['author']}, Is Bot: {case['is_bot']}")
        
        # Simulate bot check
        if case["is_bot"]:
            logger.debug(f"Ignoring bot message from {case['author']}")
            continue
            
        # Simulate channel check
        if case["channel_id"] != target_channel_id:
            logger.debug(f"Ignoring message from non-monitored channel {case['channel_id']}")
            continue
        
        logger.info(f"Processing message from {case['author']}: {case['content'][:100]}...")
        logger.debug("This message would be sent to the agent for processing")
    
    print("✅ Discord validation logging test completed")


def main():
    """Run all logging tests."""
    print("🧪 Community Bot Logging Test Suite")
    print("=" * 60)
    
    # Test 1: Basic logging levels
    test_logging_levels()
    
    # Test 2: Message flow logging (async)
    asyncio.run(test_message_flow_logging())
    
    # Test 3: Discord validation logging
    test_discord_channel_validation()
    
    print(f"\n🏁 All Tests Completed!")
    print(f"")
    print(f"💡 To enable DEBUG logging in the actual bot:")
    print(f"   Set LOG_LEVEL=DEBUG in your .env file")
    print(f"")
    print(f"📋 Logging helps identify these common issues:")
    print(f"   • Messages not being received (check Discord connection)")
    print(f"   • Wrong channel ID (check channel filtering logs)")
    print(f"   • Bot responding to itself (check bot detection logs)")
    print(f"   • Backend connection failures (check agent client logs)")
    print(f"   • Ollama communication issues (check model logs)")
    print(f"   • Memory management problems (check memory logs)")


if __name__ == "__main__":
    main()