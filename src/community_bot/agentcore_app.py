# src/community_bot/agentcore_app.py

import json
import os
import sys
import requests

from pathlib import Path
from typing import Any, Dict, Optional, TypedDict

from strands import Agent, tool
from strands.models.ollama import OllamaModel
from strands.models import BedrockModel
from strands.types.tools import ToolContext
from typing_extensions import NotRequired

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


class KnowledgeBaseResponse(TypedDict):
    """Structured representation of knowledge base results."""

    content: str
    source: NotRequired[str]
    raw: NotRequired[Any]


def _truncate_for_discord(text: str, limit: int = 1900) -> str:
    """Discord hard-limits messages to ~2000 characters. Trim responsibly."""

    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _compose_agentcore_prompt(
    user_message: str,
    *,
    memory_context: Optional[str] = None,
    knowledge_context: Optional[str] = None,
) -> str:
    """Compose the final prompt for AgentCore mode using the loaded bundle."""

    logger.debug(f"[PROMPT COMPOSE] Building prompt with user_message: {len(user_message)} chars")
    logger.debug(f"[PROMPT COMPOSE] Memory context: {len(memory_context) if memory_context else 0} chars")
    logger.debug(f"[PROMPT COMPOSE] Knowledge context: {len(knowledge_context) if knowledge_context else 0} chars")

    sections: list[str] = []

    system_prompt = (_PROMPT_BUNDLE.system or "").strip()
    if system_prompt:
        logger.debug(f"[PROMPT COMPOSE] Adding system prompt: {len(system_prompt)} chars")
        sections.append(f"[System Instructions]\n{system_prompt}")

    user_primer = (_PROMPT_BUNDLE.user or "").strip()
    if user_primer:
        role_label = _PROMPT_USER_ROLE.title()
        logger.debug(f"[PROMPT COMPOSE] Adding user primer: {len(user_primer)} chars")
        sections.append(f"[{role_label} Primer]\n{user_primer}")

    if _PROMPT_BUNDLE.extras:
        for name in sorted(_PROMPT_BUNDLE.extras.keys()):
            content = (_PROMPT_BUNDLE.extras.get(name) or "").strip()
            if not content:
                continue
            label = name.replace("_", " ").strip() or name
            logger.debug(f"[PROMPT COMPOSE] Adding extra section '{label}': {len(content)} chars")
            sections.append(f"[{label}]\n{content}")

    if memory_context:
        memory_text = memory_context.strip()
        if memory_text:
            logger.debug(f"[PROMPT COMPOSE] Adding memory context: {len(memory_text)} chars")
            sections.append(f"[Conversation Memory]\n{memory_text}")

    if knowledge_context:
        knowledge_text = knowledge_context.strip()
        if knowledge_text:
            logger.debug(f"[PROMPT COMPOSE] Adding knowledge context: {len(knowledge_text)} chars")
            sections.append(f"[Relevant Knowledge]\n{knowledge_text}")

    sections.append(f"[{_PROMPT_USER_ROLE.title()} Message]\n{user_message}")

    final_prompt = "\n\n".join(sections)
    logger.debug(f"[PROMPT COMPOSE] Final prompt composed: {len(final_prompt)} chars, {len(sections)} sections")
    
    return final_prompt

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

