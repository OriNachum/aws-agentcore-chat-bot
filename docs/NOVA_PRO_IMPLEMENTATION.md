# AgentCore with Nova Pro - Implementation Summary

## Overview

This document summarizes the changes made to enable **Amazon Nova Pro** with the **AgentCore mode** and **Bedrock setup**.

## How AgentCore Works

### Architecture Flow

```
Discord Message
    ↓
agent_client.py (routes to backend)
    ↓
agentcore_app.py (AgentCore backend)
    ↓
get_agent() - Creates Strands Agent
    ↓
Provider Selection (LLM_PROVIDER env var)
    ├─ "ollama" → OllamaModel (local)
    └─ "bedrock" → BedrockModel (AWS)
         ↓
    Settings from config.py
         ↓
    BedrockModel(
        model_id=settings.bedrock_model_id,      # "us.amazon.nova-pro-v1:0"
        temperature=settings.bedrock_temperature, # 0.7
        streaming=settings.bedrock_streaming      # true
    )
    ↓
AWS Bedrock Runtime API
    ↓
Amazon Nova Pro Model
```

### Key Components

1. **config.py** - Configuration management
   - Loads environment variables
   - Provides `Settings` dataclass
   - New: Bedrock model settings

2. **agentcore_app.py** - Main agent implementation
   - Uses Strands Agent framework
   - Supports multiple LLM providers
   - Tool integration (KB queries)
   - Prompt management
   - Streaming responses

3. **agent_client.py** - Backend router
   - Routes to agentcore or ollama backend
   - Handles Discord message processing

4. **discord_bot.py** - Discord integration
   - Watches configured channel
   - Splits long responses
   - Error handling

## Changes Made

### 1. Configuration (`config.py`)

**Added Settings:**
```python
# Bedrock model settings
bedrock_model_id: str = "us.amazon.nova-pro-v1:0"
bedrock_temperature: float = 0.7
bedrock_max_tokens: int = 4096
bedrock_streaming: bool = True
```

**Environment Variables:**
- `BEDROCK_MODEL_ID` - Model to use (default: Nova Pro)
- `BEDROCK_TEMPERATURE` - Sampling temperature (0.0-1.0)
- `BEDROCK_MAX_TOKENS` - Max response length
- `BEDROCK_STREAMING` - Enable streaming

### 2. Agent Initialization (`agentcore_app.py`)

**Before:**
```python
# Hardcoded to Claude
model = BedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    temperature=0.3,
    streaming=True
)
```

**After:**
```python
# Configurable via settings
model = BedrockModel(
    model_id=settings.bedrock_model_id,
    temperature=settings.bedrock_temperature,
    streaming=settings.bedrock_streaming
)
```

### 3. Environment File (`.env.example`)

**Added:**
- Nova Pro as default Bedrock model
- Documentation for all Nova models
- Configuration examples for different use cases

## Nova Pro Integration

### How It Works

1. **Environment Setup**
   ```bash
   BACKEND_MODE=agentcore
   LLM_PROVIDER=bedrock
   BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
   ```

2. **Agent Creation**
   - `get_agent()` reads `LLM_PROVIDER`
   - Creates `BedrockModel` with Nova Pro settings
   - Wraps in Strands `Agent` with tools

3. **Request Flow**
   - User message → Discord
   - `agent_client.py` routes to agentcore
   - `chat_with_agent()` processes message
   - Optionally queries Knowledge Base
   - Composes prompt with context
   - Sends to Nova Pro via `BedrockModel`
   - Streams response back

4. **Response Handling**
   - Nova Pro generates response
   - Streamed through Bedrock API
   - Formatted and sent to Discord

### Knowledge Base Integration

AgentCore mode supports AWS Bedrock Knowledge Base:

```python
# In agentcore_app.py
@tool
def kb_query_tool(query: str, ctx: ToolContext) -> str:
    """Query knowledge base for relevant information."""
    # Queries Bedrock KB using boto3
    # Returns relevant documents
```

Flow:
1. User asks question
2. Agent determines if KB query needed
3. Queries Bedrock KB via `kb_query_tool`
4. KB returns relevant documents
5. Documents added to context
6. Nova Pro generates response with context

## Configuration Options

### Provider Selection

```bash
# Local Ollama
BACKEND_MODE=agentcore
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3

# AWS Bedrock (Nova Pro)
BACKEND_MODE=agentcore
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
```

### Model Selection

```bash
# Nova Pro (recommended)
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0

# Nova Lite (faster, cheaper)
BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0

# Nova Micro (fastest, cheapest)
BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0

# Claude 3.5 Sonnet
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
```

### Temperature Settings

