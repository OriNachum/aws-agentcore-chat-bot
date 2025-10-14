# Nova Backend Setup Guide

This guide walks you through setting up the AWS Bedrock Nova-Pro backend for the community bot.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [Configuration](#configuration)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- AWS account with Bedrock access
- AWS CLI configured with appropriate credentials
- Python 3.11+ environment
- `boto3` library installed (included in project dependencies)

---

## AWS Setup

### Step 1: Enable Nova-Pro Model Access

1. Log into AWS Console
2. Navigate to AWS Bedrock service
3. Go to "Model access" in the left sidebar
4. Find "Amazon Nova Pro" in the list
5. Click "Request model access" or "Enable" if available
6. Wait for approval (usually instant for Nova models)

### Step 2: Verify Model Availability

Using AWS CLI:

```bash
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, `nova`)]'
```

You should see output including:
- `us.amazon.nova-pro-v1:0`
- `us.amazon.nova-lite-v1:0`
- `us.amazon.nova-micro-v1:0`

### Step 3: Configure IAM Permissions

Create or update an IAM policy with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0"
    }
  ]
}
```

If you plan to use Knowledge Bases with Nova:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
    }
  ]
}
```

### Step 4: Test AWS Credentials

```bash
aws sts get-caller-identity
```

This should return your AWS account details without errors.

---

## Configuration

### Environment Variables

Update your `.env` file with the following:

```bash
# Backend selection
BACKEND_MODE=nova

# Discord (required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=123456789012345678

# AWS Configuration (required for Nova)
AWS_REGION=us-east-1

# Nova Settings (optional - defaults shown)
NOVA_MODEL_ID=us.amazon.nova-pro-v1:0
NOVA_TEMPERATURE=0.7
NOVA_MAX_TOKENS=4096
NOVA_TOP_P=0.9

# General Settings
MAX_RESPONSE_CHARS=1800
LOG_LEVEL=INFO
MEMORY_MAX_MESSAGES=50

# Prompt Management
PROMPT_PROFILE=default
# PROMPT_ROOT=agents
# PROMPT_USER_ROLE=user
# SYSTEM_PROMPT=  # Optional inline override
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_MODE` | Yes | `agentcore` | Set to `nova` for Nova backend |
| `AWS_REGION` | Yes | - | AWS region (e.g., `us-east-1`) |
| `NOVA_MODEL_ID` | No | `us.amazon.nova-pro-v1:0` | Bedrock Nova model identifier |
| `NOVA_TEMPERATURE` | No | `0.7` | Sampling temperature (0.0-1.0) |
| `NOVA_MAX_TOKENS` | No | `4096` | Maximum tokens to generate |
| `NOVA_TOP_P` | No | `0.9` | Nucleus sampling parameter |

---

## Testing

### Test 1: Basic Connectivity

Run the connectivity test script:

```bash
uv run python test_nova_connection.py
```

Expected output:
```
Testing connection to Nova model: us.amazon.nova-pro-v1:0
Region: us-east-1
--------------------------------------------------------------------------------
Invoking Nova model...
✅ Nova-Pro is accessible!
--------------------------------------------------------------------------------
Response:
{
  "output": {
    "message": {
      "role": "assistant",
      "content": [{"text": "I am Claude..."}]
    }
  },
  ...
}
```

### Test 2: Integration Test

Run the full integration test:

```bash
uv run python test_nova_integration.py
```

This will test:
- Agent initialization
- Conversation memory
- Streaming responses
- Multiple message handling

### Test 3: Discord Bot Test

Start the bot and test in Discord:

```bash
uv run community-bot
```

In your Discord channel, send a message and verify the bot responds using Nova.

---

## Troubleshooting

### Error: "Could not connect to the endpoint URL"

**Cause**: AWS region misconfiguration or credentials issue.

**Solution**:
1. Verify `AWS_REGION` is set correctly in `.env`
2. Check AWS credentials: `aws sts get-caller-identity`
3. Ensure you're using the correct region where Nova is available

### Error: "Access denied" or "UnauthorizedException"

**Cause**: Insufficient IAM permissions.

**Solution**:
1. Check IAM policy includes `bedrock:InvokeModel` permission
2. Verify the resource ARN matches the Nova model
3. Ensure IAM user/role is attached to the policy

### Error: "Model not found" or "ValidationException"

**Cause**: Model ID incorrect or model access not enabled.

**Solution**:
1. Verify model ID: `us.amazon.nova-pro-v1:0` (note the `us.` prefix)
2. Check model access in Bedrock console
3. List available models: `aws bedrock list-foundation-models --region us-east-1`

### Error: "Throttling" or "Rate exceeded"

**Cause**: Too many requests to Bedrock API.

**Solution**:
1. Implement exponential backoff (already included in `NovaModel`)
2. Request quota increase in AWS Service Quotas
3. Consider using Nova-Lite for higher throughput use cases

### Empty or Truncated Responses

**Cause**: `NOVA_MAX_TOKENS` too low or response splitting issue.

**Solution**:
1. Increase `NOVA_MAX_TOKENS` in `.env`
2. Check `MAX_RESPONSE_CHARS` setting
3. Review logs for token limit warnings

### Slow Response Times

**Cause**: Model inference latency or network issues.

**Solution**:
1. Check AWS region - use closest region to your location
2. Consider using Nova-Lite for faster responses
3. Monitor CloudWatch metrics for Bedrock
4. Verify network connectivity to AWS

---

## Performance Benchmarking

Run the performance test:

```bash
uv run python test_nova_performance.py
```

This will measure:
- Average response time
- Time to first token (TTFT)
- Tokens per second
- Response quality

---

## Cost Monitoring

### Nova-Pro Pricing (as of October 2025)

- **Input tokens**: $0.80 per 1M tokens
- **Output tokens**: $3.20 per 1M tokens

### Estimated Costs

For moderate Discord bot usage:
- 1000 messages/day
- 200 input tokens/message average
- 500 output tokens/message average

**Daily cost**: ~$1.76/day = ~$53/month

### Cost Optimization Tips

1. **Use conversation memory wisely** - Don't store too many messages
2. **Set appropriate max_tokens** - Avoid generating unnecessarily long responses
3. **Consider Nova-Lite** - For simple queries (cheaper at $0.06/$0.24 per 1M tokens)
4. **Implement caching** - Cache common responses
5. **Monitor usage** - Use CloudWatch to track API calls

---

## Next Steps

1. ✅ Verify Nova backend is working
2. ✅ Test with Discord bot
3. ✅ Monitor costs in AWS Cost Explorer
4. Consider setting up CloudWatch alarms for:
   - High API call volume
   - Error rates
   - Cost thresholds

---

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Nova Model Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/models-nova.html)
- [Bedrock API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/)
- [Pricing Calculator](https://calculator.aws/)

---

## Support

For issues specific to this bot implementation:
1. Check the logs: `logs/community_bot.log`
2. Review error messages in the troubleshooting section above
3. Create an issue in the repository with logs and error details
