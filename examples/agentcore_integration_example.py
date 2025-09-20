#!/usr/bin/env python3
"""
Example showing how to integrate LocalAgent with AWS AgentCore and Strands.

This is a conceptual implementation showing the architecture.
To run this, you would need to install:
- pip install strands-agents
- pip install bedrock-agentcore

Note: This example shows the intended architecture but may need adjustments
based on the actual SDK APIs when they become available.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from community_bot.config import Settings
from community_bot.local_agent import LocalAgent, ConversationMemory, OllamaModel

# These imports would be available when the SDKs are installed
try:
    from strands import Agent as StrandsAgent
    from strands.models.ollama import OllamaModel as StrandsOllamaModel
    from strands.tools import calculator, current_time
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    print("⚠️  Strands SDK not available - showing conceptual implementation")

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    print("⚠️  AgentCore SDK not available - showing conceptual implementation")


class EnhancedLocalAgent:
    """Enhanced LocalAgent that can integrate with Strands and AgentCore."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.local_agent = None
        self.strands_agent = None
        
        # Initialize our LocalAgent
        model = OllamaModel(settings)
        memory = ConversationMemory(max_messages=settings.memory_max_messages)
        self.local_agent = LocalAgent(model, memory, system_prompt=settings.system_prompt)
        
        # Initialize Strands agent if available
        if STRANDS_AVAILABLE:
            self._init_strands_agent()
    
    def _init_strands_agent(self):
        """Initialize Strands agent with Ollama model and tools."""
        if not STRANDS_AVAILABLE:
            return
        
        # Configure Strands to use Ollama
        strands_model = StrandsOllamaModel(
            host=self.settings.ollama_base_url,
            model_id=self.settings.ollama_model
        )
        
        # Create Strands agent with tools
        self.strands_agent = StrandsAgent(
            model=strands_model,
            tools=[calculator, current_time]
        )
    
    async def chat_local(self, message: str):
        """Chat using our LocalAgent framework."""
        response_chunks = []
        async for chunk in self.local_agent.chat(message):
            response_chunks.append(chunk)
        return "".join(response_chunks)
    
    def chat_strands(self, message: str):
        """Chat using Strands agent (if available)."""
        if not self.strands_agent:
            return "Strands agent not available"
        
        response = self.strands_agent(message)
        return response.message['content'][0]['text']
    
    async def chat_hybrid(self, message: str):
        """Use both agents and compare responses."""
        local_response = await self.chat_local(message)
        
        if self.strands_agent:
            strands_response = self.chat_strands(message)
            return {
                "local_agent": local_response,
                "strands_agent": strands_response
            }
        else:
            return {
                "local_agent": local_response,
                "strands_agent": "Not available"
            }


# AgentCore Integration Example
if AGENTCORE_AVAILABLE:
    app = BedrockAgentCoreApp()
    
    # Global agent instance
    enhanced_agent = None
    
    @app.entrypoint
    def discord_agent_handler(request):
        """AgentCore entry point for Discord bot."""
        global enhanced_agent
        
        if not enhanced_agent:
            # Initialize with settings (in real implementation, load from environment)
            settings = Settings(
                discord_token="dummy",
                discord_channel_id=123456789,
                backend_mode="ollama",
                ollama_model="llama3.1",
                ollama_base_url="http://localhost:11434",
                max_response_chars=1800,
                memory_max_messages=50,
                system_prompt="You are a helpful Discord community assistant."
            )
            enhanced_agent = EnhancedLocalAgent(settings)
        
        # Process the request
        user_message = request.get("query", "")
        
        # Use asyncio to handle async chat method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(enhanced_agent.chat_local(user_message))
            return {
                "message": response,
                "status": "success",
                "agent_type": "local_agent"
            }
        finally:
            loop.close()


async def test_integration():
    """Test the integration example."""
    print("🔗 Testing Enhanced LocalAgent Integration")
    print("=" * 50)
    
    # Create settings
    settings = Settings(
        discord_token="test_token",
        discord_channel_id=123456789,
        backend_mode="ollama",
        ollama_model="llama3.1",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=10,
        system_prompt="You are a helpful AI assistant."
    )
    
    # Initialize enhanced agent
    enhanced_agent = EnhancedLocalAgent(settings)
    
    # Test local agent
    print("🤖 Testing LocalAgent:")
    try:
        local_response = await enhanced_agent.chat_local("What's the current time?")
        print(f"LocalAgent Response: {local_response[:100]}...")
    except Exception as e:
        print(f"LocalAgent Error: {e}")
    
    # Test Strands agent (if available)
    if STRANDS_AVAILABLE:
        print("\n🔧 Testing Strands Agent:")
        try:
            strands_response = enhanced_agent.chat_strands("What's 15 * 23?")
            print(f"Strands Response: {strands_response}")
        except Exception as e:
            print(f"Strands Error: {e}")
    
    # Test hybrid approach
    print("\n🔀 Testing Hybrid Approach:")
    try:
        hybrid_response = await enhanced_agent.chat_hybrid("Hello, how are you?")
        print("Hybrid Response:")
        for agent_type, response in hybrid_response.items():
            print(f"  {agent_type}: {response[:100]}...")
    except Exception as e:
        print(f"Hybrid Error: {e}")


if __name__ == "__main__":
    print("🚀 AgentCore Integration Example")
    print(f"Strands Available: {STRANDS_AVAILABLE}")
    print(f"AgentCore Available: {AGENTCORE_AVAILABLE}")
    
    # Run the test
    asyncio.run(test_integration())
    
    if AGENTCORE_AVAILABLE:
        print("\n🌐 To deploy with AgentCore, run:")
        print("python -c 'from examples.agentcore_integration_example import app; app.run()'")
    else:
        print("\n💡 To enable full integration:")
        print("pip install strands-agents bedrock-agentcore")
