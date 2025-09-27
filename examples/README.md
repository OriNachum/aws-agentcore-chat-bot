# LocalAgent Framework Examples

This directory contains examples demonstrating the new LocalAgent framework and its integration with AgentCore and Strands.

## Examples

### 1. `test_local_agent.py`
Basic test of the LocalAgent framework functionality.

**Features tested:**
- LocalAgent initialization
- Conversation flow with memory
- Memory management and limits
- System prompt customization

**Requirements:**
- Ollama running locally
- A model pulled (e.g., `ollama pull llama3.1`)

**Usage:**
```bash
cd examples
python test_local_agent.py
```

### 2. `agentcore_integration_example.py`
Conceptual example showing integration with AWS AgentCore and Strands.

**Features demonstrated:**
- Enhanced LocalAgent with multiple backends
- Strands integration with tools
- AgentCore deployment pattern
- Hybrid agent approach

**Requirements (for full functionality):**
```bash
pip install strands-agents bedrock-agentcore
```

**Usage:**
```bash
cd examples
python agentcore_integration_example.py
```

## Architecture Overview

The new LocalAgent framework follows this structure:

```
Discord Bot
    ↓
AgentClient (Entry Point)
    ↓
LocalAgent (Orchestrator)
    ├── OllamaModel (AI Provider)
    └── ConversationMemory (Context Management)
```

### Integration with External Frameworks

```
Discord Bot
    ↓
EnhancedLocalAgent
    ├── LocalAgent (Our Framework)
    ├── Strands Agent (Tools & Enhanced Reasoning)
    └── AgentCore (Deployment & Management)
```

## Configuration

The framework supports these environment variables:

```env
# Core settings
BACKEND_MODE=ollama
DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=123456789

# Ollama settings
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434

# LocalAgent framework settings
MEMORY_MAX_MESSAGES=50
SYSTEM_PROMPT="Custom system prompt"
PROMPT_PROFILE=default
PROMPT_ROOT=../agents
PROMPT_USER_ROLE=user
MAX_RESPONSE_CHARS=1800
```

Place prompt files under the repository `agents/` directory. When running examples from this folder, relative `PROMPT_ROOT=../agents` keeps the loader pointed at the shared prompts.

## Testing Without External Dependencies

The `test_local_agent.py` script can test core functionality with just Ollama:

1. **Memory Management Test**: Tests conversation memory limits (no Ollama required)
2. **LocalAgent Test**: Tests full conversation flow (requires Ollama)

## Future Enhancements

When the external SDKs become available, the integration examples can be enhanced with:

- **Strands Tools**: Calculator, web search, file operations
- **AgentCore Features**: Authentication, observability, scaling
- **Advanced Memory**: Persistent storage, semantic search
- **Multi-Agent Workflows**: Agent collaboration and handoffs
