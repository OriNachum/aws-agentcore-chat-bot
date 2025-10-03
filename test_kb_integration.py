"""
Simple test script to verify AgentCore with KB integration is working.

Run this to test your setup after configuring environment variables.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Enable debug logging
os.environ["LOG_LEVEL"] = "DEBUG"

from community_bot.config import load_settings
from community_bot.logging_config import setup_logging, get_logger
from community_bot.agentcore_app import chat_with_agent

settings = load_settings()
setup_logging(settings.log_level)
logger = get_logger("test_kb")

def main():
    print("\n" + "=" * 80)
    print("Testing AgentCore with Knowledge Base Integration")
    print("=" * 80 + "\n")
    
    # Check configuration
    print("Configuration:")
    print(f"  Backend: {settings.backend_mode}")
    print(f"  Ollama model: {settings.ollama_model}")
    print(f"  Ollama URL: {settings.ollama_base_url}")
    print(f"  KB Gateway ID: {'SET' if os.environ.get('KB_GATEWAY_ID') else 'NOT SET'}")
    print(f"  KB Direct Endpoint: {'SET' if os.environ.get('KB_DIRECT_ENDPOINT') else 'NOT SET'}")
    print()
    
    # Test 1: Simple chat without KB
    print("=" * 80)
    print("Test 1: Simple chat (KB disabled)")
    print("=" * 80)
    
    try:
        response = chat_with_agent(
            user_message="Hello! What can you do?",
            use_knowledge_base=False
        )
        print(f"\n✅ Response ({len(response)} chars):")
        print(f"{response[:500]}...")
        print()
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}\n")
        logger.exception("Test 1 failed")
    
    # Test 2: Chat with KB enabled
    print("=" * 80)
    print("Test 2: Chat with KB enabled")
    print("=" * 80)
    
    try:
        response = chat_with_agent(
            user_message="What information do you have in your knowledge base?",
            use_knowledge_base=True
        )
        print(f"\n✅ Response ({len(response)} chars):")
        print(f"{response[:500]}...")
        print()
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}\n")
        logger.exception("Test 2 failed")
    
    print("=" * 80)
    print("Tests complete. Check logs above for details.")
    print("=" * 80)
    print("\nIf you see empty responses, check:")
    print("  1. The detailed logs above (look for [KB TOOL] and [CHAT] markers)")
    print("  2. Run diagnose_kb_integration.py for a comprehensive diagnostic")
    print("  3. Verify your KB endpoint is accessible")
    print("  4. Check that Ollama is running and accessible")
    print()

if __name__ == "__main__":
    main()
