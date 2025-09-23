# src/community_bot/agentcore_app.py

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from strands import Agent
from strands.models.ollama import OllamaModel
from strands.models import BedrockModel

# AgentCore imports
from bedrock_agentcore.runtime import BedrockAgentCoreApp
try:
    from bedrock_agentcore.services.memory import MemoryClient
    from bedrock_agentcore.services.gateway import GatewayClient
    from bedrock_agentcore.services.identity import IdentityClient
    AGENTCORE_SERVICES_AVAILABLE = True
except ImportError:
    # Fallback for older versions or when services are not available
    MemoryClient = None
    GatewayClient = None
    IdentityClient = None
    AGENTCORE_SERVICES_AVAILABLE = False

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
logger.info(f"AgentCore services available: {AGENTCORE_SERVICES_AVAILABLE}")

# Initialize AgentCore application
agentcore_app = BedrockAgentCoreApp()

# Initialize the agent lazily
_agent = None
_memory_client = None
_gateway_client = None

def get_memory_client():
    """Get or create the memory client for knowledge persistence."""
    global _memory_client
    if _memory_client is None and AGENTCORE_SERVICES_AVAILABLE and MemoryClient:
        try:
            _memory_client = MemoryClient()
            logger.info("Initialized AgentCore Memory client")
        except Exception as e:
            logger.warning(f"Failed to initialize Memory client: {e}")
            _memory_client = None
    return _memory_client

def get_gateway_client():
    """Get or create the gateway client for knowledge base integration."""
    global _gateway_client
    if _gateway_client is None and AGENTCORE_SERVICES_AVAILABLE and GatewayClient:
        try:
            _gateway_client = GatewayClient()
            logger.info("Initialized AgentCore Gateway client")
        except Exception as e:
            logger.warning(f"Failed to initialize Gateway client: {e}")
            _gateway_client = None
    return _gateway_client

def query_knowledge_base_via_gateway(gateway_client, query: str) -> Optional[str]:
    """
    Query knowledge base through AgentCore Gateway.
    
    Args:
        gateway_client: The gateway client instance
        query: The search query
    
    Returns:
        Knowledge base response or None if no results
    """
    try:
        # This is a placeholder implementation
        # In a real scenario, this would call specific knowledge base APIs
        # configured through the gateway client
        
        # Example: Call a knowledge base API endpoint
        kb_endpoint = os.environ.get("KNOWLEDGE_BASE_ENDPOINT")
        if not kb_endpoint:
            logger.debug("No knowledge base endpoint configured")
            return None
        
        # Simulate knowledge base query
        # In practice, this would make an actual API call through the gateway
        logger.debug(f"Querying knowledge base with: {query}")
        
        # Placeholder return - replace with actual implementation
        return f"Knowledge base context for: {query}"
        
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return None

def setup_knowledge_base_integration():
    """
    Setup knowledge base integration using AgentCore Gateway.
    
    This function configures connections to external knowledge bases
    and APIs that can augment the agent's responses.
    """
    if not AGENTCORE_SERVICES_AVAILABLE:
        logger.info("AgentCore services not available, skipping knowledge base setup")
        return False
    
    gateway_client = get_gateway_client()
    if not gateway_client:
        logger.warning("Gateway client not available, knowledge base integration disabled")
        return False
    
    try:
        # Example: Configure knowledge base endpoints
        # This would typically involve setting up API endpoints, authentication, etc.
        knowledge_base_config = {
            "knowledge_bases": [
                {
                    "name": "primary_kb",
                    "type": "api",
                    "endpoint": os.environ.get("KNOWLEDGE_BASE_ENDPOINT"),
                    "auth_required": True
                }
            ]
        }
        
        # Register knowledge base with gateway
        # gateway_client.register_knowledge_source(knowledge_base_config)
        logger.info("Knowledge base integration configured")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup knowledge base integration: {e}")
        return False

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