```bash
# More focused/deterministic
BEDROCK_TEMPERATURE=0.3

# Balanced (default)
BEDROCK_TEMPERATURE=0.7

# More creative
BEDROCK_TEMPERATURE=1.0
```

## Testing

### Test Files Created

1. **`test_nova_pro.py`** - Comprehensive test suite
   - Configuration validation
   - Module import tests
   - Agent initialization
   - Simple query test

2. **`setup_nova_pro.ps1`** - Interactive setup
   - Guides through configuration
   - Sets environment variables
   - Validates AWS credentials
   - Provides next steps

### Running Tests

```powershell
# Full test suite
uv run python test_nova_pro.py

# Interactive mode
uv run python src/community_bot/agentcore_app.py

# Discord bot
uv run community-bot
```

## Documentation Created

1. **`NOVA_QUICK_START.md`** - Quick reference guide
2. **`docs/NOVA_PRO_SETUP.md`** - Comprehensive setup guide
3. **Updated `README.md`** - Nova Pro section
4. **Updated `.env.example`** - Nova Pro defaults

## Prerequisites

### AWS Requirements

1. **AWS Account** with Bedrock access
2. **Nova Pro Enabled** in Bedrock Console
   - Go to Bedrock → Model Access
   - Enable "Amazon Nova Pro"
3. **IAM Permissions**:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:InvokeModel",
       "bedrock:InvokeModelWithResponseStream"
     ],
     "Resource": "arn:aws:bedrock:*::foundation-model/amazon.nova-*"
   }
   ```

### Local Requirements

1. **Python 3.11+**
2. **uv** package manager
3. **AWS credentials** configured
4. **Dependencies** installed (`uv sync`)

## Comparison: Nova vs Existing Implementations

### Existing Nova Files

The codebase already has:
- `nova_model.py` - Direct Nova API wrapper
- `nova_agent.py` - Standalone Nova agent

These are **separate** implementations that:
- Use boto3 directly (not Strands framework)
- Have their own memory management
- Don't integrate with AgentCore flow

### New Implementation (This PR)

Uses **Strands framework** through AgentCore:
- Integrates with existing AgentCore flow
- Uses `BedrockModel` from Strands
- Shares tools, prompts, KB integration
- Consistent with other backends

**Benefit**: Switching between models is just changing config, no code changes.

## Troubleshooting

### Common Issues

1. **"ValidationException: Invalid model identifier"**
   - **Fix**: Enable Nova Pro in Bedrock Console

2. **"AccessDeniedException"**
   - **Fix**: Add IAM permissions for `bedrock:InvokeModel`

3. **No response from agent**
   - **Fix**: Check `LLM_PROVIDER=bedrock` (not `ollama`)

4. **"Could not connect to endpoint"**
   - **Fix**: Verify `AWS_REGION` and model availability

### Debug Mode

```bash
LOG_LEVEL=DEBUG
```

Shows:
- Configuration loading
- Provider selection
- Model initialization
- Request/response details
- KB queries
- Prompt composition

## Next Steps

1. **Test Configuration**: Run `test_nova_pro.py`
2. **Try Interactive Mode**: Test Nova Pro directly
3. **Add Knowledge Base**: Follow KB setup guide
4. **Customize Prompts**: Edit files in `agents/default/`
5. **Deploy to Production**: AWS Lambda or ECS

## Files Modified

### Core Files
- ✅ `src/community_bot/config.py` - Added Bedrock settings
- ✅ `src/community_bot/agentcore_app.py` - Configurable model selection
- ✅ `.env.example` - Nova Pro defaults

### Documentation
- ✅ `NOVA_QUICK_START.md` - Quick reference
- ✅ `docs/NOVA_PRO_SETUP.md` - Full guide
- ✅ `README.md` - Updated features section

### Tools
- ✅ `test_nova_pro.py` - Test suite
- ✅ `setup_nova_pro.ps1` - Setup script

### Existing (Not Modified)
- `nova_model.py` - Standalone implementation
- `nova_agent.py` - Standalone implementation
- `agent_client.py` - Routing logic
- `discord_bot.py` - Discord integration

## Summary

The implementation enables Nova Pro through the **existing AgentCore framework** by:

1. ✅ Adding configuration options for Bedrock models
2. ✅ Making model selection configurable (not hardcoded)
3. ✅ Providing setup tools and documentation
4. ✅ Maintaining compatibility with existing backends

**No breaking changes** - existing configurations continue to work.

**Switching to Nova Pro** is as simple as:
```bash
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
```

---

**Ready to use Nova Pro?** Run `.\setup_nova_pro.ps1` to get started!
