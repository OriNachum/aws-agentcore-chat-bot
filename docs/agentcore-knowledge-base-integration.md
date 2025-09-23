# AgentCore Integration with Knowledge Bases

This document explains the enhanced AgentCore integration that augments your Strands agents with knowledge bases and additional capabilities.

## Overview

The enhanced `agentcore_app.py` now includes:

- **🧠 Memory Persistence**: Conversation history across sessions
- **📚 Knowledge Base Integration**: External data sources via AgentCore Gateway
- **🔐 Identity Management**: Secure access to APIs and knowledge bases
- **🚀 Easy Deployment**: One-command deployment to AWS with AgentCore

## Key Features

### 1. Memory Persistence
```python
# Chat with session memory
response = chat_with_agent(
    user_message="What did we discuss earlier?",
    session_id="user_123"
)
```

### 2. Knowledge Base Integration
```python
# Enable knowledge base augmentation
response = chat_with_agent(
    user_message="Tell me about AgentCore",
    use_knowledge_base=True
)
```

### 3. AgentCore Deployment
```bash
# Configure and deploy your agent
agentcore configure -e agentcore_app.py
agentcore launch
```

## Quick Start

### Local Testing

1. **Run Enhanced Agent Locally**:
   ```bash
   cd C:\Git\mike-et-al-community-bot
   python src/community_bot/agentcore_app.py
   ```

2. **Test Enhanced Example**:
   ```bash
   python examples/agentcore_enhanced_example.py
   ```

### AgentCore Deployment

1. **Set AgentCore Mode**:
   ```bash
   $env:AGENTCORE_MODE = "true"
   ```

2. **Deploy with AgentCore CLI**:
   ```bash
   agentcore configure -e src/community_bot/agentcore_app.py
   agentcore launch
   ```

3. **Test Deployed Agent**:
   ```bash
   agentcore invoke '{"prompt": "Hello! How can you help me?", "session_id": "test_session"}'
   ```

## Configuration

### Environment Variables

```bash
# Required for AgentCore deployment
$env:AGENTCORE_MODE = "true"

# Optional: Knowledge base endpoint
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-kb-api.com"

# AWS credentials (for deployment)
$env:AWS_ACCESS_KEY_ID = "your_key"
$env:AWS_SECRET_ACCESS_KEY = "your_secret"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

### Agent Configuration

The enhanced agent supports both Ollama and Bedrock models:

```python
# Use Ollama (default)
$env:LLM_PROVIDER = "ollama"

# Use AWS Bedrock
$env:LLM_PROVIDER = "bedrock"
```

## API Reference

### Enhanced Chat Function

```python
def chat_with_agent(
    user_message: str, 
    session_id: Optional[str] = None, 
    use_knowledge_base: bool = True
) -> str:
    """
    Enhanced chat function with AgentCore capabilities.
    
    Args:
        user_message: User's input message
        session_id: Optional session ID for memory persistence
        use_knowledge_base: Whether to use knowledge base augmentation
    
    Returns:
        Agent's response with enhanced context
    """
```

### AgentCore Entrypoint

```python
@agentcore_app.entrypoint
def agent_invocation(payload, context=None):
    """
    AgentCore deployment entrypoint.
    
    Payload format:
    {
        "prompt": "Your message here",
        "session_id": "optional_session_id", 
        "use_knowledge_base": true
    }
    """
```

## Knowledge Base Integration

### Setup

1. **Configure Knowledge Base Endpoint**:
   ```bash
   $env:KNOWLEDGE_BASE_ENDPOINT = "https://your-knowledge-base-api.com"
   ```

2. **Initialize Integration**:
   ```python
   from community_bot.agentcore_app import setup_knowledge_base_integration
   setup_knowledge_base_integration()
   ```

### Custom Knowledge Base

To integrate your own knowledge base:

1. **Implement Knowledge Base Query Function**:
   ```python
   def query_knowledge_base_via_gateway(gateway_client, query: str) -> Optional[str]:
       # Your knowledge base query logic here
       # Return relevant context or None
       pass
   ```

2. **Configure Gateway Client**:
   ```python
   gateway_client = get_gateway_client()
   # Configure your specific knowledge base connections
   ```

## Deployment Options

### 1. Local Development
- Interactive chat interface
- Memory and knowledge base testing
- Quick prototyping

### 2. AgentCore Runtime
- Managed serverless deployment
- Auto-scaling and monitoring
- Production-ready infrastructure

### 3. Discord Integration
- Use enhanced agent in Discord bot
- Session persistence per user
- Knowledge base augmented responses

## Troubleshooting

### Common Issues

1. **AgentCore Services Not Available**:
   ```
   Warning: AgentCore services not available, using basic mode
   ```
   - Install latest bedrock-agentcore packages
   - Check AWS permissions for AgentCore services

2. **Knowledge Base Connection Failed**:
   ```
   Warning: Failed to retrieve knowledge base context
   ```
   - Verify KNOWLEDGE_BASE_ENDPOINT environment variable
   - Check API authentication and permissions

3. **Memory Storage Failed**:
   ```
   Warning: Failed to store interaction in memory
   ```
   - Verify AWS credentials and permissions
   - Check AgentCore Memory service availability

### Debug Mode

Enable debug logging:
```python
setup_logging("DEBUG")
```

Test with debug payload:
```json
{
    "prompt": "Test message",
    "session_id": "debug_session",
    "debug": true
}
```

## Examples

See `examples/agentcore_enhanced_example.py` for a complete demonstration of:
- Enhanced agent capabilities
- Memory persistence
- Knowledge base integration
- AgentCore deployment patterns

## Next Steps

1. **Configure Your Knowledge Base**: Set up your specific knowledge base endpoints
2. **Deploy to AgentCore**: Use the CLI to deploy your enhanced agent
3. **Integrate with Discord**: Update your Discord bot to use the enhanced agent
4. **Monitor and Scale**: Use AgentCore observability features to monitor performance

## Related Documentation

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [AgentCore Samples Repository](https://github.com/awslabs/amazon-bedrock-agentcore-samples)