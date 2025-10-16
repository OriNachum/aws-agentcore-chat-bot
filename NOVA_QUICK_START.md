# Quick Start: Nova Pro with AgentCore

## TL;DR

To use Amazon Nova Pro with AgentCore mode:

```powershell
# 1. Run the setup script
.\setup_nova_pro.ps1

# 2. Test configuration
uv run python test_nova_pro.py

# 3. Start using Nova Pro
uv run python src/community_bot/agentcore_app.py
```

## What is This?

This configuration lets your community bot use **Amazon Nova Pro** (AWS's latest AI model) through the **AgentCore framework** with **Bedrock integration**.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Discord Bot                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentCore Mode (agentcore_app.py)              │
│                                                              │
│  • Strands Agent Framework                                  │
│  • Prompt Management                                        │
│  • Tool Integration (KB, etc.)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Strands BedrockModel                           │
│                                                              │
│  Model: us.amazon.nova-pro-v1:0                             │
│  Temperature: 0.7                                           │
│  Max Tokens: 4096                                           │
│  Streaming: Enabled                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           AWS Bedrock Runtime API                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Amazon Nova Pro Model                          │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Files Modified

### 1. `config.py`
Added Nova Pro settings:
- `bedrock_model_id` - Model to use (default: Nova Pro)
- `bedrock_temperature` - Sampling temperature
- `bedrock_max_tokens` - Max response length
- `bedrock_streaming` - Enable streaming

### 2. `agentcore_app.py`
Updated Bedrock initialization to use configurable settings instead of hardcoded Claude model.

### 3. `.env.example`
Added Nova Pro configuration template with all available Nova models.

## Environment Variables

**Required:**
```bash
BACKEND_MODE=agentcore
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
```

**Optional (with defaults):**
```bash
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=4096
BEDROCK_STREAMING=true
```

## Model Options

| Model | ID | Best For |
|-------|-----|----------|
| **Nova Pro** | `us.amazon.nova-pro-v1:0` | Complex reasoning, long conversations |
| **Nova Lite** | `us.amazon.nova-lite-v1:0` | Balanced performance and cost |
| **Nova Micro** | `us.amazon.nova-micro-v1:0` | Fast, simple responses |

## Prerequisites

1. **AWS Account** with Bedrock access
2. **Nova Pro enabled** in Bedrock Console
3. **AWS Credentials** configured
4. **IAM permissions** for `bedrock:InvokeModel`

## Setup Methods

### Method 1: Interactive Setup (Recommended)

```powershell
.\setup_nova_pro.ps1
```

This script will:
- ✅ Set all required environment variables
- ✅ Guide you through model selection
- ✅ Check AWS credentials
- ✅ Provide next steps

### Method 2: Manual Setup

```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "bedrock"
$env:AWS_REGION = "us-east-1"
$env:BEDROCK_MODEL_ID = "us.amazon.nova-pro-v1:0"
```

### Method 3: .env File

Create/edit `.env`:
```bash
BACKEND_MODE=agentcore
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=4096
BEDROCK_STREAMING=true
```

## Testing

### 1. Test Configuration
```powershell
uv run python test_nova_pro.py
```

This runs comprehensive tests:
- ✅ Environment variables
- ✅ AWS credentials
- ✅ Module imports
- ✅ Agent initialization
- ✅ Simple query to Nova Pro

### 2. Interactive Mode
```powershell
uv run python src/community_bot/agentcore_app.py
```

Chat directly with Nova Pro:
```
You: Hello! Tell me about yourself.
Agent: [Nova Pro responds]
```

### 3. Discord Bot
```powershell
uv run community-bot
```

## Adding Knowledge Base

To enable Bedrock Knowledge Base with Nova Pro:

```bash
# Add to .env
KNOWLEDGE_BASE_ID=YOUR_KB_ID
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/YOUR_KB_ID/retrieve-and-generate
```

See `docs/BEDROCK_KB_SETUP.md` for detailed KB setup.

## Comparison with Other Modes

### Nova Pro (Current)
```bash
BACKEND_MODE=agentcore + LLM_PROVIDER=bedrock
```
- ✅ Latest AWS model
- ✅ Production-ready
- ✅ KB integration
- ❌ Requires AWS account

### Ollama Local
```bash
BACKEND_MODE=agentcore + LLM_PROVIDER=ollama
```
- ✅ Free/local
- ✅ Private
- ❌ Requires GPU
- ❌ Limited models

### Legacy Ollama
```bash
BACKEND_MODE=ollama
```
- ✅ Simple
- ❌ Fewer features
- ❌ No KB support

## Troubleshooting

**"Could not connect to endpoint"**
→ Check AWS_REGION and model availability

**"ValidationException: Invalid model identifier"**
→ Enable Nova Pro in Bedrock Console

**"AccessDeniedException"**
→ Add IAM permissions for bedrock:InvokeModel

**No response**
→ Check LLM_PROVIDER=bedrock (not ollama)

**See full troubleshooting guide:** `docs/NOVA_PRO_SETUP.md`

## Cost Estimation

Nova Pro (approximate):
- **Input**: ~$0.008 per 1K tokens
- **Output**: ~$0.024 per 1K tokens

Example: 1000 messages with ~300 tokens each ≈ $8-10

## Documentation

- **Full Setup Guide**: `docs/NOVA_PRO_SETUP.md`
- **KB Integration**: `docs/BEDROCK_KB_SETUP.md`
- **AgentCore Usage**: `docs/agentcore-use.md`
- **Environment Variables**: `docs/environment-variables-reference.md`

## Support Files

- `setup_nova_pro.ps1` - Interactive configuration
- `test_nova_pro.py` - Comprehensive testing
- `.env.example` - Configuration template

## Key Benefits

1. **State-of-the-art**: Latest Amazon Nova Pro model
2. **AWS Native**: Seamless Bedrock integration
3. **Streaming**: Real-time response streaming
4. **Knowledge Base**: RAG with Bedrock KB
5. **Production Ready**: Scalable AWS infrastructure
6. **Tool Support**: Extensible tool framework

## Next Steps

1. ✅ Run setup script
2. ✅ Test configuration
3. ✅ Try interactive mode
4. 📖 Read full docs: `docs/NOVA_PRO_SETUP.md`
5. 🚀 Deploy to production

---

**Questions?** Check `docs/NOVA_PRO_SETUP.md` for detailed documentation.
