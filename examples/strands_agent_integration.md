# Strands Agent Integration Example

This example demonstrates how to use the new Strands-based agent system that replaces the legacy LocalAgent framework.

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Run the interactive agent:**
   ```bash
   python src/community_bot/agentcore_app.py
   ```

3. **Use in your code:**
   ```python
   from community_bot.agentcore_app import chat_with_agent
   
   response = chat_with_agent("Hello, how can you help me?")
   print(response)
   ```

## Configuration

The agent supports both Ollama and Bedrock models:

### Ollama (Default)
```bash
export LLM_PROVIDER=ollama
```

### Amazon Bedrock
```bash
export LLM_PROVIDER=bedrock
```

## Model Configuration

The agent reads from your existing configuration files:
- `settings.ollama_model` - Model name (default: "llama3")
- `settings.ollama_base_url` - Ollama server URL (default: "http://localhost:11434")

## Integration with Discord Bot

The `agentcore_app.py` provides a `chat_with_agent()` function that can be easily integrated with the existing Discord bot:

```python
from community_bot.agentcore_app import chat_with_agent

# In your Discord bot handler
@bot.event
async def on_message(message):
    if message.author != bot.user:
        response = chat_with_agent(message.content)
        await message.channel.send(response)
```

## Key Differences from LocalAgent

1. **Simpler API**: Just call `chat_with_agent(message)` instead of managing agent state
2. **Model Agnostic**: Easy switching between Ollama and Bedrock
3. **Strands Framework**: Built on the modern Strands agents framework
4. **Better Error Handling**: Graceful fallbacks for connection issues

## Testing

Run the test script to verify your setup:

```bash
python test_strands_agent.py
```

This will test both Ollama and Bedrock model creation (without requiring actual connections).