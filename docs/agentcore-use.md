# AgentCore Integration Guide

This document explains how to use the new AgentCore integration with Strands agents in the community bot project.

## Overview

The community bot has been modernized to use the [Strands Agents](https://strandsagents.com/) framework, which provides a model-agnostic approach to building AI agents. This allows seamless switching between local models (like Ollama) and cloud providers (like Amazon Bedrock).

## Architecture

The new architecture consists of:

- **`agentcore_app.py`** - Main agent application using Strands framework
- **Model Providers** - Support for Ollama (local) and Bedrock (cloud)
- **Lazy Loading** - Agent is initialized only when needed
- **Simple API** - Easy integration with existing Discord bot

## Installation & Setup

### 1. Install Dependencies

The required dependencies are already defined in `pyproject.toml`:

```bash
uv sync
# or if you don't have uv:
pip install -e .
```

### 2. Configure Environment

Set your preferred model provider:

```bash
# For Ollama (default)
export LLM_PROVIDER=ollama

# For Amazon Bedrock
export LLM_PROVIDER=bedrock
```

### 3. Verify Configuration

Your existing configuration files will be used:
- `settings.ollama_model` - Model name (default: "llama3")
- `settings.ollama_base_url` - Ollama server URL (default: "http://localhost:11434")

### Prompt Profiles

Local and AgentCore paths now share a file-based prompt system. Profiles live under `agents/<profile>/` with:

- `<profile>.system.md` (required) — initial system message
- `<profile>.user.md` (optional) — primer inserted as the first user message
- Additional files like `<profile>.tool.md` or `<profile>.safety.md` (optional) for future tooling

Key environment variables:

```env
SYSTEM_PROMPT="Inline override for the system prompt"
PROMPT_PROFILE=default
PROMPT_ROOT=./agents
PROMPT_USER_ROLE=user
```

- `SYSTEM_PROMPT` overrides the file while still allowing primers and extras from disk.
- Relative `PROMPT_ROOT` paths are resolved against the working directory, so repos can bundle prompts alongside code.
- Adjust `PROMPT_USER_ROLE` if a primer should appear as `system`, `assistant`, or another supported role.

## Usage

### Running the Interactive Agent

Start the agent in interactive mode for testing:

```bash
python src/community_bot/agentcore_app.py
```

This will start a chat session where you can test the agent directly:

```
You: Hello! How can you help me?
Agent: [Response from your configured model]
You: Tell me about Python
Agent: [Detailed explanation about Python]
You: quit
```

### Using in Your Code

Import and use the agent function in your applications:

```python
from community_bot.agentcore_app import chat_with_agent

# Simple usage
response = chat_with_agent("Hello! How can you help me?")
print(response)

# In a Discord bot
@bot.event
async def on_message(message):
    if message.author != bot.user:
        response = chat_with_agent(message.content)
        await message.channel.send(response)

# Error handling
try:
    response = chat_with_agent(user_input)
    print(f"Agent: {response}")
except Exception as e:
    print(f"Error: {e}")
    # Fallback response
    response = "I'm sorry, I'm having trouble connecting to the AI service right now."
```

### Testing the Setup

Run the test script to verify your configuration:

```bash
python test_strands_agent.py
```

This will test both Ollama and Bedrock model creation and show you what's working.

Run the Discord integration example:

```bash
python examples/discord_integration_example.py
```

## Model Providers

### Ollama (Local Development)

**Configuration:**
```bash
export LLM_PROVIDER=ollama
```

**Requirements:**
- Ollama server running locally
- Model downloaded (e.g., `ollama pull llama3`)

**Settings:**
- `settings.ollama_model` - Model name (e.g., "llama3", "gpt-oss:20b")
- `settings.ollama_base_url` - Server URL (e.g., "http://localhost:11434")

**Example:**
```python
# Uses your existing Ollama configuration
response = chat_with_agent("Explain Python decorators")
```

### Amazon Bedrock (Cloud)

**Configuration:**
```bash
export LLM_PROVIDER=bedrock
```

**Requirements:**
- AWS credentials configured
- Access to Claude models in your region

**Model Used:**
- `anthropic.claude-3-sonnet-20240229-v1:0`

**Example:**
```python
# Uses AWS Bedrock Claude model
response = chat_with_agent("Write a Python function")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Model provider: `ollama` or `bedrock` |

## Migration from LocalAgent

The new system replaces the previous `LocalAgent` framework:

### Before (LocalAgent)
```python
from community_bot.local_agent import LocalAgent, OllamaModel, ConversationMemory

model = OllamaModel(settings)
memory = ConversationMemory(max_messages=10)
agent = LocalAgent(model, memory)

async for chunk in agent.chat(message):
    print(chunk, end='')
```

### After (Strands AgentCore)
```python
from community_bot.agentcore_app import chat_with_agent

response = chat_with_agent(message)
print(response)
```

## Key Benefits

1. **Simplified API** - One function call instead of managing agent state
2. **Model Agnostic** - Easy switching between local and cloud models
3. **Better Error Handling** - Graceful fallbacks for connection issues
4. **Modern Framework** - Built on actively maintained Strands SDK
5. **Lazy Loading** - No initialization overhead until needed
6. **Backward Compatible** - Easy integration with existing Discord bot

## Troubleshooting

### Ollama Connection Issues

If you see "All connection attempts failed":

1. **Check Ollama is running:**
   ```bash
   ollama list
   ```

2. **Verify your model is available:**
   ```bash
   ollama pull llama3
   ```

3. **Check configuration:**
   - Verify `settings.ollama_base_url` points to your Ollama server
   - Verify `settings.ollama_model` matches an available model

### Import Errors

If you see import errors when running the agent directly:

```bash
# Run from project root
python src/community_bot/agentcore_app.py

# Or use the test script
python test_strands_agent.py
```

### Bedrock Issues

If you see AWS/Bedrock errors:

1. **Check AWS credentials:**
   ```bash
   aws sts get-caller-identity
   ```

2. **Verify model access:**
   - Ensure you have access to Claude models in your region
   - Check the model ID is correct

## Examples

See the `examples/` directory for complete working examples:

- `examples/strands_agent_integration.md` - Integration guide
- `examples/discord_integration_example.py` - Discord bot integration
- `test_strands_agent.py` - Setup verification

## Support

The agent uses the [Strands Agents](https://strandsagents.com/) framework. For framework-specific issues, refer to:

- [Strands Documentation](https://strandsagents.com/)
- [Strands GitHub](https://github.com/strands-agents/sdk-python)
- [Ollama Documentation](https://ollama.ai/docs)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)