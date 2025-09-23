# src/community_bot/agentcore_app.py

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from strands import Agent
from strands.models.ollama import OllamaModel
from strands.models import BedrockModel

# Add the src directory to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from community_bot.config import load_settings
from community_bot.logging_config import setup_logging, get_logger

# --- Model Configuration ---
# This is where we can switch between Ollama and Bedrock
# When called from agent_client with agentcore mode, we'll use Ollama with the settings configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")  # 'ollama' or 'bedrock'

# Allow overriding via function parameter for agent_client integration
_force_provider = None

def set_provider(provider: str):
    """Set the provider for this session (used by agent_client)."""
    global _force_provider
    _force_provider = provider

# Load application settings
settings = load_settings()
setup_logging(settings.log_level)
logger = get_logger("community_bot.agentcore_app")

logger.info(f"Initializing AgentCore app with LLM provider: {LLM_PROVIDER}")

# Initialize the agent lazily
_agent = None

def get_agent():
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        # Use forced provider if set, otherwise use environment variable
        provider = _force_provider or LLM_PROVIDER
        
        if provider == "ollama":
            # Assumes Ollama is running locally
            model_name = settings.ollama_model or "llama3"  # Default fallback
            base_url = settings.ollama_base_url or "http://localhost:11434"  # Default fallback
            logger.info(f"Configuring Ollama model: {model_name} at {base_url}")
            model = OllamaModel(
                host=base_url,
                model_id=model_name
            )
        elif provider == "bedrock":
            # Configure for Bedrock (e.g., Claude)
            logger.info("Configuring Bedrock model")
            model = BedrockModel(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                temperature=0.3,
                streaming=True
            )
        else:
            logger.error(f"Unknown LLM provider: {provider}")
            raise ValueError(f"Unknown LLM provider: {provider}")

        _agent = Agent(model=model)
        logger.info("Initialized Strands Agent with configured model")
    
    return _agent

def chat_with_agent(user_message: str) -> str:
    """
    Simple function to chat with the agent.
    This can be called directly or integrated with other systems.
    """
    logger.info(f"Processing user message: {user_message[:100]}...")
    
    try:
        agent = get_agent()
        result = agent(user_message)
        # Extract the text content from the AgentResult
        response_text = str(result)  # AgentResult has __str__ method
        logger.info(f"Agent response generated: {len(response_text)} characters")
        return response_text
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return f"I encountered an error while processing your request: {str(e)}"

def main():
    """Main function for testing the agent locally."""
    logger.info("Starting interactive chat with the agent")
    logger.info("Type 'quit' or 'exit' to stop")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue
                
            response = chat_with_agent(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            print(f"Error: {e}")
    
    logger.info("Chat session ended")

if __name__ == "__main__":
    main()