def chat_with_agent(user_message: str, session_id: Optional[str] = None, use_knowledge_base: bool = True) -> str:
    """
    Enhanced function to chat with the agent using AgentCore capabilities.
    
    Args:
        user_message: The user's input message
        session_id: Optional session ID for memory persistence
        use_knowledge_base: Whether to use knowledge base augmentation
    
    Returns:
        The agent's response
    """
    logger.info(f"Processing user message: {user_message[:100]}...")
    
    try:
        agent = get_agent()
        
        # Enhanced message with memory and knowledge base context
        enhanced_message = user_message
        
        # Add memory context if available
        if session_id and AGENTCORE_SERVICES_AVAILABLE:
            memory_client = get_memory_client()
            if memory_client:
                try:
                    # Retrieve conversation history for context
                    memory_context = memory_client.get_session_memory(session_id)
                    if memory_context:
                        enhanced_message = f"Previous context: {memory_context}\n\nCurrent message: {user_message}"
                        logger.info("Added memory context to message")
                except Exception as e:
                    logger.warning(f"Failed to retrieve memory context: {e}")
        
        # Add knowledge base context if available and requested
        if use_knowledge_base and AGENTCORE_SERVICES_AVAILABLE:
            gateway_client = get_gateway_client()
            if gateway_client:
                try:
                    # Query knowledge base for relevant information
                    # This would typically involve calling your knowledge base API
                    # through the gateway client
                    knowledge_context = query_knowledge_base_via_gateway(gateway_client, user_message)
                    if knowledge_context:
                        enhanced_message = f"{enhanced_message}\n\nRelevant knowledge: {knowledge_context}"
                        logger.info("Added knowledge base context to message")
                except Exception as e:
                    logger.warning(f"Failed to retrieve knowledge base context: {e}")
        
        # Process with the agent
        result = agent(enhanced_message)
        response_text = str(result)  # AgentResult has __str__ method
        
        # Store the interaction in memory if session_id is provided
        if session_id and AGENTCORE_SERVICES_AVAILABLE:
            memory_client = get_memory_client()
            if memory_client:
                try:
                    memory_client.store_interaction(
                        session_id=session_id,
                        user_message=user_message,
                        agent_response=response_text
                    )
                    logger.info("Stored interaction in memory")
                except Exception as e:
                    logger.warning(f"Failed to store interaction in memory: {e}")
        
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
                
            # Use a simple session ID for local testing
            session_id = "local_session" if AGENTCORE_SERVICES_AVAILABLE else None
            response = chat_with_agent(user_input, session_id=session_id)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            print(f"Error: {e}")
    
    logger.info("Chat session ended")

# AgentCore entrypoint for deployment
@agentcore_app.entrypoint
def agent_invocation(payload, context=None):
    """
    AgentCore entrypoint for agent invocation.
    
    This function is called when the agent is deployed via AgentCore
    and receives requests through the AgentCore runtime.
    
    Args:
        payload: Input payload containing the user message and optional parameters
        context: AgentCore context object (optional)
    
    Returns:
        Dict containing the agent's response
    """
    logger.info("AgentCore entrypoint invoked")
    
    try:
        # Extract message and optional parameters from payload
        user_message = payload.get("prompt", payload.get("message", ""))
        session_id = payload.get("session_id", None)
        use_knowledge_base = payload.get("use_knowledge_base", True)
        
        if not user_message:
            return {
                "error": "No prompt or message found in input. Please provide a JSON payload with 'prompt' or 'message' key."
            }
        
        # Process the message with enhanced capabilities
        response = chat_with_agent(
            user_message=user_message,
            session_id=session_id,
            use_knowledge_base=use_knowledge_base
        )
        
        return {
            "result": response,
            "session_id": session_id,
            "agentcore_enhanced": AGENTCORE_SERVICES_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"Error in AgentCore entrypoint: {e}", exc_info=True)
        return {
            "error": f"Agent processing failed: {str(e)}"
        }

def run_agentcore_app():
    """Run the AgentCore application for deployment."""
    logger.info("Starting AgentCore application")
    agentcore_app.run()

if __name__ == "__main__":
    # Check if running in AgentCore mode or local mode
    agentcore_mode = os.environ.get("AGENTCORE_MODE", "false").lower() == "true"
    
    if agentcore_mode:
        # Run as AgentCore application for deployment
        run_agentcore_app()
    else:
        # Run local interactive mode
        main()