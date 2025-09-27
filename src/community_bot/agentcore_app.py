# src/community_bot/agentcore_app.py

import os
import sys
import requests

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
from community_bot.prompt_loader import load_prompt_bundle

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

try:
    _PROMPT_BUNDLE = load_prompt_bundle(settings)
    logger.info(
        "Loaded prompt profile '%s'%s for AgentCore backend",
        _PROMPT_BUNDLE.profile,
        " with user primer" if _PROMPT_BUNDLE.user else "",
    )
    if _PROMPT_BUNDLE.extras:
        logger.debug(
            "Prompt extras discovered for profile '%s': %s",
            _PROMPT_BUNDLE.profile,
            ", ".join(sorted(_PROMPT_BUNDLE.extras.keys())),
        )
except Exception:  # Propagate after logging for visibility
    logger.exception("Failed to load prompt bundle for AgentCore backend")
    raise

_PROMPT_USER_ROLE = (settings.prompt_user_role or "user").strip() or "user"

logger.info(f"Initializing AgentCore app with LLM provider: {LLM_PROVIDER}")
logger.info(f"AgentCore services available: {AGENTCORE_SERVICES_AVAILABLE}")

# Initialize AgentCore application
agentcore_app = BedrockAgentCoreApp()

# Initialize the agent lazily
_agent = None
_memory_client = None
_gateway_client = None


def _compose_agentcore_prompt(
    user_message: str,
    *,
    memory_context: Optional[str] = None,
    knowledge_context: Optional[str] = None,
) -> str:
    """Compose the final prompt for AgentCore mode using the loaded bundle."""

    sections: list[str] = []

    system_prompt = (_PROMPT_BUNDLE.system or "").strip()
    if system_prompt:
        sections.append(f"[System Instructions]\n{system_prompt}")

    user_primer = (_PROMPT_BUNDLE.user or "").strip()
    if user_primer:
        role_label = _PROMPT_USER_ROLE.title()
        sections.append(f"[{role_label} Primer]\n{user_primer}")

    if _PROMPT_BUNDLE.extras:
        for name in sorted(_PROMPT_BUNDLE.extras.keys()):
            content = (_PROMPT_BUNDLE.extras.get(name) or "").strip()
            if not content:
                continue
            label = name.replace("_", " ").strip() or name
            sections.append(f"[{label}]\n{content}")

    if memory_context:
        memory_text = memory_context.strip()
        if memory_text:
            sections.append(f"[Conversation Memory]\n{memory_text}")

    if knowledge_context:
        knowledge_text = knowledge_context.strip()
        if knowledge_text:
            sections.append(f"[Relevant Knowledge]\n{knowledge_text}")

    sections.append(f"[{_PROMPT_USER_ROLE.title()} Message]\n{user_message}")

    return "\n\n".join(sections)

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
    Query knowledge base through AgentCore Gateway or direct API.
    
    Args:
        gateway_client: The gateway client instance
        query: The search query
    
    Returns:
        Knowledge base response or None if no results
    """
    try:
        logger.debug(f"Querying knowledge base with: {query[:100]}...")
        
        # Try AgentCore Gateway approach first
        kb_gateway_id = os.environ.get("KB_GATEWAY_ID")
        kb_gateway_endpoint = os.environ.get("KB_GATEWAY_ENDPOINT")
        
        if kb_gateway_id and kb_gateway_endpoint and gateway_client:
            try:
                # Use AgentCore Gateway MCP tools
                result = _query_via_agentcore_gateway(gateway_client, kb_gateway_id, query)
                if result:
                    logger.debug("Successfully queried via AgentCore Gateway")
                    return result
            except Exception as gateway_error:
                logger.warning(f"AgentCore Gateway query failed, trying direct approach: {gateway_error}")
        
        # Fallback to direct API approach
        kb_direct_endpoint = os.environ.get("KB_DIRECT_ENDPOINT")
        if kb_direct_endpoint:
            result = _query_via_direct_api(kb_direct_endpoint, query)
            if result:
                logger.debug("Successfully queried via direct API")
                return result
        
        logger.debug("No knowledge base configured or available")
        return None
        
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return None

def _query_via_agentcore_gateway(gateway_client, gateway_id: str, query: str) -> Optional[str]:
    """
    Query knowledge base using AgentCore Gateway MCP tools.
    
    Args:
        gateway_client: AgentCore gateway client
        gateway_id: Gateway ID
        query: Search query
    
    Returns:
        Query result or None
    """
    try:
        # Use MCP tools via AgentCore Gateway
        tool_result = gateway_client.invoke_tool(
            gateway_id=gateway_id,
            tool_name="kb-query-tool",
            parameters={
                "query": query,
                "max_results": 5,
                "include_metadata": True
            }
        )
        
        if tool_result and tool_result.get("content"):
            return tool_result["content"]
        
        return None
        
    except Exception as e:
        logger.warning(f"AgentCore Gateway query failed: {e}")
        return None

def _query_via_direct_api(kb_endpoint: str, query: str) -> Optional[str]:
    """
    Query knowledge base using direct API calls.
    
    Args:
        kb_endpoint: Knowledge base API endpoint
        query: Search query
    
    Returns:
        Query result or None
    """
    try:        
        kb_api_key = os.environ.get("KB_DIRECT_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {kb_api_key}" if kb_api_key else ""
        }
        
        # Standard knowledge base query format
        payload = {
            "query": query,
            "max_results": 5,
            "include_metadata": True
        }
        
        response = requests.post(
            f"{kb_endpoint}/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract relevant context from response
            if result.get("results"):
                context_items = []
                for item in result["results"][:3]:  # Use top 3 results
                    content = item.get("content", item.get("text", ""))
                    if content:
                        context_items.append(content)
                
                if context_items:
                    return "\n".join(context_items)
            
            # Fallback to direct content
            return result.get("content", result.get("answer"))
        
        else:
            logger.warning(f"Knowledge base API returned status {response.status_code}: {response.text}")
            return None
        
    except Exception as e:
        logger.warning(f"Direct API query failed: {e}")
        return None

def setup_knowledge_base_integration():
    """
    Setup knowledge base integration using AgentCore Gateway.
    
    This function configures connections to external knowledge bases
    and APIs that can augment the agent's responses by converting them
    into MCP (Model Context Protocol) tools via AgentCore Gateway.
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    if not AGENTCORE_SERVICES_AVAILABLE:
        logger.info("AgentCore services not available, skipping knowledge base setup")
        return False
    
    gateway_client = get_gateway_client()
    if not gateway_client:
        logger.warning("Gateway client not available, knowledge base integration disabled")
        return False
    
    try:
        # Check for knowledge base configuration
        kb_endpoint = os.environ.get("KNOWLEDGE_BASE_ENDPOINT")
        kb_api_key = os.environ.get("KNOWLEDGE_BASE_API_KEY")
        
        if not kb_endpoint:
            logger.info("No KNOWLEDGE_BASE_ENDPOINT configured, skipping knowledge base setup")
            logger.info("To enable knowledge base: set KNOWLEDGE_BASE_ENDPOINT environment variable")
            return False
        
        logger.info(f"Setting up knowledge base integration with endpoint: {kb_endpoint}")
        
        # Create AgentCore Gateway for knowledge base API
        # This converts your knowledge base API into MCP tools
        gateway_config = {
            "name": "knowledge-base-gateway",
            "description": "Gateway for knowledge base queries",
            "targets": [
                {
                    "name": "kb-query-tool",
                    "type": "api",
                    "endpoint": kb_endpoint,
                    "description": "Query knowledge base for relevant information",
                    "authentication": {
                        "type": "api_key" if kb_api_key else "none",
                        "api_key": kb_api_key
                    }
                }
            ]
        }
        
        # Register gateway with AgentCore
        try:
            gateway_response = gateway_client.create_gateway(gateway_config)
            logger.info(f"Knowledge base gateway created successfully: {gateway_response.get('gatewayId', 'Unknown ID')}")
            
            # Store gateway info for later use
            os.environ["KB_GATEWAY_ID"] = gateway_response.get('gatewayId', '')
            os.environ["KB_GATEWAY_ENDPOINT"] = gateway_response.get('endpoint', '')
            
        except Exception as gateway_error:
            logger.warning(f"Failed to create gateway, using direct API approach: {gateway_error}")
            # Fallback to direct API integration
            return _setup_direct_kb_integration(kb_endpoint, kb_api_key)
        
        logger.info("Knowledge base integration configured successfully via AgentCore Gateway")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup knowledge base integration: {e}")
        return False

