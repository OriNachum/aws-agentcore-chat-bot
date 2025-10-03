# AWS Bedrock Knowledge Base Setup - Quick Guide

## What Was Fixed (October 2025)

The bot now properly integrates with AWS Bedrock Knowledge Base using `boto3` with proper AWS authentication instead of making unauthenticated HTTP requests.

## Configuration

### Required Environment Variables

```bash
# AWS Region
AWS_REGION=us-east-1

# Knowledge Base Configuration
KNOWLEDGE_BASE_ID=NIZI6QLHY7
KNOWLEDGE_BASE_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/NIZI6QLHY7/retrieve-and-generate

# Direct endpoint (used by agentcore_app.py)
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/NIZI6QLHY7/retrieve-and-generate
```

### AWS Credentials

Make sure you have AWS credentials configured in one of these ways:

1. **AWS Credentials File** (Recommended)
   ```
   ~/.aws/credentials
   ```
   Contains:
   ```ini
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   ```

2. **Environment Variables**
   ```bash
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **IAM Role** (when running on EC2/ECS)

## How It Works

1. **Auto-Detection**: The code automatically detects when you're using a Bedrock KB endpoint
2. **boto3 Authentication**: Uses boto3's `bedrock-agent-runtime` client with AWS SigV4 authentication
3. **Retrieve API**: Calls the Bedrock Knowledge Base `retrieve` API (not REST API)
4. **Result Formatting**: Converts Bedrock results into a standard format for the agent

## Code Flow

```
User Query
    ↓
kb_query_tool (Strands tool)
    ↓
query_knowledge_base_via_gateway()
    ↓
_query_via_direct_api() → Detects Bedrock endpoint
    ↓
_query_bedrock_kb() → Uses boto3 client
    ↓
AWS Bedrock KB retrieve API
    ↓
Results formatted and returned to agent
```

## Testing

### Quick Test
```powershell
uv run python test_kb_bedrock.py
```

### Full Integration Test
```powershell
uv run community-bot
```

Then in Discord, ask: "What are word embeddings?"

## Troubleshooting

### Error: "Authorization header cannot be empty"
- **Cause**: Missing AWS credentials
- **Fix**: Configure AWS credentials (see above)

### Error: "AccessDenied"
- **Cause**: IAM user doesn't have permissions for Bedrock KB
- **Fix**: Add IAM policy with `bedrock:Retrieve` permission

### Error: "ResourceNotFoundException"
- **Cause**: Knowledge Base ID doesn't exist or wrong region
- **Fix**: Verify `KNOWLEDGE_BASE_ID` and `AWS_REGION` are correct

### Error: "No results found"
- **Cause**: Query doesn't match any documents in KB
- **Fix**: Try different queries or check your KB has documents indexed

## Required IAM Permissions

Your IAM user/role needs:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1:*:knowledge-base/NIZI6QLHY7"
            ]
        }
    ]
}
```

## Example Queries

Good queries that should return results:
- "What are word embeddings?"
- "Explain contrastive learning"
- "How does RAG work?"

## Next Steps

1. ✅ Test basic queries work
2. Consider adding query caching to reduce costs
3. Monitor CloudWatch for Bedrock API usage
4. Tune `numberOfResults` parameter for better responses
