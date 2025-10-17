# Amazon Nova Pro Setup Guide

## Overview

This guide explains how to configure the community bot to use **Amazon Nova Pro** with the **AgentCore mode** and **Bedrock setup**.

## What is Nova Pro?

Amazon Nova Pro is AWS's new family of foundation models available through Amazon Bedrock. It offers:

- **Advanced capabilities**: State-of-the-art language understanding and generation
- **Native AWS integration**: Seamless integration with Bedrock services
- **Cost-effective**: Competitive pricing compared to other frontier models
- **Streaming support**: Real-time response streaming
- **Knowledge Base integration**: Works with Bedrock Knowledge Bases

## Architecture

The bot uses the **Strands Agents framework** in AgentCore mode:

```
User Message
    ↓
Discord Bot (discord_bot.py)
    ↓
Agent Client (agent_client.py)
    ↓
AgentCore App (agentcore_app.py)
    ↓
Strands Agent Framework
    ↓
BedrockModel (Nova Pro)
    ↓
AWS Bedrock Runtime API
    ↓
Nova Pro Model
```

## Configuration Steps

### 1. Set Environment Variables

Create or edit your `.env` file:

```bash
# Backend Configuration
BACKEND_MODE=agentcore
LLM_PROVIDER=bedrock

# AWS Configuration
AWS_REGION=us-east-1

# Nova Pro Model Configuration
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=4096
BEDROCK_STREAMING=true

# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=your_channel_id

# Logging
LOG_LEVEL=INFO
```

### 2. Configure AWS Credentials

Ensure you have AWS credentials configured. Nova Pro requires proper IAM permissions:

**Option A: AWS Credentials File** (Recommended)
```bash
# Linux/macOS: ~/.aws/credentials
# Windows: C:\Users\USERNAME\.aws\credentials

[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

**Option B: Environment Variables**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 3. Verify IAM Permissions

Your IAM user/role needs these permissions:

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
            "Resource": "arn:aws:bedrock:*::foundation-model/amazon.nova-*"
        }
    ]
}
```

### 4. Enable Model Access in Bedrock

Before using Nova Pro:

1. Go to **AWS Console** → **Amazon Bedrock**
2. Navigate to **Model access** (left sidebar)
3. Click **Enable specific models**
4. Find **Amazon Nova Pro** in the list
5. Click **Enable** and accept the terms

### 5. Test the Configuration

Run the interactive test:

```bash
# Using uv (recommended)
uv run python src/community_bot/agentcore_app.py

# Or directly
python src/community_bot/agentcore_app.py
```

You should see:
```
[AGENT INIT] LLM Provider: bedrock
[AGENT INIT] Configuring Bedrock model: us.amazon.nova-pro-v1:0
[AGENT INIT] ✅ Bedrock model configured successfully
[AGENT INIT] ✅ Strands Agent initialized successfully

You: Hello!
Agent: [Response from Nova Pro]
```

## Knowledge Base Integration

Nova Pro works seamlessly with Bedrock Knowledge Bases:

### Setup Knowledge Base

```bash
# Add to your .env file
KNOWLEDGE_BASE_ID=YOUR_KB_ID
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/YOUR_KB_ID/retrieve-and-generate
```