def query_knowledge_base_via_gateway(
    gateway_client,
    query: str,
    *,
    max_results: int = 5,
    include_metadata: bool = True,
) -> Optional[KnowledgeBaseResponse]:
    """
    Query knowledge base through AgentCore Gateway or direct API.
    
    Args:
        gateway_client: The gateway client instance
        query: The search query
    
    Returns:
        Knowledge base response or None if no results
    """
    try:
        logger.info(f"[KB QUERY] Starting knowledge base query with: {query[:100]}...")
        logger.debug(f"[KB QUERY] Query parameters: max_results={max_results}, include_metadata={include_metadata}")
        
        # Try AgentCore Gateway approach first
        kb_gateway_id = os.environ.get("KB_GATEWAY_ID")
        kb_gateway_endpoint = os.environ.get("KB_GATEWAY_ENDPOINT")
        
        logger.debug(f"[KB QUERY] Gateway configuration: gateway_id={kb_gateway_id}, endpoint={kb_gateway_endpoint}")
        logger.debug(f"[KB QUERY] Gateway client available: {gateway_client is not None}")
        
        if kb_gateway_id and kb_gateway_endpoint and gateway_client:
            logger.info("[KB QUERY] Attempting AgentCore Gateway query...")
            try:
                # Use AgentCore Gateway MCP tools
                result = _query_via_agentcore_gateway(
                    gateway_client,
                    kb_gateway_id,
                    query,
                    max_results=max_results,
                    include_metadata=include_metadata,
                )
                logger.debug(f"[KB QUERY] Gateway result type: {type(result)}")
                logger.debug(f"[KB QUERY] Gateway result: {str(result)[:500]}")
                
                content = _extract_content_from_result(result)
                if content:
                    logger.info(f"[KB QUERY] ✅ Successfully queried via AgentCore Gateway - {len(content)} characters")
                    return {
                        "content": content,
                        "source": "gateway",
                        "raw": result,
                    }
                else:
                    logger.warning("[KB QUERY] Gateway query returned result but no content could be extracted")
            except Exception as gateway_error:
                logger.error(f"[KB QUERY] ❌ AgentCore Gateway query failed: {gateway_error}", exc_info=True)
                logger.info("[KB QUERY] Falling back to direct API approach...")
        else:
            logger.info("[KB QUERY] Gateway not configured, checking direct API...")
        
        # Fallback to direct API approach
        kb_direct_endpoint = os.environ.get("KB_DIRECT_ENDPOINT")
        logger.debug(f"[KB QUERY] Direct endpoint: {kb_direct_endpoint}")
        
        if kb_direct_endpoint:
            logger.info("[KB QUERY] Attempting direct API query...")
            result = _query_via_direct_api(
                kb_direct_endpoint,
                query,
                max_results=max_results,
                include_metadata=include_metadata,
            )
            logger.debug(f"[KB QUERY] Direct API result type: {type(result)}")
            logger.debug(f"[KB QUERY] Direct API result: {str(result)[:500]}")
            
            content = _extract_content_from_result(result)
            if content:
                logger.info(f"[KB QUERY] ✅ Successfully queried via direct API - {len(content)} characters")
                return {
                    "content": content,
                    "source": "direct",
                    "raw": result,
                }
            else:
                logger.warning("[KB QUERY] Direct API query returned result but no content could be extracted")
        
        logger.warning("[KB QUERY] ❌ No knowledge base configured or available")
        logger.info("[KB QUERY] Configuration check:")
        logger.info(f"  - KB_GATEWAY_ID: {'SET' if kb_gateway_id else 'NOT SET'}")
        logger.info(f"  - KB_GATEWAY_ENDPOINT: {'SET' if kb_gateway_endpoint else 'NOT SET'}")
        logger.info(f"  - KB_DIRECT_ENDPOINT: {'SET' if kb_direct_endpoint else 'NOT SET'}")
        logger.info(f"  - Gateway client: {'AVAILABLE' if gateway_client else 'NOT AVAILABLE'}")
        return None
        
    except Exception as e:
        logger.error(f"[KB QUERY] ❌ Error querying knowledge base: {e}", exc_info=True)
        return None

def _query_via_agentcore_gateway(
    gateway_client,
    gateway_id: str,
    query: str,
    *,
    max_results: int = 5,
    include_metadata: bool = True,
) -> Optional[Any]:
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
        logger.info(f"[GATEWAY] Invoking AgentCore Gateway tool...")
        logger.debug(f"[GATEWAY] Gateway ID: {gateway_id}")
        logger.debug(f"[GATEWAY] Tool name: kb-query-tool")
        
        # Use MCP tools via AgentCore Gateway
        parameters: Dict[str, Any] = {
            "query": query,
            "include_metadata": include_metadata,
        }
        if max_results is not None:
            parameters["max_results"] = max_results
        
        logger.debug(f"[GATEWAY] Tool parameters: {parameters}")

        logger.info("[GATEWAY] Calling gateway_client.invoke_tool()...")
        tool_result = gateway_client.invoke_tool(
            gateway_id=gateway_id,
            tool_name="kb-query-tool",
            parameters=parameters,
        )
        
        logger.info(f"[GATEWAY] Tool invocation completed")
        logger.debug(f"[GATEWAY] Result type: {type(tool_result)}")
        logger.debug(f"[GATEWAY] Result value: {str(tool_result)[:1000]}")
        
        if tool_result:
            logger.info("[GATEWAY] ✅ Tool returned result")
            return tool_result
        else:
            logger.warning("[GATEWAY] ⚠️ Tool returned empty/None result")
            return None
        
    except Exception as e:
        logger.error(f"[GATEWAY] ❌ Gateway query failed: {e}", exc_info=True)
        return None

