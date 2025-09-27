# AgentCore Knowledge Base Setup Guide

This guide shows how to set up and use AgentCore knowledge base integration with your Strands agents. You have several options depending on your infrastructure and requirements.

## Knowledge Base Options

### Option 1: AWS Bedrock Knowledge Base (Recommended for AWS users)
**Best for**: AWS-native deployments, fully managed solution

**Do you need S3 beforehand?** Yes, you need to:
1. Create an S3 bucket for your documents
2. Upload your knowledge documents to S3
3. Create a Bedrock Knowledge Base pointing to that S3 bucket

```powershell
# 1. Create S3 bucket
aws s3 mb s3://my-kb --region us-east-1

# 2. Upload documents
aws s3 cp ./docs/ s3://my-kb/docs/ --recursive

# 3. Create Knowledge Base via AWS Console, then:
$env:KNOWLEDGE_BASE_ENDPOINT = "bedrock-agent-runtime"
$env:KNOWLEDGE_BASE_ID = "YOUR_KB_ID_FROM_AWS_CONSOLE"
$env:AWS_REGION = "us-east-1"
```

#### Troubleshoot
aws gives:
```
make_bucket failed: s3://my-kb An error occurred (AccessDenied) when calling the CreateBucket operation: User: arn:aws:iam::435593604218:user/cli-user-amd is not authorized to perform: s3:CreateBucket on resource: "arn:aws:s3:::my-kb" because no identity-based policy allows the s3:CreateBucket action
```
Missing policy / permissions.
Add to usergroup or give permissions.

After:
```
make_bucket: my-kb
```

### Option 2: Pinecone Vector Database
**Best for**: Multi-cloud, high-performance vector search (like Pinecone)

**No S3 needed!** Just sign up at pinecone.io and create an index.

```powershell
# After creating Pinecone account and index:
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-index-xxxxx.svc.region.pinecone.io"
$env:KNOWLEDGE_BASE_API_KEY = "your-pinecone-api-key"
```

### Option 3: Local Development (Chroma/Qdrant)
**Best for**: Development and testing without external dependencies

```powershell
# Install and start Chroma
uv add chromadb
chroma run --host localhost --port 8000

# Configure
$env:KNOWLEDGE_BASE_ENDPOINT = "http://localhost:8000"
```

### Option 4: Custom Knowledge Base API
**Best for**: Existing knowledge systems

Your API should support this format:
```json
POST /query
{
  "query": "search terms",
  "max_results": 5
}
```

```powershell
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-custom-api.com/api/v1"
$env:KNOWLEDGE_BASE_API_KEY = "your-api-key"  # if needed
```

## Quick Setup Steps

### 1. Choose Your Knowledge Base Option (see above)

### 2. Set Environment Variables

```powershell
# Required: Your knowledge base endpoint
$env:KNOWLEDGE_BASE_ENDPOINT = "your-chosen-endpoint-from-above"

# Optional: API key (if your KB requires authentication)
$env:KNOWLEDGE_BASE_API_KEY = "your-api-key"

# Optional: For AWS Bedrock Knowledge Base
$env:KNOWLEDGE_BASE_ID = "your-bedrock-kb-id"
$env:AWS_REGION = "us-east-1"
```

### 3. Test Knowledge Base Integration

```powershell
# Run the agent locally to test KB integration
cd C:\Git\mike-et-al-community-bot
python src/community_bot/agentcore_app.py
```

Look for these log messages:
- ✅ `Knowledge base integration enabled` - Success!
- ℹ️ `Knowledge base integration not available` - Check your setup

### 4. Deploy to AgentCore (Optional)

```powershell
# Set AgentCore mode
$env:AGENTCORE_MODE = "true"

# Deploy using AgentCore CLI
agentcore configure -e src/community_bot/agentcore_app.py
agentcore launch

# Test deployed agent
agentcore invoke '{"prompt": "Tell me about our documentation", "session_id": "test"}'
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

## Detailed Setup Examples

### AWS Bedrock Knowledge Base Setup

**Yes, you need S3 first!** Here's the complete setup:

```powershell
# 1. Create S3 bucket
aws s3 mb s3://my-bot-knowledge-base