### Required IAM Permissions for KB

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
            "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
        }
    ]
}
```

## Model Options

You can use different Nova models by changing `BEDROCK_MODEL_ID`:

| Model | Model ID | Use Case | Cost |
|-------|----------|----------|------|
| **Nova Pro** | `us.amazon.nova-pro-v1:0` | Advanced reasoning, complex tasks | $$$ |
| **Nova Lite** | `us.amazon.nova-lite-v1:0` | Balanced performance | $$ |
| **Nova Micro** | `us.amazon.nova-micro-v1:0` | Fast, simple tasks | $ |

### Other Bedrock Models

You can also use other Bedrock models:

```bash
# Claude 3 Sonnet
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Claude 3.5 Sonnet
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# Titan Text
BEDROCK_MODEL_ID=amazon.titan-text-premier-v1:0
```

## Advanced Configuration

### Temperature

Controls randomness in responses:

```bash
BEDROCK_TEMPERATURE=0.7  # Default: balanced creativity
BEDROCK_TEMPERATURE=0.3  # More focused/deterministic
BEDROCK_TEMPERATURE=1.0  # More creative/diverse
```

### Max Tokens

Maximum tokens in response:

```bash
BEDROCK_MAX_TOKENS=4096  # Default
BEDROCK_MAX_TOKENS=2048  # Shorter responses
BEDROCK_MAX_TOKENS=8192  # Longer responses (if model supports)
```

### Streaming

Enable/disable streaming responses:

```bash
BEDROCK_STREAMING=true   # Stream responses (recommended)
BEDROCK_STREAMING=false  # Wait for complete response
```

## Troubleshooting

### Error: "Could not connect to the endpoint URL"

**Cause**: Wrong region or model not available in your region

**Solution**: 
- Verify `AWS_REGION` is correct
- Check if Nova Pro is available in your region
- Try `us-east-1` or `us-west-2`

### Error: "ValidationException: The provided model identifier is invalid"

**Cause**: Model ID is incorrect or model not enabled

**Solution**:
1. Verify model ID: `us.amazon.nova-pro-v1:0`
2. Enable Nova Pro in Bedrock console (see step 4 above)
3. Check if model is available in your region

### Error: "AccessDeniedException"

**Cause**: Missing IAM permissions

**Solution**:
1. Add required IAM permissions (see step 3 above)
2. Verify AWS credentials are configured
3. Check IAM policy is attached to your user/role

### Error: "ThrottlingException: Rate exceeded"

**Cause**: Too many requests to Bedrock API

**Solution**:
- Implement rate limiting in your application
- Reduce request frequency
- Request quota increase in AWS Console

### Model not responding

**Check these:**
1. Is Ollama accidentally running? (Set `LLM_PROVIDER=bedrock`)
2. Is `BACKEND_MODE=agentcore`?
3. Check logs with `LOG_LEVEL=DEBUG`
4. Verify AWS credentials with: `aws sts get-caller-identity`

## Testing Commands

### Quick Test

```bash
# Test Nova Pro directly
uv run python -c "from community_bot.agentcore_app import chat_with_agent; print(chat_with_agent('Hello!'))"
```

### Full Integration Test

```bash
# Test with Discord bot
uv run community-bot
```

Then send a message in your Discord channel.

### Test with Knowledge Base

```bash
# Configure KB first, then:
uv run python test_kb_bedrock.py
```

## Comparison with Other Modes

### AgentCore + Nova Pro (Current)

```bash
BACKEND_MODE=agentcore
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
```

**Pros:**
- ✅ AWS-native integration
- ✅ Streaming support
- ✅ Knowledge Base integration
- ✅ Scalable and production-ready
- ✅ No local setup needed

**Cons:**
- ❌ Requires AWS account
- ❌ API costs
- ❌ Latency depends on region

### AgentCore + Ollama

```bash
BACKEND_MODE=agentcore
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
```

**Pros:**
- ✅ Free (local)
- ✅ No API costs
- ✅ Privacy (runs locally)
- ✅ Fast (if local GPU)

**Cons:**
- ❌ Requires local setup
- ❌ Need powerful hardware
- ❌ Limited model options

### Ollama Backend (Legacy)

```bash
BACKEND_MODE=ollama
OLLAMA_MODEL=llama3
```

**Pros:**
- ✅ Simple setup
- ✅ Direct Ollama integration

**Cons:**
- ❌ Less features
- ❌ No knowledge base integration
- ❌ Legacy mode

## Best Practices

1. **Start with default settings**: The default configuration is optimized for most use cases

2. **Use streaming**: Enable `BEDROCK_STREAMING=true` for better user experience

3. **Monitor costs**: Nova Pro charges per token. Use CloudWatch to monitor usage

4. **Set proper temperature**: 
   - 0.3-0.5 for factual/deterministic tasks
   - 0.7-0.9 for creative tasks

5. **Use Knowledge Base**: Combine Nova Pro with Bedrock KB for RAG applications

6. **Enable logging**: Use `LOG_LEVEL=DEBUG` during development

7. **Test incrementally**: Test without KB first, then add KB integration

## Cost Estimation

Nova Pro pricing (as of October 2025):

- **Input**: ~$0.008 per 1K tokens
- **Output**: ~$0.024 per 1K tokens

Example calculation for 1000 messages:
- Average message: 100 tokens input, 300 tokens output
- Cost per message: (100 × $0.008 + 300 × $0.024) / 1000 = ~$0.0088
- Cost for 1000 messages: ~$8.80

*Note: Prices vary by region. Check AWS Bedrock pricing page for current rates.*

## Next Steps

1. **Customize prompts**: Edit files in `agents/default/` directory
2. **Add tools**: Implement custom tools in `agentcore_app.py`
3. **Integrate Knowledge Base**: Follow `BEDROCK_KB_SETUP.md`
4. **Deploy to production**: Set up AWS Lambda or ECS deployment

## Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents Documentation](https://strandsagents.com/)
- [AgentCore Integration Guide](./agentcore-use.md)
- [Knowledge Base Setup](./BEDROCK_KB_SETUP.md)
- [Environment Variables Reference](./environment-variables-reference.md)

## Support

If you encounter issues:

1. Check the logs: `LOG_LEVEL=DEBUG`
2. Run diagnostic: `python diagnose_kb_integration.py`
3. Review troubleshooting section above
4. Check AWS CloudWatch logs
5. Open an issue on GitHub

---

**Last Updated**: October 2025  
**Compatible with**: AgentCore mode, Strands framework, Nova Pro v1
