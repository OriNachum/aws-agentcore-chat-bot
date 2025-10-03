# AWS Bedrock KB Integration - Architecture

## Problem: Authentication Failure

### Original (Broken) Flow
```
Agent queries KB
      ↓
kb_query_tool() invoked
      ↓
_query_via_direct_api()
      ↓
requests.post(kb_endpoint + "/query")  ❌ FAILED
   headers = {"Authorization": ""}     ❌ No AWS auth!
      ↓
AWS responds: 403 Forbidden
"Authorization header cannot be empty"
      ↓
User sees: "No knowledge base entries matched"  😞
```

**Issue**: Making a plain HTTP request to AWS requires AWS Signature Version 4 authentication, which wasn't being performed.

---

## Solution: boto3 with AWS SDK

### Fixed Flow
```
Agent queries KB
      ↓
kb_query_tool() invoked
      ↓
_query_via_direct_api()
      ↓
Detects "bedrock-agent-runtime" in URL
      ↓
_query_bedrock_kb()
      ↓
boto3.client('bedrock-agent-runtime')  ✅ Creates authenticated client
      ↓
client.retrieve(knowledgeBaseId=...)   ✅ Uses AWS SDK
      ↓
AWS SigV4 authentication automatically applied
      ↓
AWS Bedrock KB responds with results  ✅ SUCCESS
      ↓
Results formatted and returned
      ↓
User sees: Relevant knowledge base content  😊
```

---

## Code Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Discord User Query                        │
│               "What are word embeddings?"                    │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               Discord Bot (discord_bot.py)                   │
│                  Receives message                            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│            Agent Client (agent_client.py)                    │
│              Routes to appropriate backend                   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│          AgentCore App (agentcore_app.py)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  @tool kb_query_tool()                             │    │
│  │  - Invoked by Strands agent when KB needed         │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ↓                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  query_knowledge_base_via_gateway()                │    │
│  │  - Checks for gateway vs. direct API               │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ↓                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  _query_via_direct_api()                           │    │
│  │  - Detects Bedrock KB endpoint                     │    │
│  │  - Routes to appropriate handler                   │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ↓                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  _query_bedrock_kb()  ⭐ NEW                       │    │
│  │  - Uses boto3 bedrock-agent-runtime client         │    │
│  │  - Proper AWS authentication                       │    │
│  │  - Calls retrieve() API                            │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ↓                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  _extract_content_from_result()                    │    │
│  │  - Formats response for agent                      │    │
│  └────────────────┬───────────────────────────────────┘    │
└───────────────────┼────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              AWS Bedrock Knowledge Base                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Vector Search with Embeddings                     │    │
│  │  - Searches indexed documents                      │    │
│  │  - Returns top K results with scores               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## AWS Authentication Flow

```
boto3.client('bedrock-agent-runtime')
      ↓
Credential Chain:
  1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  2. ~/.aws/credentials file  ✅ Used in our case
  3. IAM role (when on EC2/ECS)
  4. AWS SSO
      ↓
Credentials loaded from ~/.aws/credentials
      ↓
Request prepared with:
  - Method: POST
  - URL: https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/KB_ID/retrieve
  - Body: JSON with query parameters
      ↓
AWS Signature Version 4 Applied:
  1. Create canonical request
  2. Create string to sign
  3. Calculate signature using secret key
  4. Add Authorization header with signature
      ↓
Request sent with proper AWS auth headers:
  - Authorization: AWS4-HMAC-SHA256 Credential=... Signature=...
  - X-Amz-Date: 20251003T222150Z
  - Content-Type: application/json
      ↓
AWS validates signature
      ↓
✅ Request authorized and processed
```

---

## Error Handling Improvements

### Before
```python
if response.status_code != 200:
    logger.error(f"API returned status {response.status_code}")
    return None  # Generic failure
```

**Result to agent**: "No knowledge base entries matched the query."

### After
```python
try:
    response = client.retrieve(...)
except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code')
    error_message = e.response.get('Error', {}).get('Message')
    return {
        "error": f"AWS Error: {error_code}",
        "message": error_message
    }
```

**Result to agent**: "Knowledge base query failed: AWS Error: AccessDenied

User: arn:aws:iam::123456:user/cli-user is not authorized to perform: bedrock:Retrieve on resource: arn:aws:bedrock:us-east-1:123456:knowledge-base/KB123"

**Much more actionable!** 🎯

---

## Configuration

### Environment Variables Used
```bash
# Region for AWS services
AWS_REGION=us-east-1

# Knowledge Base ID (extracted from endpoint)
KNOWLEDGE_BASE_ID=NIZI6QLHY7

# Full endpoint URL
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/NIZI6QLHY7/retrieve-and-generate
```

### AWS Credentials
```ini
# ~/.aws/credentials
[default]
aws_access_key_id = AKIAWK23G5R5GX6ADKBH
aws_secret_access_key = <secret>
```

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve"
            ],
            "Resource": "arn:aws:bedrock:us-east-1:*:knowledge-base/NIZI6QLHY7"
        }
    ]
}
```

---

## Result Format

### Bedrock API Response
```json
{
    "retrievalResults": [
        {
            "content": {
                "text": "Word embeddings are...",
                "type": "TEXT"
            },
            "location": {
                "s3Location": {"uri": "s3://bucket/doc.pdf"},
                "type": "S3"
            },
            "metadata": {
                "x-amz-bedrock-kb-source-uri": "s3://bucket/doc.pdf",
                "x-amz-bedrock-kb-chunk-id": "abc-123"
            },
            "score": 0.85
        }
    ]
}
```

### Formatted for Agent
```json
{
    "results": [
        {
            "content": "Word embeddings are...",
            "score": 0.85,
            "metadata": {
                "location": {"s3Location": {"uri": "s3://bucket/doc.pdf"}},
                "index": 0
            }
        }
    ],
    "count": 1,
    "source": "bedrock-kb"
}
```

### Extracted Content (sent to agent)
```
Word embeddings are...

[Additional results if multiple matches]
```

---

## Performance Characteristics

- **Latency**: ~1-2 seconds for typical queries
- **Cost**: ~$0.00002 per query (Bedrock KB pricing)
- **Concurrency**: Handled by boto3 connection pooling
- **Caching**: Not implemented (future improvement)
- **Max Results**: Configurable, default 5

---

## Future Enhancements

1. **Response Caching** - Cache frequently asked queries
2. **Query Expansion** - Use LLM to expand user query before KB search
3. **Hybrid Search** - Combine vector search with keyword search
4. **Result Reranking** - Use LLM to rerank results by relevance
5. **Streaming Responses** - Stream results as they arrive
6. **Metrics & Monitoring** - Track query performance and costs
