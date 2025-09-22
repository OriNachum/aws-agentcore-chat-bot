#!/usr/bin/env python3
"""
Example of integrating the new Strands agent with the existing Discord bot.
This shows how to replace the LocalAgent with the new AgentCore-compatible system.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from community_bot.agentcore_app import chat_with_agent

def example_discord_integration():
    """
    Example showing how the new agent can be integrated with Discord bot.
    """
    print("=== Strands Agent Integration Example ===\n")
    
    # Simulate some Discord messages
    test_messages = [
        "Hello! How can you help me?",
        "What's the weather like?",
        "Can you explain Python decorators?",
        "Tell me a joke",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"User Message {i}: {message}")
        
        try:
            # This is how you'd call the agent in your Discord bot
            response = chat_with_agent(message)
            print(f"Agent Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
            # In a real Discord bot, you might want to send a fallback message
            response = "I'm sorry, I'm having trouble connecting to the AI service right now."
            print(f"Fallback Response: {response}")
        
        print("-" * 50)

def example_custom_configuration():
    """
    Example showing how to use different model providers.
    """
    print("\n=== Custom Configuration Example ===\n")
    
    # Show current configuration
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    print(f"Current LLM Provider: {provider}")
    
    print("\nTo switch providers:")
    print("For Ollama: export LLM_PROVIDER=ollama")
    print("For Bedrock: export LLM_PROVIDER=bedrock")
    
    print("\nConfiguration is read from your existing settings:")
    print("- settings.ollama_model")
    print("- settings.ollama_base_url")

if __name__ == "__main__":
    example_custom_configuration()
    
    # Only run the integration example if we can import the agent
    try:
        example_discord_integration()
    except Exception as e:
        print(f"Integration example failed: {e}")
        print("This is expected if Ollama is not running or configuration is missing.")
        print("The agent setup is still correct - just needs proper model server running.")