def _query_via_direct_api(
    kb_endpoint: str,
    query: str,
    *,
    max_results: int = 5,
    include_metadata: bool = True,
) -> Optional[Any]:
    """
    Query knowledge base using direct API calls.
    
    Args:
        kb_endpoint: Knowledge base API endpoint
        query: Search query
    
    Returns:
        Query result or None
    """
    try:
        logger.info(f"[DIRECT API] Querying knowledge base endpoint: {kb_endpoint}")
        
        kb_api_key = os.environ.get("KB_DIRECT_API_KEY")
        logger.debug(f"[DIRECT API] API key: {'SET' if kb_api_key else 'NOT SET'}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {kb_api_key}" if kb_api_key else ""
        }
        
        # Standard knowledge base query format
        payload = {
            "query": query,
            "max_results": max_results,
            "include_metadata": include_metadata,
        }
        
        logger.debug(f"[DIRECT API] Request payload: {payload}")
        logger.debug(f"[DIRECT API] Request URL: {kb_endpoint}/query")
        
        logger.info("[DIRECT API] Sending POST request...")
        response = requests.post(
            f"{kb_endpoint}/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"[DIRECT API] Response status: {response.status_code}")
        logger.debug(f"[DIRECT API] Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("[DIRECT API] ✅ Received successful response")
            result = response.json()
            logger.debug(f"[DIRECT API] Response body (first 1000 chars): {str(result)[:1000]}")
            
            if isinstance(result.get("results"), list):
                original_count = len(result["results"])
                if max_results is not None:
                    result = result.copy()
                    result["results"] = result["results"][:max_results]
                    logger.debug(f"[DIRECT API] Truncated results from {original_count} to {len(result['results'])}")
            
            return result
        else:
            logger.error(f"[DIRECT API] ❌ API returned status {response.status_code}")
            logger.debug(f"[DIRECT API] Response text: {response.text[:500]}")
            return None
        
    except requests.exceptions.Timeout as e:
        logger.error(f"[DIRECT API] ❌ Request timeout: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[DIRECT API] ❌ Connection error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[DIRECT API] ❌ Request failed: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"[DIRECT API] ❌ Unexpected error: {e}", exc_info=True)
        return None


def _extract_content_from_result(result: Any) -> Optional[str]:
    """Best-effort extraction of human-readable content from varied KB responses."""
    
    logger.debug(f"[EXTRACT] Extracting content from result type: {type(result)}")

    if not result:
        logger.debug("[EXTRACT] Result is None or empty")
        return None

    if isinstance(result, str):
        extracted = result.strip() or None
        logger.debug(f"[EXTRACT] Result is string - {len(extracted) if extracted else 0} characters")
        return extracted

    if isinstance(result, dict):
        logger.debug(f"[EXTRACT] Result is dict with keys: {list(result.keys())}")
        
        # Try common content keys
        for key in ("content", "text", "answer"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                logger.info(f"[EXTRACT] ✅ Extracted content from '{key}' field - {len(value.strip())} characters")
                return value.strip()

        # Try extracting from results array
        if isinstance(result.get("results"), list):
            results_list = result["results"]
            logger.debug(f"[EXTRACT] Found 'results' array with {len(results_list)} items")
            
            snippets: list[str] = []
            for idx, item in enumerate(results_list):
                if not isinstance(item, dict):
                    logger.debug(f"[EXTRACT] Result item {idx} is not a dict, skipping")
                    continue
                    
                snippet = item.get("content") or item.get("text")
                if isinstance(snippet, str) and snippet.strip():
                    snippets.append(snippet.strip())
                    logger.debug(f"[EXTRACT] Extracted snippet {idx}: {len(snippet.strip())} characters")
                else:
                    logger.debug(f"[EXTRACT] Result item {idx} has no extractable content")
            
            if snippets:
                combined = "\n\n".join(snippets)
                logger.info(f"[EXTRACT] ✅ Combined {len(snippets)} snippets - {len(combined)} total characters")
                return combined
            else:
                logger.warning("[EXTRACT] ⚠️ Results array exists but no snippets could be extracted")

    logger.warning(f"[EXTRACT] ❌ Could not extract content from result: {str(result)[:200]}")
    return None


@tool(
    name="kb-query-tool",
    description="Query the configured knowledge base for relevant context",
    context=True,
)
def kb_query_tool(
    query: str,
    max_results: int = 5,
    include_metadata: bool = True,
    tool_context: ToolContext | None = None,
) -> Dict[str, Any]:
    """Return knowledge base snippets that match the provided query."""

    logger.info("=" * 80)
    logger.info("[KB TOOL] kb-query-tool invoked by Strands agent")
    logger.info("=" * 80)

    trimmed_query = query.strip()
    if not trimmed_query:
        logger.warning("[KB TOOL] ⚠️ Received empty query")
        return {
            "status": "error",
            "content": [{"text": "Knowledge base query cannot be empty."}],
        }

    logger.info(f"[KB TOOL] Query: '{trimmed_query[:100]}{'...' if len(trimmed_query) > 100 else ''}'")
    logger.info(f"[KB TOOL] Parameters: max_results={max_results}, include_metadata={include_metadata}")
    
    if tool_context:
        logger.debug(f"[KB TOOL] Tool use ID: {tool_context.tool_use.get('toolUseId')}")
        logger.debug(f"[KB TOOL] Tool context: {tool_context}")

    gateway_client = get_gateway_client() if AGENTCORE_SERVICES_AVAILABLE else None
    logger.info(f"[KB TOOL] Gateway client: {'AVAILABLE' if gateway_client else 'NOT AVAILABLE'}")
    logger.info(f"[KB TOOL] AgentCore services: {'AVAILABLE' if AGENTCORE_SERVICES_AVAILABLE else 'NOT AVAILABLE'}")
    
    logger.info("[KB TOOL] Calling query_knowledge_base_via_gateway()...")
    result = query_knowledge_base_via_gateway(
        gateway_client,
        trimmed_query,
        max_results=max_results,
        include_metadata=include_metadata,
    )

    logger.info(f"[KB TOOL] Query result: {result is not None}")
    if result:
        logger.debug(f"[KB TOOL] Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

    content_value = (result or {}).get("content") if result else None

    if not content_value:
        logger.warning(f"[KB TOOL] ❌ No results found for query: {trimmed_query[:100]}")
        logger.info("[KB TOOL] Returning error response to agent")
        return {
            "status": "error",
            "content": [{"text": "No knowledge base entries matched the query."}],
        }

    logger.info(f"[KB TOOL] ✅ Found content: {len(content_value)} characters")
    response_text = content_value.strip()

    source_value = result.get("source") if result else None
    if source_value:
        logger.debug(f"[KB TOOL] Content source: {source_value}")
        response_text = f"Source: {source_value}\n\n" + response_text

    raw_value = result.get("raw") if result else None
    if include_metadata and raw_value is not None:
        try:
            raw_json = json.dumps(raw_value, indent=2)
            metadata_snippet = _truncate_for_discord(raw_json, 1500)
            response_text = "\n\n".join(
                [response_text, f"```json\n{metadata_snippet}\n```"]
            )
            logger.debug(f"[KB TOOL] Included metadata: {len(metadata_snippet)} characters")
        except (TypeError, ValueError):
            logger.debug("[KB TOOL] Could not serialize raw metadata")

    response_text = _truncate_for_discord(response_text)
    logger.info(f"[KB TOOL] Final response: {len(response_text)} characters")

    if tool_context:
        logger.info(
            f"[KB TOOL] Returning success to agent (tool_use_id={tool_context.tool_use.get('toolUseId')})"
        )
    else:
        logger.info("[KB TOOL] Returning success to agent")

    logger.info("=" * 80)

    return {
        "status": "success",
        "content": [{"text": response_text}],
    }

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
        logger.info("=" * 80)
        logger.info("[AGENT INIT] Initializing Strands Agent...")
        logger.info("=" * 80)
        
        # Use forced provider if set, otherwise use environment variable
        provider = _force_provider or LLM_PROVIDER
        
        logger.info(f"[AGENT INIT] LLM Provider: {provider}")
        logger.info(f"[AGENT INIT] Forced provider: {_force_provider}")
        logger.info(f"[AGENT INIT] Environment LLM_PROVIDER: {LLM_PROVIDER}")
        
        if provider == "ollama":
            # Assumes Ollama is running locally
            model_name = settings.ollama_model or "llama3"  # Default fallback
            base_url = settings.ollama_base_url or "http://localhost:11434"  # Default fallback
            logger.info(f"[AGENT INIT] Configuring Ollama model: {model_name}")
            logger.info(f"[AGENT INIT] Ollama base URL: {base_url}")
            
            try:
                model = OllamaModel(
                    host=base_url,
                    model_id=model_name
                )
                logger.info("[AGENT INIT] ✅ Ollama model configured successfully")
            except Exception as e:
                logger.error(f"[AGENT INIT] ❌ Failed to configure Ollama model: {e}", exc_info=True)
                raise
                
        elif provider == "bedrock":
            # Configure for Bedrock (e.g., Claude)
            model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
            logger.info(f"[AGENT INIT] Configuring Bedrock model: {model_id}")
            
            try:
                model = BedrockModel(
                    model_id=model_id,
                    temperature=0.3,
                    streaming=True
                )
                logger.info("[AGENT INIT] ✅ Bedrock model configured successfully")
            except Exception as e:
                logger.error(f"[AGENT INIT] ❌ Failed to configure Bedrock model: {e}", exc_info=True)
                raise
        else:
            logger.error(f"[AGENT INIT] ❌ Unknown LLM provider: {provider}")
            raise ValueError(f"Unknown LLM provider: {provider}")

        tools = [kb_query_tool]
        logger.info(f"[AGENT INIT] Registering {len(tools)} tools: {[t.__name__ for t in tools]}")

        try:
            _agent = Agent(model=model, tools=tools)
            logger.info("[AGENT INIT] ✅ Strands Agent initialized successfully")
        except Exception as e:
            logger.error(f"[AGENT INIT] ❌ Failed to initialize Agent: {e}", exc_info=True)
            raise
        
        logger.info("=" * 80)
    else:
        logger.debug("[AGENT INIT] Using existing agent instance")
    
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
    logger.info("=" * 80)
    logger.info(f"[CHAT] Processing user message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
    logger.info(f"[CHAT] Session ID: {session_id}")
    logger.info(f"[CHAT] Use knowledge base: {use_knowledge_base}")
    logger.info("=" * 80)
    
    try:
        logger.info("[CHAT] Getting agent instance...")
        agent = get_agent()
        logger.debug(f"[CHAT] Agent type: {type(agent)}")
        
        memory_context: Optional[str] = None
        knowledge_context: Optional[str] = None
        
        # Add memory context if available
        if session_id and AGENTCORE_SERVICES_AVAILABLE:
            logger.info(f"[CHAT] Retrieving memory for session: {session_id}")
            memory_client = get_memory_client()
            if memory_client:
                try:
                    # Retrieve conversation history for context
                    memory_context = memory_client.get_session_memory(session_id)
                    if memory_context:
                        logger.info(f"[CHAT] ✅ Memory context retrieved: {len(memory_context)} characters")
                    else:
                        logger.debug("[CHAT] No memory context found for session")
                except Exception as e:
                    logger.error(f"[CHAT] ❌ Failed to retrieve memory context: {e}", exc_info=True)
            else:
                logger.debug("[CHAT] Memory client not available")
        else:
            logger.debug("[CHAT] Skipping memory retrieval (no session_id or services unavailable)")
        
        # Add knowledge base context if available and requested
        if use_knowledge_base:
            logger.info("[CHAT] Knowledge base augmentation enabled")
            gateway_client = get_gateway_client() if AGENTCORE_SERVICES_AVAILABLE else None
            direct_available = os.environ.get("KB_DIRECT_ENDPOINT") is not None

            logger.debug(f"[CHAT] Gateway client: {'AVAILABLE' if gateway_client else 'NOT AVAILABLE'}")
            logger.debug(f"[CHAT] Direct KB endpoint: {'CONFIGURED' if direct_available else 'NOT CONFIGURED'}")

            if gateway_client or direct_available:
                try:
                    logger.info("[CHAT] Querying knowledge base for context...")
                    knowledge_result = query_knowledge_base_via_gateway(
                        gateway_client,
                        user_message,
                    )

                    if knowledge_result and knowledge_result.get("content"):
                        knowledge_context = knowledge_result["content"]
                        logger.info(
                            f"[CHAT] ✅ Knowledge base context retrieved (source={knowledge_result.get('source', 'unknown')}): {len(knowledge_context)} characters"
                        )
                        raw_snapshot = knowledge_result.get("raw")
                        if raw_snapshot is not None:
                            logger.debug(
                                f"[CHAT] Knowledge base raw snapshot: {str(raw_snapshot)[:500]}"
                            )
                    else:
                        logger.warning("[CHAT] ⚠️ Knowledge base query returned no content")
                except Exception as e:
                    logger.error(f"[CHAT] ❌ Failed to retrieve knowledge base context: {e}", exc_info=True)
            else:
                logger.warning("[CHAT] ⚠️ No knowledge base access available (neither gateway nor direct)")
        else:
            logger.info("[CHAT] Knowledge base augmentation disabled")
        
        logger.info("[CHAT] Composing enhanced prompt...")
        enhanced_message = _compose_agentcore_prompt(
            user_message=user_message,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )
        
        logger.debug(f"[CHAT] Enhanced message length: {len(enhanced_message)} characters")
        logger.debug(f"[CHAT] Enhanced message preview: {enhanced_message[:300]}...")
        logger.debug("=" * 80)
        logger.debug(f"[CHAT] FULL QUERY TO MODEL:\n{enhanced_message}")
        logger.debug("=" * 80)

        # Process with the agent
        logger.info("[CHAT] Invoking Strands agent...")
        logger.info("=" * 80)
        result = agent(enhanced_message)
        logger.info("=" * 80)
        logger.info("[CHAT] Agent invocation completed")
        
        # Log the result object details
        logger.debug(f"[CHAT] Result object type: {type(result)}")
        logger.debug(f"[CHAT] Result object repr: {repr(result)[:500]}")
        
        response_text = str(result)  # AgentResult has __str__ method
        logger.info(f"[CHAT] Agent response: {len(response_text)} characters")
        logger.debug(f"[CHAT] Response preview: {response_text[:300]}...")
        logger.debug("=" * 80)
        logger.debug(f"[CHAT] FULL RESPONSE FROM MODEL:\n{response_text}")
        logger.debug("=" * 80)
        
        # Log additional result properties if available
        try:
            if hasattr(result, 'messages'):
                logger.debug(f"[CHAT] Result has messages attribute: {len(getattr(result, 'messages', []))} messages")  # type: ignore
            if hasattr(result, 'content'):
                logger.debug(f"[CHAT] Result content: {getattr(result, 'content', 'N/A')}")  # type: ignore
            if hasattr(result, 'tool_calls'):
                logger.debug(f"[CHAT] Result tool calls: {getattr(result, 'tool_calls', 'N/A')}")  # type: ignore
        except Exception as attr_err:
            logger.debug(f"[CHAT] Could not access result attributes: {attr_err}")
        
        # Store the interaction in memory if session_id is provided
        if session_id and AGENTCORE_SERVICES_AVAILABLE:
            logger.info(f"[CHAT] Storing interaction in memory for session: {session_id}")
            memory_client = get_memory_client()
            if memory_client:
                try:
                    memory_client.store_interaction(
                        session_id=session_id,
                        user_message=user_message,
                        agent_response=response_text
                    )
                    logger.info("[CHAT] ✅ Interaction stored in memory")
                except Exception as e:
                    logger.error(f"[CHAT] ❌ Failed to store interaction in memory: {e}", exc_info=True)
            else:
                logger.debug("[CHAT] Memory client not available for storage")
        
        logger.info(f"[CHAT] ✅ Chat completed successfully: {len(response_text)} characters")
        logger.info("=" * 80)
        return response_text
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[CHAT] ❌ Error processing request: {e}", exc_info=True)
        logger.error("=" * 80)
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