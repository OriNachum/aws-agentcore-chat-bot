#!/usr/bin/env python3
"""
Test script to verify AgentCore integration with Strands framework.
"""

import sys
from pathlib import Path

# Add the src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from community_bot.config import load_settings
from community_bot.agent_client import AgentClient
from community_bot.logging_config import setup_logging, get_logger


def test_agentcore_integration():
    """Test the AgentCore integration with the Strands framework."""
    print("Testing AgentCore integration...")
    
    # Load settings
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger("test_agentcore_integration")
    
    print(f"Backend mode: {settings.backend_mode}")
    print(f"Ollama model: {settings.ollama_model}")
    print(f"Ollama base URL: {settings.ollama_base_url}")
    
    try:
        # Initialize agent client
        agent_client = AgentClient(settings)
        logger.info("AgentClient initialized successfully")
        
        # Test a simple conversation
        test_message = "Hello! Can you tell me what 2+2 equals?"
        print(f"\nTesting with message: {test_message}")
        
        async def test_chat():
            response_parts = []
            async for chunk in agent_client.chat(test_message):
                response_parts.append(chunk)
                print(f"Received chunk: {chunk[:100]}...")
            
            full_response = "".join(response_parts)
            return full_response
        
        # Run the async test
        import asyncio
        response = asyncio.run(test_chat())
        
        print(f"\nFull response: {response}")
        print("\n✅ AgentCore integration test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"AgentCore integration test failed: {e}", exc_info=True)
        print(f"\n❌ AgentCore integration test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_agentcore_integration()
    sys.exit(0 if success else 1)