def _setup_direct_kb_integration(kb_endpoint: str, kb_api_key: Optional[str] = None):
    """
    Fallback function to setup direct knowledge base integration 
    when AgentCore Gateway is not available.
    
    Args:
        kb_endpoint: Knowledge base API endpoint
        kb_api_key: Optional API key for authentication
    
    Returns:
        bool: True if setup successful
    """
    try:
        logger.info("Setting up direct knowledge base integration (fallback mode)")
        
        # Store configuration for direct usage
        os.environ["KB_DIRECT_ENDPOINT"] = kb_endpoint
        if kb_api_key:
            os.environ["KB_DIRECT_API_KEY"] = kb_api_key
        
        # Test connectivity to knowledge base
        headers = {"Authorization": f"Bearer {kb_api_key}"} if kb_api_key else {}
        
        # Simple health check
        try:
            response = requests.get(f"{kb_endpoint}/health", headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("Knowledge base endpoint is accessible")
            else:
                logger.warning(f"Knowledge base endpoint returned status: {response.status_code}")
        except requests.exceptions.RequestException as req_error:
            logger.warning(f"Could not verify knowledge base connectivity: {req_error}")
        
        logger.info("Direct knowledge base integration configured")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup direct knowledge base integration: {e}")
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
        
        memory_context: Optional[str] = None
        knowledge_context: Optional[str] = None
        
        # Add memory context if available
        if session_id and AGENTCORE_SERVICES_AVAILABLE:
            memory_client = get_memory_client()
            if memory_client:
                try:
                    # Retrieve conversation history for context
                    memory_context = memory_client.get_session_memory(session_id)
                    if memory_context:
                        logger.info("Including memory context in AgentCore prompt")
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
                        logger.info("Including knowledge base context in AgentCore prompt")
                except Exception as e:
                    logger.warning(f"Failed to retrieve knowledge base context: {e}")
        
        enhanced_message = _compose_agentcore_prompt(
            user_message=user_message,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )

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