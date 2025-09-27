#!/usr/bin/env python3
"""Test script for the LocalAgent framework."""

import asyncio
import os
from pathlib import Path
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from community_bot.config import Settings
from community_bot.local_agent import LocalAgent, ConversationMemory, OllamaModel


async def test_local_agent():
    """Test the LocalAgent framework with a simple conversation."""
    print("🤖 Testing LocalAgent Framework")
    print("=" * 50)
    
    # Create mock settings for testing
    settings = Settings(
        discord_token="test_token",
        discord_channel_id=123456789,
        backend_mode="ollama",
        ollama_model="llama3.1",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=10,
        system_prompt="You are a helpful AI assistant for testing purposes.",
        prompt_profile="default",
        prompt_root=(Path(__file__).parent.parent / "agents").resolve(),
        prompt_user_role="user",
    )
    
    try:
        # Initialize components
        print("📝 Initializing LocalAgent components...")
        model = OllamaModel(settings)
        memory = ConversationMemory(max_messages=settings.memory_max_messages)
        agent = LocalAgent(model, memory, settings)
        
        print(f"✅ LocalAgent initialized with memory limit: {settings.memory_max_messages}")
        print(f"📊 Current memory size: {agent.get_memory_size()}")
        
        # Test conversation
        test_messages = [
            "Hello! Can you introduce yourself?",
            "What's 2 + 2?",
            "Tell me a short joke.",
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n💬 Test {i}: {message}")
            print("🤖 Response: ", end="", flush=True)
            
            try:
                response_chunks = []
                async for chunk in agent.chat(message):
                    print(chunk, end="", flush=True)
                    response_chunks.append(chunk)
                
                print()  # New line after response
                print(f"📊 Memory size after message {i}: {agent.get_memory_size()}")
                
            except Exception as e:
                print(f"❌ Error during conversation: {e}")
                print("💡 Make sure Ollama is running with the specified model!")
                return False
        
        # Test memory management
        print(f"\n🧠 Testing memory management...")
        print(f"Current conversation history has {len(memory.get_history())} messages")
        
        # Test clearing memory
        agent.settings.system_prompt = "You are now a pirate assistant. Speak like a pirate!"
        agent.clear_memory()
        print(f"🔄 Memory cleared and reset. New size: {agent.get_memory_size()}")
        
        # Test with new personality
        print(f"\n🏴‍☠️ Testing with new personality...")
        print("💬 Test: Tell me about the weather")
        print("🤖 Response: ", end="", flush=True)
        
        async for chunk in agent.chat("Tell me about the weather"):
            print(chunk, end="", flush=True)
        
        print()
        print("\n✅ LocalAgent framework test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_memory_limits():
    """Test memory management with message limits."""
    print("\n🧠 Testing Memory Limits")
    print("=" * 30)
    
    # Create a memory with very small limit for testing
    memory = ConversationMemory(max_messages=5)
    
    # Add system message
    memory.add_message("system", "You are a test assistant.")
    print(f"After system message: {len(memory)} messages")
    
    # Add more messages than the limit
    for i in range(8):
        memory.add_message("user", f"Test message {i}")
        memory.add_message("assistant", f"Response {i}")
        print(f"After message pair {i}: {len(memory)} messages")
    
    # Check that system message is preserved
    history = memory.get_history()
    system_messages = [msg for msg in history if msg["role"] == "system"]
    print(f"System messages preserved: {len(system_messages)}")
    print(f"Total messages in memory: {len(history)}")
    
    return len(system_messages) > 0 and len(history) <= 5


if __name__ == "__main__":
    print("🚀 Starting LocalAgent Framework Tests")
    
    # Test memory limits first (doesn't require Ollama)
    memory_test_result = asyncio.run(test_memory_limits())
    print(f"Memory test result: {'✅ PASSED' if memory_test_result else '❌ FAILED'}")
    
    # Test full LocalAgent (requires Ollama)
    print(f"\n" + "="*60)
    agent_test_result = asyncio.run(test_local_agent())
    
    print(f"\n🏁 Final Results:")
    print(f"Memory Management: {'✅ PASSED' if memory_test_result else '❌ FAILED'}")
    print(f"LocalAgent Framework: {'✅ PASSED' if agent_test_result else '❌ FAILED'}")
    
    if not agent_test_result:
        print(f"\n💡 To run the full test, make sure:")
        print(f"   1. Ollama is installed and running")
        print(f"   2. The model 'llama3.1' is available (or change the model name)")
        print(f"   3. Ollama is accessible at http://localhost:11434")
