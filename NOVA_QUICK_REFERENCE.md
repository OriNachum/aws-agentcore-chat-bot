# Nova Backend - Quick Reference

## Quick Start

### 1. Enable Nova in AWS
```bash
# Check model access
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, `nova`)]'

# If not available, request access in Bedrock Console > Model access
```

### 2. Configure Environment
```bash
# Edit .env
BACKEND_MODE=nova
AWS_REGION=us-east-1
DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=your_channel_id
```

### 3. Test & Run
```bash
# Test connectivity
uv run python test_nova_connection.py

# Run bot
uv run community-bot
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_MODE` | ✅ Yes | - | Set to `nova` |
| `AWS_REGION` | ✅ Yes | - | AWS region (e.g., `us-east-1`) |
| `DISCORD_BOT_TOKEN` | ✅ Yes | - | Discord bot token |
| `DISCORD_CHANNEL_ID` | ✅ Yes | - | Discord channel ID |
| `NOVA_MODEL_ID` | No | `us.amazon.nova-pro-v1:0` | Model identifier |
| `NOVA_TEMPERATURE` | No | `0.7` | Temperature (0.0-1.0) |
| `NOVA_MAX_TOKENS` | No | `4096` | Max output tokens |
| `NOVA_TOP_P` | No | `0.9` | Top-p sampling |
| `MEMORY_MAX_MESSAGES` | No | `50` | Conversation memory size |
| `MAX_RESPONSE_CHARS` | No | `1800` | Discord char limit |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## Commands

### Testing
```bash
# Basic connectivity
uv run python test_nova_connection.py

# Integration test
uv run python test_nova_integration.py

# Performance benchmark
uv run python test_nova_performance.py
```

### Running
```bash
# Start bot
uv run community-bot

# With debug logging
LOG_LEVEL=DEBUG uv run community-bot
```

---

## IAM Permissions

Minimum required policy:
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

---

## Troubleshooting

### "Access denied"
→ Check IAM permissions (see above)  
→ Verify AWS credentials: `aws sts get-caller-identity`

### "Model not found"
→ Check model ID: `us.amazon.nova-pro-v1:0` (note the `us.` prefix)  
→ Request access in Bedrock Console

### "Could not connect to endpoint"
→ Check AWS_REGION is set correctly  
→ Verify internet connectivity

### Empty responses
→ Increase NOVA_MAX_TOKENS  
→ Check logs for truncation warnings  
→ Verify prompt is not too long

### Slow responses
→ Normal: 2-5s for first token  
→ Check AWS region proximity  
→ Consider Nova-Lite for faster responses

---

## Cost Estimate

**Pricing** (Nova-Pro):
- Input: $0.80 per 1M tokens
- Output: $3.20 per 1M tokens

**Example** (1000 msgs/day, 200 input / 500 output tokens avg):
- Daily: ~$1.76
- Monthly: ~$53

**Cost Controls**:
- Set `NOVA_MAX_TOKENS` lower (e.g., 2048)
- Reduce `MEMORY_MAX_MESSAGES` (e.g., 20)
- Use Nova-Lite for simple queries

---

## Switching Backends

Change `BACKEND_MODE` in `.env`:
```bash
BACKEND_MODE=nova       # AWS Nova-Pro
BACKEND_MODE=agentcore  # AgentCore/Strands
BACKEND_MODE=ollama     # Local Ollama
```

Restart bot - no code changes needed!

---

## Logs

Watch for Nova-specific logs:
```bash
tail -f logs/community_bot.log | grep "NOVA"
```

Common log patterns:
- `[NOVA AGENT] Processing message` - Message received
- `[NOVA AGENT] Response complete` - Response sent
- `Initialized Nova model` - Model initialized successfully

---

## Architecture

```
Discord → AgentClient → NovaAgent → NovaModel → AWS Bedrock
                            ↓
                     ConversationMemory
                            ↓
                      PromptBundle
```

---

## Files

### Core Implementation
- `src/community_bot/nova_model.py` - Bedrock API wrapper
- `src/community_bot/nova_agent.py` - Agent orchestration
- `src/community_bot/agent_client.py` - Backend routing

### Tests
- `test_nova_connection.py` - Basic connectivity
- `test_nova_integration.py` - Full integration
- `test_nova_performance.py` - Performance benchmarks

### Documentation
- `docs/NOVA_SETUP.md` - Complete setup guide
- `NOVA_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `README.md` - Quick start

---

## Support Resources

- 📚 Setup Guide: `docs/NOVA_SETUP.md`
- 📋 Implementation Details: `NOVA_IMPLEMENTATION_SUMMARY.md`
- 🐛 Troubleshooting: `docs/NOVA_SETUP.md#troubleshooting`
- 📖 AWS Docs: https://docs.aws.amazon.com/bedrock/

---

## Next Steps

1. ✅ Verify AWS access to Nova
2. ✅ Configure `.env` with Nova settings
3. ✅ Run connectivity test
4. ✅ Test with Discord bot
5. 📊 Monitor costs in AWS Cost Explorer
6. 🔔 Set up CloudWatch alarms (optional)

---

**Ready to go!** Change `BACKEND_MODE=nova` and run `uv run community-bot` 🚀
