#!/usr/bin/env python3
"""
Example script demonstrating enhanced AgentCore integration with knowledge bases.

This script shows how to use the enhanced agentcore_app with:
- Memory persistence across sessions
- Knowledge base integration
- AgentCore deployment capabilities

Usage:
    # Local testing with memory and knowledge base
    python agentcore_enhanced_example.py
    
    # Deploy to AgentCore
    agentcore configure -e agentcore_enhanced_example.py
    agentcore launch
"""

import os
import sys
from pathlib import Path

# Add the src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from community_bot.agentcore_app import (
    chat_with_agent,
    setup_knowledge_base_integration,
    agentcore_app,
    AGENTCORE_SERVICES_AVAILABLE
)
from community_bot.logging_config import setup_logging, get_logger

# Setup logging
setup_logging("INFO")
logger = get_logger("agentcore_enhanced_example")

def test_local_enhanced_agent():
    """Test the enhanced agent locally with memory and knowledge base features."""
    logger.info("Testing enhanced AgentCore agent locally")
    
    # Setup knowledge base integration
    kb_available = setup_knowledge_base_integration()
    logger.info(f"Knowledge base integration: {'Available' if kb_available else 'Not available'}")
    
    # Simulate a conversation with session persistence
    session_id = "demo_session_123"
    
    print("🤖 Enhanced AgentCore Agent Demo")
    print("=" * 50)
    print(f"AgentCore Services: {'✅ Available' if AGENTCORE_SERVICES_AVAILABLE else '❌ Limited'}")
    print(f"Knowledge Base: {'✅ Enabled' if kb_available else '❌ Disabled'}")
    print(f"Session ID: {session_id}")
    print("=" * 50)
    
    # Test messages
    test_messages = [
        "Hello! Can you help me understand what AgentCore is?",
        "What are the key benefits of using knowledge bases with agents?",
        "Can you remember what we discussed earlier in this conversation?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[Message {i}] User: {message}")
        
        response = chat_with_agent(
            user_message=message,
            session_id=session_id,
            use_knowledge_base=True
        )
        
        print(f"[Response {i}] Agent: {response}")
        print("-" * 50)

@agentcore_app.entrypoint
def enhanced_agent_entrypoint(payload, context=None):
    """
    Enhanced AgentCore entrypoint with additional features.
    
    This demonstrates how to extend the base agent with custom logic
    while still leveraging the enhanced AgentCore capabilities.
    """
    logger.info("Enhanced AgentCore entrypoint called")
    
    # Setup knowledge base if not already done
    setup_knowledge_base_integration()
    
    # Extract enhanced payload parameters
    user_message = payload.get("prompt", payload.get("message", ""))
    session_id = payload.get("session_id", f"session_{hash(str(payload))}")
    use_knowledge_base = payload.get("use_knowledge_base", True)
    include_debug_info = payload.get("debug", False)
    
    if not user_message:
        return {
            "error": "No prompt or message found. Please include 'prompt' or 'message' in your payload.",
            "example_payload": {
                "prompt": "Your message here",
                "session_id": "optional_session_id",
                "use_knowledge_base": True,
                "debug": False
            }
        }
    
    # Process with enhanced capabilities
    response = chat_with_agent(
        user_message=user_message,
        session_id=session_id,
        use_knowledge_base=use_knowledge_base
    )
    
    result = {
        "result": response,
        "session_id": session_id,
        "enhanced_features": {
            "memory_enabled": AGENTCORE_SERVICES_AVAILABLE,
            "knowledge_base_enabled": use_knowledge_base and AGENTCORE_SERVICES_AVAILABLE,
            "agentcore_services": AGENTCORE_SERVICES_AVAILABLE
        }
    }
    
    if include_debug_info:
        result["debug_info"] = {
            "message_length": len(user_message),
            "response_length": len(response),
            "payload_keys": list(payload.keys())
        }
    
    return result

def main():
    """Main function for running the enhanced example."""
    # Check if running in AgentCore deployment mode
    if os.environ.get("AGENTCORE_MODE", "false").lower() == "true":
        logger.info("Running in AgentCore deployment mode")
        agentcore_app.run()
    else:
        logger.info("Running in local test mode")
        test_local_enhanced_agent()

if __name__ == "__main__":
    main()