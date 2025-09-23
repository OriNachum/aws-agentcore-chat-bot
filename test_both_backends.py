#!/usr/bin/env python3
"""
Test script to demonstrate both Ollama and AgentCore backend modes.
"""

import sys
import os
from pathlib import Path

# Add the src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from community_bot.config import load_settings
from community_bot.agent_client import AgentClient
from community_bot.logging_config import setup_logging, get_logger


async def test_backend_mode(backend_mode: str):
    """Test a specific backend mode."""
    print(f"\n{'='*50}")
    print(f"Testing BACKEND_MODE={backend_mode}")
    print(f"{'='*50}")
    
    # Temporarily set the backend mode
    original_mode = os.environ.get("BACKEND_MODE")
    os.environ["BACKEND_MODE"] = backend_mode
    
    try:
        # Reload settings to pick up the new backend mode
        settings = load_settings()
        print(f"Backend mode: {settings.backend_mode}")
        print(f"Ollama model: {settings.ollama_model}")
        print(f"Ollama base URL: {settings.ollama_base_url}")
        
        # Initialize agent client
        agent_client = AgentClient(settings)
        
        # Test a simple conversation
        test_message = "What is the capital of France?"
        print(f"\nTesting with message: {test_message}")
        
        response_parts = []
        async for chunk in agent_client.chat(test_message):
            response_parts.append(chunk)
            print(f"Received chunk: {chunk[:50]}...")
        
        full_response = "".join(response_parts)
        print(f"\nFull response: {full_response}")
        print(f"✅ {backend_mode} backend test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ {backend_mode} backend test failed: {e}")
        return False
    
    finally:
        # Restore original backend mode
        if original_mode is not None:
            os.environ["BACKEND_MODE"] = original_mode
        elif "BACKEND_MODE" in os.environ:
            del os.environ["BACKEND_MODE"]


async def main():
    """Run tests for both backend modes."""
    print("Testing both backend modes...")
    
    # Setup logging
    setup_logging("INFO")
    
    import asyncio
    
    # Test both modes
    ollama_success = await test_backend_mode("ollama")
    agentcore_success = await test_backend_mode("agentcore")
    
    print(f"\n{'='*50}")
    print("Summary:")
    print(f"Ollama backend: {'✅ Success' if ollama_success else '❌ Failed'}")
    print(f"AgentCore backend: {'✅ Success' if agentcore_success else '❌ Failed'}")
    print(f"{'='*50}")
    
    if ollama_success and agentcore_success:
        print("\n🎉 All tests passed! Both backend modes are working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)