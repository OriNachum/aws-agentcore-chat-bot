# AgentCore Knowledge Base Setup Guide

This guide shows how to set up and use AgentCore knowledge base integration with your Strands agents.

## Quick Setup for Developers

### 1. Environment Variables

Set these environment variables to enable knowledge base integration:

```bash
# Required: Your knowledge base API endpoint
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-kb-api.example.com"

# Optional: API key for authentication (if your KB requires it)
$env:KNOWLEDGE_BASE_API_KEY = "your-api-key-here"

# Optional: Enable AgentCore mode for deployment
$env:AGENTCORE_MODE = "true"
```

### 2. Test Knowledge Base Integration

```bash
# Run the agent locally to test KB integration
cd C:\Git\mike-et-al-community-bot
python src/community_bot/agentcore_app.py
```

Look for these log messages:
- ✅ `Knowledge base integration enabled` - Success!
- ℹ️ `Knowledge base integration not available` - Check your setup

### 3. Deploy to AgentCore (Optional)

```bash
# Set AgentCore mode
$env:AGENTCORE_MODE = "true"

# Deploy using AgentCore CLI
agentcore configure -e src/community_bot/agentcore_app.py
agentcore launch
```

## How It Works

### Automatic Setup
- Knowledge base integration is **automatically initialized** when the agent starts
- No manual setup calls needed - it's wired into `get_agent()`
- Supports both AgentCore Gateway (MCP tools) and direct API fallback

### Two Integration Modes

#### 1. AgentCore Gateway Mode (Preferred)
- Converts your knowledge base API into MCP (Model Context Protocol) tools
- Managed by AWS AgentCore Gateway service
- Automatic scaling and security
- Used when AgentCore services are available

#### 2. Direct API Mode (Fallback)
- Direct HTTP calls to your knowledge base API
- Used when AgentCore Gateway is not available
- Still works for local development and testing

### Query Flow
1. User sends message to agent
2. Agent automatically queries knowledge base for relevant context
3. Knowledge base results are added to the prompt
4. Enhanced prompt sent to LLM
5. Agent responds with knowledge-augmented answer

## Supported Knowledge Base APIs

Your knowledge base API should support:

### Required Endpoint
```
POST /query
Content-Type: application/json
Authorization: Bearer {api_key}  # Optional

{
  "query": "user question",
  "max_results": 5,
  "include_metadata": true
}
```

### Expected Response
```json
{
  "results": [
    {
      "content": "relevant information...",
      "metadata": {...}
    }
  ]
}
```

### Optional Health Check
```
GET /health
```

## Example Usage

### Local Testing
```python
# This automatically uses knowledge base if configured
response = chat_with_agent("What is AgentCore?")
```

### AgentCore Deployment
```bash
# Test deployed agent with knowledge base
agentcore invoke '{
  "prompt": "What is AgentCore?",
  "session_id": "user_123",
  "use_knowledge_base": true
}'
```

### Disable Knowledge Base (if needed)
```python
# Skip knowledge base for this query
response = chat_with_agent(
    "Simple question", 
    use_knowledge_base=False
)
```

## Configuration Examples

### Example 1: Public API (No Auth)
```bash
$env:KNOWLEDGE_BASE_ENDPOINT = "https://public-kb.example.com"
# No API key needed
```

### Example 2: Private API with Auth
```bash
$env:KNOWLEDGE_BASE_ENDPOINT = "https://private-kb.example.com"
$env:KNOWLEDGE_BASE_API_KEY = "sk-your-secret-key"
```

### Example 3: Local Development
```bash
$env:KNOWLEDGE_BASE_ENDPOINT = "http://localhost:8080"
# For testing with local knowledge base
```

## Troubleshooting

### Common Issues

#### 1. "Knowledge base integration not available"
**Causes:**
- `KNOWLEDGE_BASE_ENDPOINT` not set
- AgentCore services not available
- Gateway client initialization failed

**Solutions:**
```bash
# Check environment variable
echo $env:KNOWLEDGE_BASE_ENDPOINT

# Set it if missing
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-kb.example.com"
```

#### 2. "AgentCore Gateway query failed"
**Causes:**
- Gateway creation failed
- Invalid API endpoint
- Authentication issues

**Solutions:**
- Check logs for specific error
- Verify API endpoint is accessible
- Check API key if required
- Agent will automatically fallback to direct API

#### 3. "Direct API query failed"
**Causes:**
- Knowledge base API is down
- Wrong endpoint URL
- Invalid API response format

**Solutions:**
- Test API manually: `curl https://your-kb.example.com/health`
- Check API documentation for correct format
- Verify network connectivity

### Debug Mode

Enable detailed logging:
```python
from community_bot.logging_config import setup_logging
setup_logging("DEBUG")
```

Look for these debug messages:
- `Querying knowledge base with: {query}`
- `Successfully queried via AgentCore Gateway`
- `Successfully queried via direct API`

## Advanced Configuration

### Custom Knowledge Base Integration

If you need to customize the knowledge base integration:

1. **Modify the query function**:
   ```python
   # Edit query_knowledge_base_via_gateway() in agentcore_app.py
   # Customize for your specific API format
   ```

2. **Add custom authentication**:
   ```python
   # Modify _query_via_direct_api() for custom auth
   headers["Custom-Auth"] = "your-custom-token"
   ```

3. **Custom response parsing**:
   ```python
   # Modify response parsing in _query_via_direct_api()
   # Extract data in your specific format
   ```

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `KNOWLEDGE_BASE_ENDPOINT` | Yes | KB API base URL | `https://api.example.com` |
| `KNOWLEDGE_BASE_API_KEY` | No | API authentication key | `sk-abc123` |
| `AGENTCORE_MODE` | No | Enable AgentCore deployment | `true` |
| `LLM_PROVIDER` | No | Model provider | `ollama` or `bedrock` |

## Testing Your Setup

### 1. Quick Test Script
```python
import os
os.environ["KNOWLEDGE_BASE_ENDPOINT"] = "https://your-kb.example.com"

from community_bot.agentcore_app import chat_with_agent
response = chat_with_agent("Test question")
print(response)
```

### 2. Verify Integration
Look for log messages containing:
- "Knowledge base integration configured successfully"
- "Added knowledge base context to message"
- "Successfully queried via..."

### 3. Manual API Test
```bash
curl -X POST "https://your-kb.example.com/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"query": "test", "max_results": 5}'
```

## Next Steps

1. **Set up your knowledge base API** following the required format
2. **Configure environment variables** for your setup
3. **Test locally** with `python src/community_bot/agentcore_app.py`
4. **Deploy to AgentCore** for production use
5. **Integrate with Discord** bot for enhanced conversations

## Support

- Check the main AgentCore documentation: https://docs.aws.amazon.com/bedrock-agentcore/
- AgentCore samples: https://github.com/awslabs/amazon-bedrock-agentcore-samples
- Enable debug logging for detailed troubleshooting