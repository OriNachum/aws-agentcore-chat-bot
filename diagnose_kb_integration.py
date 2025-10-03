"""
Diagnostic script to test knowledge base integration with AgentCore.

This script helps identify issues with KB integration by testing each component separately.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from community_bot.config import load_settings
from community_bot.logging_config import setup_logging, get_logger

# Force debug logging
settings = load_settings()
settings.log_level = "DEBUG"
setup_logging(settings.log_level)

logger = get_logger("diagnose_kb")

def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_environment():
    """Check environment variables."""
    print_section("Environment Variables Check")
    
    vars_to_check = [
        "LLM_PROVIDER",
        "AGENTCORE_MODE",
        "KNOWLEDGE_BASE_ENDPOINT",
        "KNOWLEDGE_BASE_API_KEY",
        "KB_GATEWAY_ID",
        "KB_GATEWAY_ENDPOINT",
        "KB_DIRECT_ENDPOINT",
        "KB_DIRECT_API_KEY",
    ]
    
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display_value = f"{'*' * 8}...{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")

def check_agentcore_services():
    """Check if AgentCore services are available."""
    print_section("AgentCore Services Check")
    
    try:
        from community_bot.agentcore_app import AGENTCORE_SERVICES_AVAILABLE
        print(f"AgentCore services available: {AGENTCORE_SERVICES_AVAILABLE}")
        
        if AGENTCORE_SERVICES_AVAILABLE:
            from bedrock_agentcore.services.gateway import GatewayClient
            from bedrock_agentcore.services.memory import MemoryClient
            print("✅ GatewayClient imported successfully")
            print("✅ MemoryClient imported successfully")
        else:
            print("⚠️  AgentCore services not available (older version or not installed)")
    except Exception as e:
        print(f"❌ Error checking AgentCore services: {e}")

def check_gateway_client():
    """Check if gateway client can be initialized."""
    print_section("Gateway Client Check")
    
    try:
        from community_bot.agentcore_app import get_gateway_client
        
        gateway_client = get_gateway_client()
        if gateway_client:
            print("✅ Gateway client initialized successfully")
            print(f"   Type: {type(gateway_client)}")
        else:
            print("❌ Gateway client is None")
    except Exception as e:
        print(f"❌ Error initializing gateway client: {e}")
        logger.exception("Gateway client initialization failed")

def test_kb_query_direct():
    """Test direct knowledge base query."""
    print_section("Direct KB Query Test")
    
    kb_endpoint = os.environ.get("KB_DIRECT_ENDPOINT")
    if not kb_endpoint:
        print("⚠️  KB_DIRECT_ENDPOINT not set, skipping direct query test")
        return
    
    try:
        from community_bot.agentcore_app import _query_via_direct_api
        
        test_query = "test query"
        print(f"Testing query: '{test_query}'")
        print(f"Endpoint: {kb_endpoint}")
        
        result = _query_via_direct_api(
            kb_endpoint,
            test_query,
            max_results=3,
            include_metadata=True
        )
        
        if result:
            print(f"✅ Query returned result")
            print(f"   Type: {type(result)}")
            print(f"   Result: {str(result)[:300]}...")
        else:
            print("❌ Query returned None")
    except Exception as e:
        print(f"❌ Direct query failed: {e}")
        logger.exception("Direct query test failed")

def test_kb_query_gateway():
    """Test gateway knowledge base query."""
    print_section("Gateway KB Query Test")
    
    kb_gateway_id = os.environ.get("KB_GATEWAY_ID")
    if not kb_gateway_id:
        print("⚠️  KB_GATEWAY_ID not set, skipping gateway query test")
        return
    
    try:
        from community_bot.agentcore_app import get_gateway_client, _query_via_agentcore_gateway
        
        gateway_client = get_gateway_client()
        if not gateway_client:
            print("❌ Gateway client not available")
            return
        
        test_query = "test query"
        print(f"Testing query: '{test_query}'")
        print(f"Gateway ID: {kb_gateway_id}")
        
        result = _query_via_agentcore_gateway(
            gateway_client,
            kb_gateway_id,
            test_query,
            max_results=3,
            include_metadata=True
        )
        
        if result:
            print(f"✅ Query returned result")
            print(f"   Type: {type(result)}")
            print(f"   Result: {str(result)[:300]}...")
        else:
            print("❌ Query returned None")
    except Exception as e:
        print(f"❌ Gateway query failed: {e}")
        logger.exception("Gateway query test failed")

def test_kb_tool():
    """Test the kb-query-tool function."""
    print_section("KB Tool Test")
    
    try:
        from community_bot.agentcore_app import kb_query_tool
        
        test_query = "test query"
        print(f"Testing kb-query-tool with query: '{test_query}'")
        
        result = kb_query_tool(
            query=test_query,
            max_results=3,
            include_metadata=True
        )
        
        print(f"✅ Tool executed")
        print(f"   Status: {result.get('status')}")
        if result.get('content'):
            content = result['content']
            if isinstance(content, list) and content:
                text = content[0].get('text', '')
                print(f"   Content preview: {text[:200]}...")
            else:
                print(f"   Content: {content}")
        else:
            print("   No content returned")
    except Exception as e:
        print(f"❌ KB tool test failed: {e}")
        logger.exception("KB tool test failed")

def test_agent_initialization():
    """Test agent initialization."""
    print_section("Agent Initialization Test")
    
    try:
        from community_bot.agentcore_app import get_agent
        
        print("Initializing agent...")
        agent = get_agent()
        
        if agent:
            print(f"✅ Agent initialized successfully")
            print(f"   Type: {type(agent)}")
            print(f"   Model: {type(agent.model) if hasattr(agent, 'model') else 'N/A'}")
            print(f"   Tools: {len(agent.tools) if hasattr(agent, 'tools') else 'N/A'} tools")
            
            if hasattr(agent, 'tools'):
                for idx, tool in enumerate(agent.tools):
                    tool_name = getattr(tool, '__name__', str(tool))
                    print(f"      {idx+1}. {tool_name}")
        else:
            print("❌ Agent is None")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        logger.exception("Agent initialization test failed")

def test_simple_chat():
    """Test a simple chat interaction."""
    print_section("Simple Chat Test")
    
    try:
        from community_bot.agentcore_app import chat_with_agent
        
        test_message = "Hello, can you help me?"
        print(f"Testing chat with message: '{test_message}'")
        
        response = chat_with_agent(
            user_message=test_message,
            session_id=None,
            use_knowledge_base=False  # Disable KB for this test
        )
        
        if response:
            print(f"✅ Chat completed")
            print(f"   Response length: {len(response)} characters")
            print(f"   Response preview: {response[:300]}...")
        else:
            print("❌ Empty response")
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        logger.exception("Chat test failed")

def test_chat_with_kb():
    """Test chat with knowledge base enabled."""
    print_section("Chat with KB Test")
    
    kb_available = (
        os.environ.get("KB_GATEWAY_ID") or 
        os.environ.get("KB_DIRECT_ENDPOINT")
    )
    
    if not kb_available:
        print("⚠️  No KB endpoint configured, skipping KB chat test")
        return
    
    try:
        from community_bot.agentcore_app import chat_with_agent
        
        test_message = "Tell me about your knowledge base"
        print(f"Testing chat with KB enabled: '{test_message}'")
        
        response = chat_with_agent(
            user_message=test_message,
            session_id=None,
            use_knowledge_base=True  # Enable KB
        )
        
        if response:
            print(f"✅ Chat with KB completed")
            print(f"   Response length: {len(response)} characters")
            print(f"   Response preview: {response[:300]}...")
        else:
            print("❌ Empty response")
    except Exception as e:
        print(f"❌ Chat with KB test failed: {e}")
        logger.exception("Chat with KB test failed")

def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 80)
    print("  Knowledge Base Integration Diagnostic Tool")
    print("  " + "=" * 78)
    print("\n  This tool will test each component of the KB integration")
    print("  and help identify where issues may be occurring.")
    print("=" * 80)
    
    check_environment()
    check_agentcore_services()
    check_gateway_client()
    test_kb_query_direct()
    test_kb_query_gateway()
    test_kb_tool()
    test_agent_initialization()
    test_simple_chat()
    test_chat_with_kb()
    
    print_section("Diagnostic Complete")
    print("Check the logs above for any ❌ errors or ⚠️ warnings.")
    print("The detailed logs should help identify where the KB integration is failing.")
    print("\nCommon issues:")
    print("  1. Missing environment variables (KB_GATEWAY_ID or KB_DIRECT_ENDPOINT)")
    print("  2. AgentCore services not installed or outdated version")
    print("  3. Knowledge base endpoint not accessible")
    print("  4. Agent not configured to use the KB tool")
    print("  5. KB tool returning results but agent not using them")
    print("\n")

if __name__ == "__main__":
    main()
