#!/usr/bin/env python3
"""
Demo script to show AI-generated thread name feature.
This simulates the thread name generation without requiring Discord.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from community_bot.config import Settings
from community_bot.agent_client import AgentClient
from community_bot.discord_bot import CommunityBot


def create_demo_settings():
    """Create minimal settings for demo."""
    return Settings(
        discord_token="demo-token",
        discord_channel_id=12345,
        backend_mode="ollama",  # Change to "agentcore" if you want to use that
        ollama_model="llama3.1",  # Or your preferred model
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=50,
        log_level="INFO",
    )


async def demo_thread_name_generation():
    """Demonstrate thread name generation for various messages."""
    print("=" * 80)
    print("AI-Generated Thread Names Demo")
    print("=" * 80)
    print()
    
    # Create settings and bot instance
    settings = create_demo_settings()
    agent_client = AgentClient(settings)
    bot = CommunityBot(settings, agent_client)
    
    # Test messages
    test_messages = [
        ("Alice", "Can you explain how transformers work in machine learning?"),
        ("Bob", "I'm having trouble deploying my Docker container to AWS"),
        ("Charlie", "What's the difference between supervised and unsupervised learning?"),
        ("Diana", "Help me understand async/await in Python"),
        ("Eve", "Hello! How are you today?"),
    ]
    
    print(f"Backend: {settings.backend_mode}")
    print(f"Model: {settings.ollama_model if settings.backend_mode == 'ollama' else 'Bedrock'}")
    print()
    print("Generating thread names...")
    print("-" * 80)
    print()
    
    for username, message in test_messages:
        print(f"User: {username}")
        print(f"Message: {message}")
        
        try:
            # Generate thread name
            thread_name = await bot._generate_thread_name(message, username)
            print(f"✅ Thread Name: {thread_name}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("Demo completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(demo_thread_name_generation())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