# 2. Upload your documents (PDFs, text files, etc.)
aws s3 cp ./company-docs/ s3://my-bot-knowledge-base/docs/ --recursive

# 3. Go to AWS Console > Amazon Bedrock > Knowledge bases
# 4. Click "Create knowledge base"
# 5. Connect to your S3 bucket
# 6. Wait for indexing to complete
# 7. Note the Knowledge Base ID

# 8. Configure your agent
$env:KNOWLEDGE_BASE_ENDPOINT = "bedrock-agent-runtime"
$env:KNOWLEDGE_BASE_ID = "ABC123XYZ"  # From step 6
$env:AWS_REGION = "us-east-1"
```

### Pinecone Setup (No S3 needed)

```powershell
# 1. Sign up at https://pinecone.io
# 2. Create a new index in the Pinecone console
# 3. Get your API key from settings
# 4. Configure:

$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-index-12345.svc.us-east1-gcp.pinecone.io"
$env:KNOWLEDGE_BASE_API_KEY = "your-pinecone-api-key"
```

## Supported Knowledge Base APIs

Your knowledge base API should support:

### Required Endpoint
```
POST /query
Content-Type: application/json
Authorization: Bearer {api_key}  # Optional

Request:
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
      "metadata": {"source": "doc.pdf", "score": 0.95}
    }
  ]
}
```

## Troubleshooting

### ❌ "Knowledge base integration not available"

**Check these items:**

1. **Environment variable set?**
   ```powershell
   echo $env:KNOWLEDGE_BASE_ENDPOINT
   # Should show your endpoint URL
   ```

2. **Network connectivity?**
   ```powershell
   # Test if endpoint is reachable
   curl $env:KNOWLEDGE_BASE_ENDPOINT/health
   ```

3. **API authentication?**
   ```powershell
   # Check API key is set (if required)
   echo $env:KNOWLEDGE_BASE_API_KEY
   ```

### ❌ "AgentCore Gateway query failed"

**This is normal!** The system will fallback to direct API calls. Common reasons:
- AgentCore services not available in your region
- AWS permissions not set up
- Gateway creation failed

**Resolution**: The fallback mode still works perfectly for knowledge base queries.

### ❌ "Direct API query failed"

Check your knowledge base API:

1. **Correct endpoint format?**
   ```
   ✅ https://api.example.com/v1
   ❌ https://api.example.com/v1/query  (don't include /query)
   ```

2. **API responds to POST /query?**
   ```powershell
   curl -X POST "$env:KNOWLEDGE_BASE_ENDPOINT/query" `
     -H "Content-Type: application/json" `
     -H "Authorization: Bearer $env:KNOWLEDGE_BASE_API_KEY" `
     -d '{"query": "test", "max_results": 1}'
   ```

3. **Check API rate limits and quotas**

### ❌ "No relevant knowledge found"

- Check if your documents are properly indexed
- Try different search terms
- Verify document format is supported by your knowledge base

## Recommendations by Use Case

| Use Case | Recommended Option | Why |
|----------|-------------------|-----|
| **AWS Production** | Bedrock Knowledge Base | Fully managed, secure, scales automatically |
| **Multi-cloud** | Pinecone | High performance, cloud-agnostic |  
| **Development** | Local Chroma | No external dependencies, fast iteration |
| **Existing Systems** | Custom API | Integrate with what you already have |

## Next Steps

1. **Choose your option** from the table above
2. **Follow the setup steps** for your chosen knowledge base
3. **Test locally** with `python src/community_bot/agentcore_app.py`
4. **Deploy to production** with AgentCore when ready

## Support

- Check the logs for detailed error messages
- Test your knowledge base API independently first
- Start with local development options before moving to production
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