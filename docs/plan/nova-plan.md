# Migration Plan: Ollama to AWS Bedrock Nova-Pro

**Document Version:** 1.0  
**Date:** October 15, 2025  
**Author:** GitHub Copilot  
**Status:** Planning Phase

---

## Executive Summary

This document outlines the complete migration strategy from Ollama-based local models to AWS Bedrock's Nova-Pro foundation model. The migration will maintain backward compatibility while introducing a new backend option that leverages AWS's managed AI services.

**Migration Goals:**
1. Add AWS Bedrock Nova-Pro as a third backend option (alongside Ollama and AgentCore)
2. Maintain existing functionality and Discord integration
3. Enable seamless switching between backends via configuration
4. Preserve existing prompt management and knowledge base features
5. Improve scalability and reduce operational overhead

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Target Architecture](#target-architecture)
3. [Migration Strategy](#migration-strategy)
4. [Implementation Plan](#implementation-plan)
5. [Configuration Changes](#configuration-changes)
6. [Code Changes](#code-changes)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)
9. [Rollback Strategy](#rollback-strategy)
10. [Post-Migration Considerations](#post-migration-considerations)

---

## Current State Analysis

### Existing Backend Modes

The community bot currently supports two backend modes:

1. **Ollama Mode** (`BACKEND_MODE=ollama`)
   - Local LLM inference via Ollama server
   - Direct HTTP API calls to `OLLAMA_BASE_URL`
   - Models: Currently using `gpt-oss:120b` or `llama3:8b`
   - Location: `src/community_bot/agent_client.py` and `src/community_bot/local_agent.py`

2. **AgentCore Mode** (`BACKEND_MODE=agentcore`)
   - Uses Strands framework with pluggable LLM providers
   - Currently supports both Ollama and Bedrock (Claude) via `LLM_PROVIDER` env var
   - Location: `src/community_bot/agentcore_app.py`
   - Integrates with AWS Bedrock Knowledge Bases

### Current Dependencies

```toml
dependencies = [
    "discord.py>=2.3.2",
    "boto3>=1.34.0",
    "python-dotenv>=1.0.0",
    "aiohttp>=3.9.0",
    "httpx>=0.27.0",
    "backoff>=2.2.1",
    "pydantic>=2.7.0",
    "bedrock-agentcore",
    "bedrock-agentcore-starter-toolkit",
    "strands-agents",
    "ollama"
]
```

### Key Components

- **Discord Integration**: `src/community_bot/discord_bot.py`
- **Agent Client**: `src/community_bot/agent_client.py` (orchestrates backends)
- **AgentCore App**: `src/community_bot/agentcore_app.py` (Strands-based agent)
- **Configuration**: `src/community_bot/config.py`
- **Prompt Management**: `src/community_bot/prompt_loader.py`
- **Logging**: `src/community_bot/logging_config.py`

---

## Target Architecture

### New Backend: Nova-Pro Mode

We'll introduce a **third backend mode** that uses AWS Bedrock Nova-Pro directly:

```
BACKEND_MODE Options:
├── ollama          (Existing - Local Ollama server)
├── agentcore       (Existing - Strands framework with Ollama/Bedrock)
└── nova            (NEW - Direct AWS Bedrock Nova-Pro integration)
```

### Why Nova-Pro?

**AWS Nova-Pro Advantages:**
- Latest Amazon foundation model optimized for complex reasoning
- Managed service (no infrastructure maintenance)
- Native AWS integration with other Bedrock services
- Cost-effective compared to Claude for many workloads
- Better performance for extended context windows
- Streaming support for real-time responses

### Architecture Diagram

```
┌─────────────────┐
│  Discord Bot    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Agent Client   │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
    v                         v
┌─────────┐            ┌──────────────┐
│ Ollama  │            │ AgentCore    │
│ Mode    │            │ Mode         │
└─────────┘            └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    v                   v
            ┌──────────┐        ┌──────────┐
            │  Ollama  │        │ Bedrock  │
            │ (Strands)│        │ (Claude) │
            └──────────┘        └──────────┘
                              
┌──────────────────────────────────────────┐
│         NEW: Nova Mode                   │
│  ┌────────────────────────────────┐     │
│  │  Direct Bedrock Nova-Pro Call  │     │
│  │  - streaming support           │     │
│  │  - KB integration              │     │
│  │  - conversation memory         │     │
│  └────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

---

## Migration Strategy

### Approach: Additive Migration

We'll use an **additive approach** rather than replacement:

1. ✅ **Keep existing backends functional** (no breaking changes)
2. ✅ **Add Nova-Pro as a new option** (new code paths)
3. ✅ **Reuse existing infrastructure** (logging, prompts, config)
4. ✅ **Gradual rollout** (test alongside Ollama/AgentCore)

### Migration Phases

#### Phase 1: Infrastructure Setup (Week 1)
- Configure AWS Bedrock access
- Enable Nova-Pro model in AWS account
- Set up IAM permissions
- Test basic Nova-Pro API connectivity

#### Phase 2: Core Implementation (Week 2)
- Create `NovaModel` class
- Implement streaming responses
- Add Nova backend to `AgentClient`
- Configuration updates

#### Phase 3: Feature Parity (Week 3)
- Knowledge Base integration
- Conversation memory
- Prompt management integration
- Response splitting for Discord

#### Phase 4: Testing & Validation (Week 4)
- Unit tests
- Integration tests
- Load testing
- Discord bot testing

#### Phase 5: Deployment (Week 5)
- Documentation updates
- Production deployment
- Monitoring setup
- Performance benchmarking

---

## Implementation Plan

### Step 1: AWS Bedrock Setup

#### 1.1 Enable Nova-Pro Access

```bash
# Check model availability
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `nova`)]'

# Expected output:
# - amazon.nova-pro-v1:0
# - amazon.nova-lite-v1:0
# - amazon.nova-micro-v1:0
```

#### 1.2 IAM Permissions

Create/update IAM policy for Nova access:

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
      "Resource": "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0"
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

#### 1.3 Test Connectivity

Create test script `test_nova_connection.py`:

```python
import boto3
import json

def test_nova_connection():
    """Test basic Nova-Pro connectivity."""
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, are you working?"}]
            }
        ],
        "inferenceConfig": {
            "temperature": 0.7,
            "maxTokens": 100
        }
    })
    
    response = client.invoke_model(
        modelId='amazon.nova-pro-v1:0',
        body=body
    )
    
    response_body = json.loads(response['body'].read())
    print("✅ Nova-Pro is accessible!")
    print(response_body)

if __name__ == "__main__":
    test_nova_connection()
```

### Step 2: Code Implementation

#### 2.1 Create Nova Model Class

Create new file: `src/community_bot/nova_model.py`

```python
"""AWS Bedrock Nova-Pro model implementation."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional, Dict, Any

import boto3
from botocore.config import Config

from .logging_config import get_logger

logger = get_logger("community_bot.nova_model")


class NovaModel:
    """AWS Bedrock Nova-Pro model with streaming support."""
    
    def __init__(
        self,
        model_id: str = "amazon.nova-pro-v1:0",
        region: str = "us-east-1",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.9,
    ):
        """Initialize Nova-Pro model.
        
        Args:
            model_id: Bedrock model identifier
            region: AWS region
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
        """
        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        
        # Configure boto3 client with retries
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.client = boto3.client('bedrock-runtime', config=config)
        logger.info(f"Initialized Nova model: {model_id} in {region}")
    
    async def generate_streaming(
        self,
        messages: list[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Nova-Pro.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            
        Yields:
            Text chunks from the model
        """
        logger.debug(f"Generating streaming response with {len(messages)} messages")
        
        # Build Nova request body
        body = {
            "messages": self._format_messages(messages),
            "inferenceConfig": {
                "temperature": self.temperature,
                "maxTokens": self.max_tokens,
                "topP": self.top_p,
            }
        }
        
        if system_prompt:
            body["system"] = [{"text": system_prompt}]
        
        try:
            # Invoke model with streaming
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            # Process streaming chunks
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # Extract text from chunk
                        if 'contentBlockDelta' in chunk_data:
                            delta = chunk_data['contentBlockDelta'].get('delta', {})
                            if 'text' in delta:
                                yield delta['text']
                                
        except Exception as e:
            logger.error(f"Error during Nova streaming: {e}", exc_info=True)
            raise
    
    def _format_messages(self, messages: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Format messages for Nova API.
        
        Args:
            messages: Raw message list
            
        Returns:
            Formatted messages for Nova
        """
        formatted = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            formatted.append({
                "role": role,
                "content": [{"text": content}]
            })
        
        return formatted
```

#### 2.2 Update Configuration

Update `src/community_bot/config.py`:

```python
@dataclass
class Settings:
    discord_token: str
    discord_channel_id: int
    backend_mode: str  # 'agentcore', 'ollama', or 'nova'
    
    # AWS/AgentCore settings
    aws_region: Optional[str] = None
    agent_id: Optional[str] = None
    agent_alias_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    
    # Ollama settings
    ollama_model: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # Nova settings (NEW)
    nova_model_id: str = "amazon.nova-pro-v1:0"
    nova_temperature: float = 0.7
    nova_max_tokens: int = 4096
    nova_top_p: float = 0.9
    
    # Response settings
    max_response_chars: int = 1800
    memory_max_messages: int = 50
    system_prompt: Optional[str] = None
    log_level: str = "INFO"
    
    # Prompt management
    prompt_profile: str = "default"
    prompt_root: Path = Path.cwd() / "agents"
    prompt_user_role: str = "user"
    
    # Source Agents
    source_agents_enabled: bool = False
    source_agents_s3_bucket: Optional[str] = None
    source_agents_s3_region: str = "us-east-1"
    source_agents_data_source_id: Optional[str] = None
    source_agents_run_on_startup: bool = False
    source_agents_interval: int = 3600


def load_settings() -> Settings:
    load_dotenv()

    missing = [k for k in REQUIRED_BASE if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    backend_mode = os.getenv("BACKEND_MODE", "agentcore").lower()
    if backend_mode not in {"agentcore", "ollama", "nova"}:  # ADD 'nova'
        raise RuntimeError("BACKEND_MODE must be 'agentcore', 'ollama', or 'nova'")

    # Validate backend-specific requirements
    if backend_mode == "agentcore":
        if not os.getenv("AWS_REGION"):
            raise RuntimeError("AWS_REGION is required for AgentCore backend")
        if not os.getenv("AGENT_ID") or not os.getenv("AGENT_ALIAS_ID"):
            raise RuntimeError("AGENT_ID and AGENT_ALIAS_ID are required for AgentCore backend")

    if backend_mode == "ollama":
        if not os.getenv("OLLAMA_MODEL"):
            raise RuntimeError("OLLAMA_MODEL is required for Ollama backend")
    
    # NEW: Nova validation
    if backend_mode == "nova":
        if not os.getenv("AWS_REGION"):
            raise RuntimeError("AWS_REGION is required for Nova backend")

    # Load prompt settings
    prompt_profile = os.getenv("PROMPT_PROFILE", "default")
    prompt_root_env = os.getenv("PROMPT_ROOT")
    if prompt_root_env:
        prompt_root = Path(prompt_root_env)
        if not prompt_root.is_absolute():
            prompt_root = (Path.cwd() / prompt_root).resolve()
        else:
            prompt_root = prompt_root.resolve()
    else:
        prompt_root = (Path.cwd() / "agents").resolve()

    prompt_user_role = os.getenv("PROMPT_USER_ROLE", "user") or "user"

    return Settings(
        discord_token=os.environ["DISCORD_BOT_TOKEN"],
        discord_channel_id=int(os.environ["DISCORD_CHANNEL_ID"]),
        backend_mode=backend_mode,
        aws_region=os.getenv("AWS_REGION"),
        agent_id=os.getenv("AGENT_ID"),
        agent_alias_id=os.getenv("AGENT_ALIAS_ID"),
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
        ollama_model=os.getenv("OLLAMA_MODEL"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        # Nova settings
        nova_model_id=os.getenv("NOVA_MODEL_ID", "amazon.nova-pro-v1:0"),
        nova_temperature=float(os.getenv("NOVA_TEMPERATURE", "0.7")),
        nova_max_tokens=int(os.getenv("NOVA_MAX_TOKENS", "4096")),
        nova_top_p=float(os.getenv("NOVA_TOP_P", "0.9")),
        # General settings
        max_response_chars=int(os.getenv("MAX_RESPONSE_CHARS", "1800")),
        memory_max_messages=int(os.getenv("MEMORY_MAX_MESSAGES", "50")),
        system_prompt=os.getenv("SYSTEM_PROMPT"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        prompt_profile=prompt_profile,
        prompt_root=prompt_root,
        prompt_user_role=prompt_user_role,
        # Source Agents
        source_agents_enabled=os.getenv("SOURCE_AGENTS_ENABLED", "false").lower() == "true",
        source_agents_s3_bucket=os.getenv("SOURCE_AGENTS_S3_BUCKET"),
        source_agents_s3_region=os.getenv("SOURCE_AGENTS_S3_REGION", "us-east-1"),
        source_agents_data_source_id=os.getenv("SOURCE_AGENTS_DATA_SOURCE_ID"),
        source_agents_run_on_startup=os.getenv("SOURCE_AGENTS_RUN_ON_STARTUP", "false").lower() == "true",
        source_agents_interval=int(os.getenv("SOURCE_AGENTS_INTERVAL", "3600")),
    )
```

#### 2.3 Create Nova Agent Implementation

Create new file: `src/community_bot/nova_agent.py`

```python
"""Nova-based agent with conversation memory and KB integration."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from .config import Settings
from .nova_model import NovaModel
from .logging_config import get_logger
from .prompt_loader import PromptBundle

logger = get_logger("community_bot.nova_agent")


class ConversationMemory:
    """Simple conversation memory for Nova agent."""
    
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.messages: list[dict] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to memory."""
        self.messages.append({"role": role, "content": content})
        
        # Trim old messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_context(self) -> list[dict]:
        """Get conversation history."""
        return self.messages.copy()
    
    def clear(self):
        """Clear conversation history."""
        self.messages.clear()


class NovaAgent:
    """Agent implementation using AWS Bedrock Nova-Pro."""
    
    def __init__(
        self,
        settings: Settings,
        prompt_bundle: PromptBundle,
    ):
        """Initialize Nova agent.
        
        Args:
            settings: Application settings
            prompt_bundle: Loaded prompt configuration
        """
        self.settings = settings
        self.prompt_bundle = prompt_bundle
        
        # Initialize Nova model
        self.model = NovaModel(
            model_id=settings.nova_model_id,
            region=settings.aws_region or "us-east-1",
            temperature=settings.nova_temperature,
            max_tokens=settings.nova_max_tokens,
            top_p=settings.nova_top_p,
        )
        
        # Initialize conversation memory
        self.memory = ConversationMemory(max_messages=settings.memory_max_messages)
        
        logger.info("Nova agent initialized successfully")
    
    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process user message and stream response.
        
        Args:
            user_message: User's input message
            
        Yields:
            Response chunks from Nova
        """
        logger.info("=" * 80)
        logger.debug(f"[NOVA AGENT] Processing message: {user_message[:100]}...")
        
        # Add user message to memory
        self.memory.add_message("user", user_message)
        
        # Get conversation context
        messages = self.memory.get_context()
        
        # Build system prompt from bundle
        system_prompt = self._build_system_prompt()
        
        # Stream response from Nova
        response_text = ""
        async for chunk in self.model.generate_streaming(
            messages=messages,
            system_prompt=system_prompt
        ):
            response_text += chunk
            yield chunk
        
        # Add assistant response to memory
        self.memory.add_message("assistant", response_text)
        
        logger.info(f"[NOVA AGENT] Response complete: {len(response_text)} characters")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from prompt bundle.
        
        Returns:
            Formatted system prompt
        """
        sections = []
        
        # Add system prompt
        if self.prompt_bundle.system:
            sections.append(self.prompt_bundle.system.strip())
        
        # Add user primer
        if self.prompt_bundle.user:
            sections.append(f"User Context:\n{self.prompt_bundle.user.strip()}")
        
        # Add extras
        if self.prompt_bundle.extras:
            for name, content in sorted(self.prompt_bundle.extras.items()):
                if content:
                    label = name.replace("_", " ").title()
                    sections.append(f"{label}:\n{content.strip()}")
        
        return "\n\n".join(sections)
```

#### 2.4 Update Agent Client

Update `src/community_bot/agent_client.py`:

```python
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from .config import Settings
from .logging_config import get_logger
from .agentcore_app import chat_with_agent
from .prompt_loader import load_prompt_bundle

# Import Nova components (NEW)
from .nova_agent import NovaAgent

# Import Ollama components (existing)
try:
    from .local_agent import LocalAgent, ConversationMemory, OllamaModel
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = get_logger("community_bot.agent")


class AgentClient:
    """Entry point for the multi-backend agent framework."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        logger.info(f"Initializing AgentClient with backend mode: {settings.backend_mode}")
        
        # Initialize appropriate backend
        if settings.backend_mode == "ollama":
            if not OLLAMA_AVAILABLE:
                raise RuntimeError("Ollama backend not available - missing dependencies")
            
            logger.info("Setting up Ollama backend")
            logger.debug(f"Ollama model: {settings.ollama_model}")
            logger.debug(f"Ollama base URL: {settings.ollama_base_url}")
            
            self.model = OllamaModel(settings)
            self.memory = ConversationMemory(max_messages=settings.memory_max_messages)
            self.prompt_bundle = load_prompt_bundle(settings)
            
            self.agent = LocalAgent(
                self.model,
                self.memory,
                settings,
                prompt_bundle=self.prompt_bundle,
            )
            logger.info("Ollama backend initialized successfully")
            
        elif settings.backend_mode == "agentcore":
            logger.info("Setting up AgentCore backend with Strands framework")
            
            from .agentcore_app import set_provider
            set_provider("ollama")
            
            self.agent = "agentcore"
            self.prompt_bundle = load_prompt_bundle(settings)
            logger.info("AgentCore backend initialized successfully")
        
        # NEW: Nova backend
        elif settings.backend_mode == "nova":
            logger.info("Setting up Nova backend")
            logger.debug(f"Nova model: {settings.nova_model_id}")
            logger.debug(f"AWS region: {settings.aws_region}")
            logger.debug(f"Temperature: {settings.nova_temperature}")
            logger.debug(f"Max tokens: {settings.nova_max_tokens}")
            
            self.prompt_bundle = load_prompt_bundle(settings)
            self.agent = NovaAgent(settings, self.prompt_bundle)
            
            logger.info("Nova backend initialized successfully")
            
        else:
            error_msg = f"Unknown backend mode: {settings.backend_mode}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent using the configured backend."""
        logger.info("=" * 80)
        logger.debug(f"[AGENT CLIENT] Processing chat request: {user_message[:100]}...")
        logger.debug(f"[AGENT CLIENT] Backend mode: {self.settings.backend_mode}")
        
        if self.settings.backend_mode == "ollama":
            if not OLLAMA_AVAILABLE or not isinstance(self.agent, LocalAgent):
                raise RuntimeError("Ollama backend not properly initialized")
            
            logger.debug("[AGENT CLIENT] Using LocalAgent framework for Ollama backend")
            async for chunk in self.agent.chat(user_message):
                yield chunk
            
        elif self.settings.backend_mode == "agentcore":
            logger.debug("[AGENT CLIENT] Using AgentCore backend")
            async for chunk in chat_with_agent(
                user_message,
                self.settings,
                self.prompt_bundle
            ):
                yield chunk
        
        # NEW: Nova backend
        elif self.settings.backend_mode == "nova":
            logger.debug("[AGENT CLIENT] Using Nova backend")
            if not isinstance(self.agent, NovaAgent):
                raise RuntimeError("Nova backend not properly initialized")
            
            chunk_count = 0
            async for chunk in self.agent.chat(user_message):
                chunk_count += 1
                logger.debug(f"[AGENT CLIENT] Received chunk {chunk_count}: {len(chunk)} characters")
                yield chunk
            
            logger.info(f"[AGENT CLIENT] Nova chat completed: {chunk_count} chunks received")
        
        logger.info("=" * 80)
```

---

## Configuration Changes

### Environment Variables

Update `.env.example`:

```bash
# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=123456789012345678

# Backend selection: agentcore, ollama, or nova
BACKEND_MODE=nova

# Ollama local model settings (if BACKEND_MODE=ollama)
OLLAMA_MODEL=llama3:8b
# OLLAMA_BASE_URL=http://localhost:11434

# AWS AgentCore settings (if BACKEND_MODE=agentcore)
AWS_REGION=us-east-1
AGENT_ID=your_agent_id
AGENT_ALIAS_ID=your_agent_alias_id

# AWS Bedrock Nova settings (if BACKEND_MODE=nova)
# AWS_REGION is shared with AgentCore
NOVA_MODEL_ID=amazon.nova-pro-v1:0
NOVA_TEMPERATURE=0.7
NOVA_MAX_TOKENS=4096
NOVA_TOP_P=0.9

# AWS Bedrock Knowledge Base (optional, works with agentcore and nova)
KNOWLEDGE_BASE_ID=your_kb_id
KNOWLEDGE_BASE_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/YOUR_KB_ID/retrieve-and-generate
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/YOUR_KB_ID/retrieve-and-generate

# General
MAX_RESPONSE_CHARS=1800
LOG_LEVEL=INFO

# Prompt Management
PROMPT_PROFILE=default
# PROMPT_ROOT=agents
# PROMPT_USER_ROLE=user
# SYSTEM_PROMPT=  # Inline override

# Source Agents (automatic knowledge base updates)
SOURCE_AGENTS_ENABLED=false
# SOURCE_AGENTS_S3_BUCKET=my-kb-bucket
# SOURCE_AGENTS_S3_REGION=us-east-1
# SOURCE_AGENTS_DATA_SOURCE_ID=your-data-source-id
# SOURCE_AGENTS_RUN_ON_STARTUP=false
# SOURCE_AGENTS_INTERVAL=3600  # seconds
```

### Configuration Table

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_MODE` | Yes | `agentcore` | Backend selection: `ollama`, `agentcore`, or `nova` |
| `AWS_REGION` | Yes (Nova/AgentCore) | `us-east-1` | AWS region for Bedrock |
| `NOVA_MODEL_ID` | No | `amazon.nova-pro-v1:0` | Bedrock Nova model identifier |
| `NOVA_TEMPERATURE` | No | `0.7` | Sampling temperature (0.0-1.0) |
| `NOVA_MAX_TOKENS` | No | `4096` | Maximum tokens to generate |
| `NOVA_TOP_P` | No | `0.9` | Nucleus sampling parameter |

---

## Code Changes

### Files to Create

1. **`src/community_bot/nova_model.py`** (NEW)
   - Nova-Pro model implementation
   - Streaming response handling
   - Error handling and retries

2. **`src/community_bot/nova_agent.py`** (NEW)
   - Nova agent orchestration
   - Conversation memory management
   - Prompt bundle integration

3. **`test_nova.py`** (NEW)
   - Nova connectivity tests
   - Response quality tests
   - Performance benchmarks

4. **`docs/NOVA_SETUP.md`** (NEW)
   - Nova setup instructions
   - IAM configuration
   - Troubleshooting guide

### Files to Modify

1. **`src/community_bot/config.py`**
   - Add Nova settings to `Settings` dataclass
   - Update `load_settings()` validation
   - Add Nova-specific validation

2. **`src/community_bot/agent_client.py`**
   - Add Nova backend initialization
   - Add Nova chat handler
   - Update logging

3. **`.env.example`**
   - Add Nova configuration examples
   - Update documentation

4. **`README.md`**
   - Add Nova quick start section
   - Update backend comparison table

5. **`pyproject.toml`** (optional)
   - Consider version bumping
   - No new dependencies needed (boto3 already present)

### Estimated Lines of Code

- **New code**: ~600 lines
- **Modified code**: ~150 lines
- **Documentation**: ~400 lines
- **Tests**: ~300 lines

**Total effort**: ~1450 lines

---

## Testing Strategy

### Unit Tests

Create `tests/test_nova_model.py`:

```python
"""Unit tests for Nova model."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from community_bot.nova_model import NovaModel


@pytest.mark.asyncio
async def test_nova_model_initialization():
    """Test Nova model initializes correctly."""
    model = NovaModel(
        model_id="amazon.nova-pro-v1:0",
        region="us-east-1",
        temperature=0.7,
    )
    
    assert model.model_id == "amazon.nova-pro-v1:0"
    assert model.region == "us-east-1"
    assert model.temperature == 0.7


@pytest.mark.asyncio
async def test_nova_streaming_response():
    """Test streaming response handling."""
    model = NovaModel()
    
    # Mock boto3 client
    with patch.object(model, 'client') as mock_client:
        # Mock streaming response
        mock_stream = [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'contentBlockDelta': {
                            'delta': {'text': 'Hello '}
                        }
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'contentBlockDelta': {
                            'delta': {'text': 'World!'}
                        }
                    }).encode()
                }
            }
        ]
        
        mock_client.invoke_model_with_response_stream.return_value = {
            'body': iter(mock_stream)
        }
        
        # Test streaming
        messages = [{"role": "user", "content": "Test"}]
        response = ""
        async for chunk in model.generate_streaming(messages):
            response += chunk
        
        assert response == "Hello World!"
```

Create `tests/test_nova_agent.py`:

```python
"""Unit tests for Nova agent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from community_bot.nova_agent import NovaAgent, ConversationMemory
from community_bot.config import Settings
from community_bot.prompt_loader import PromptBundle


def test_conversation_memory():
    """Test conversation memory."""
    memory = ConversationMemory(max_messages=3)
    
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there")
    memory.add_message("user", "How are you?")
    memory.add_message("assistant", "I'm good")
    
    # Should keep only last 3 messages
    context = memory.get_context()
    assert len(context) == 3
    assert context[0]["content"] == "Hi there"


@pytest.mark.asyncio
async def test_nova_agent_chat():
    """Test Nova agent chat."""
    settings = Settings(
        discord_token="test",
        discord_channel_id=123,
        backend_mode="nova",
        aws_region="us-east-1",
        nova_model_id="amazon.nova-pro-v1:0",
        nova_temperature=0.7,
        nova_max_tokens=100,
        nova_top_p=0.9,
    )
    
    prompt_bundle = PromptBundle(
        profile="test",
        system="You are a helpful assistant",
        user=None,
        extras={}
    )
    
    with patch('community_bot.nova_agent.NovaModel') as MockModel:
        mock_model_instance = AsyncMock()
        mock_model_instance.generate_streaming.return_value = iter(["Test ", "response"])
        MockModel.return_value = mock_model_instance
        
        agent = NovaAgent(settings, prompt_bundle)
        
        response = ""
        async for chunk in agent.chat("Hello"):
            response += chunk
        
        # Verify response
        assert "response" in response.lower()
```

### Integration Tests

Create `test_nova_integration.py`:

```python
"""Integration tests for Nova backend."""

import asyncio
import os
from dotenv import load_dotenv

from community_bot.config import Settings, load_settings
from community_bot.agent_client import AgentClient
from community_bot.logging_config import setup_logging, get_logger


async def test_nova_integration():
    """Test complete Nova integration."""
    # Load settings
    settings = load_settings()
    
    # Override to use Nova
    settings.backend_mode = "nova"
    
    setup_logging(settings.log_level)
    logger = get_logger("test_nova_integration")
    
    logger.info("=" * 80)
    logger.info("Testing Nova Integration")
    logger.info("=" * 80)
    
    # Initialize agent client
    client = AgentClient(settings)
    
    # Test messages
    test_messages = [
        "Hello, can you introduce yourself?",
        "What is the capital of France?",
        "Tell me a short joke.",
    ]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\nTest {i}/{len(test_messages)}: {message}")
        logger.info("-" * 40)
        
        response = ""
        async for chunk in client.chat(message):
            response += chunk
            print(chunk, end="", flush=True)
        
        print()  # New line after response
        logger.info(f"Response length: {len(response)} characters")
        
        assert len(response) > 0, "Response should not be empty"
    
    logger.info("=" * 80)
    logger.info("✅ All Nova integration tests passed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_nova_integration())
```

### Performance Tests

Create `test_nova_performance.py`:

```python
"""Performance benchmarks for Nova."""

import asyncio
import time
from statistics import mean, stdev

from community_bot.config import load_settings
from community_bot.agent_client import AgentClient


async def benchmark_nova():
    """Benchmark Nova response times."""
    settings = load_settings()
    settings.backend_mode = "nova"
    
    client = AgentClient(settings)
    
    # Test queries
    queries = [
        "What is AI?",
        "Explain machine learning in one sentence.",
        "What is Python?",
    ]
    
    response_times = []
    
    for query in queries:
        start_time = time.time()
        
        response = ""
        async for chunk in client.chat(query):
            response += chunk
        
        elapsed = time.time() - start_time
        response_times.append(elapsed)
        
        print(f"Query: {query}")
        print(f"Response time: {elapsed:.2f}s")
        print(f"Response length: {len(response)} chars")
        print(f"Chars/sec: {len(response)/elapsed:.1f}")
        print("-" * 40)
    
    print("\nStatistics:")
    print(f"Mean response time: {mean(response_times):.2f}s")
    print(f"Std dev: {stdev(response_times):.2f}s")
    print(f"Min: {min(response_times):.2f}s")
    print(f"Max: {max(response_times):.2f}s")


if __name__ == "__main__":
    asyncio.run(benchmark_nova())
```

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] AWS Bedrock Nova-Pro access enabled
- [ ] IAM permissions configured
- [ ] Test script passes (`test_nova_connection.py`)
- [ ] Unit tests passing (`pytest tests/test_nova_*.py`)
- [ ] Integration tests passing (`test_nova_integration.py`)
- [ ] Performance benchmarks acceptable
- [ ] Documentation complete
- [ ] `.env` configuration ready

### Deployment Steps

#### Step 1: Backup Current System

```bash
# Create backup branch
git checkout -b backup-pre-nova
git push origin backup-pre-nova

# Document current configuration
cp .env .env.backup.$(date +%Y%m%d)
```

#### Step 2: Deploy Code Changes

```bash
# Merge Nova implementation
git checkout main
git merge nova-implementation

# Install dependencies
uv sync

# Run tests
uv run pytest tests/test_nova_*.py
```

#### Step 3: Configure Environment

```bash
# Update .env with Nova settings
cat >> .env << EOF
BACKEND_MODE=nova
AWS_REGION=us-east-1
NOVA_MODEL_ID=amazon.nova-pro-v1:0
NOVA_TEMPERATURE=0.7
NOVA_MAX_TOKENS=4096
NOVA_TOP_P=0.9
EOF
```

#### Step 4: Test Deployment

```bash
# Run integration test
uv run python test_nova_integration.py

# Run performance benchmark
uv run python test_nova_performance.py
```

#### Step 5: Start Bot

```bash
# Start with Nova backend
uv run community-bot
```

#### Step 6: Monitor

```bash
# Watch logs for errors
tail -f logs/community_bot.log

# Monitor Discord channel for responses
```

### Gradual Rollout Strategy

1. **Week 1**: Deploy to test Discord server
2. **Week 2**: Monitor performance and costs
3. **Week 3**: Deploy to production server (low-traffic hours)
4. **Week 4**: Full production rollout

---

## Rollback Strategy

### Rollback Triggers

Rollback if any of the following occur:
- Response error rate > 5%
- Average response time > 10 seconds
- AWS costs exceed budget
- Critical bugs in production

### Rollback Procedure

```bash
# Step 1: Switch back to Ollama/AgentCore
# Edit .env
BACKEND_MODE=ollama  # or agentcore

# Step 2: Restart bot
# Stop current process (Ctrl+C)
uv run community-bot

# Step 3: Verify functionality
# Test in Discord channel

# Step 4: Investigate issues
# Check logs
tail -100 logs/community_bot.log

# Check AWS CloudWatch (if applicable)
aws logs tail /aws/bedrock/nova --follow
```

### Emergency Rollback

```bash
# Immediately revert to last known good state
git checkout backup-pre-nova
uv sync
uv run community-bot
```

---

## Post-Migration Considerations

### Monitoring

#### Metrics to Track

1. **Performance Metrics**
   - Average response time
   - Time to first token (TTFT)
   - Tokens per second
   - End-to-end latency

2. **Quality Metrics**
   - Response relevance (user feedback)
   - Error rate
   - Timeout rate
   - Knowledge base hit rate

3. **Cost Metrics**
   - Input tokens per day
   - Output tokens per day
   - Total API calls
   - Daily/monthly costs

#### CloudWatch Dashboards

Create CloudWatch dashboard:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Bedrock", "InvocationLatency", {"stat": "Average"}],
          [".", "TokensGenerated", {"stat": "Sum"}],
          [".", "Invocations", {"stat": "Sum"}]
        ],
        "period": 300,
        "region": "us-east-1",
        "title": "Nova-Pro Metrics"
      }
    }
  ]
}
```

### Cost Optimization

#### Nova-Pro Pricing (as of Oct 2025)

- **Input tokens**: $0.80 per 1M tokens
- **Output tokens**: $3.20 per 1M tokens

#### Cost Estimation

For a Discord bot with moderate usage:
- 1000 messages/day
- Avg 200 input tokens/message
- Avg 500 output tokens/message

**Daily cost**:
```
Input:  1000 × 200 × $0.80/1M = $0.16
Output: 1000 × 500 × $3.20/1M = $1.60
Total:  $1.76/day = ~$53/month
```

#### Cost Reduction Strategies

1. **Implement caching** for common questions
2. **Set max_tokens limits** appropriately
3. **Use Nova-Lite** for simple queries (cheaper)
4. **Implement rate limiting** per user
5. **Monitor and alert** on cost spikes

### Feature Enhancements

#### Future Improvements

1. **Multi-model routing**
   - Route simple queries to Nova-Lite
   - Route complex queries to Nova-Pro
   - Route specialized queries to domain models

2. **Enhanced KB integration**
   - Automatic KB query detection
   - Multi-KB support
   - KB result caching

3. **Advanced memory management**
   - Persistent conversation storage
   - Summary-based compression
   - User-specific memory

4. **Tool integration**
   - Function calling with Nova
   - Custom tools (search, calculator, etc.)
   - Multi-step reasoning

5. **A/B Testing**
   - Compare Ollama vs Nova quality
   - Benchmark response times
   - User satisfaction surveys

---

## Success Criteria

### Definition of Done

The migration is complete when:

- ✅ Nova backend fully implemented and tested
- ✅ All existing features work with Nova
- ✅ Documentation complete and accurate
- ✅ Tests passing (unit + integration)
- ✅ Performance meets/exceeds Ollama
- ✅ Costs within acceptable range
- ✅ Monitoring and alerting in place
- ✅ Rollback procedure validated
- ✅ Team trained on new system

### Quality Gates

| Gate | Criteria | Status |
|------|----------|--------|
| Code Quality | All tests passing, no critical bugs | ⬜ Pending |
| Performance | Response time < 5s avg | ⬜ Pending |
| Reliability | Error rate < 1% | ⬜ Pending |
| Cost | Daily cost < $2 | ⬜ Pending |
| Documentation | All docs complete | ⬜ Pending |
| User Acceptance | Positive feedback from users | ⬜ Pending |

---

## Conclusion

This migration plan provides a comprehensive roadmap for transitioning from Ollama to AWS Bedrock Nova-Pro. The additive approach ensures backward compatibility while introducing a powerful new backend option.

**Key Benefits:**
- Managed infrastructure (no Ollama server maintenance)
- Better scalability and reliability
- Cost-effective for production workloads
- Native AWS integration
- Latest AI capabilities

**Next Steps:**
1. Review and approve this plan
2. Set up AWS Bedrock access
3. Begin Phase 1: Infrastructure Setup
4. Implement core Nova model class
5. Integration with agent client
6. Testing and validation
7. Production deployment

---

## Appendices

### Appendix A: Nova API Reference

#### Invoke Model Request

```json
{
  "messages": [
    {
      "role": "user",
      "content": [{"text": "Hello"}]
    }
  ],
  "system": [
    {"text": "You are a helpful assistant"}
  ],
  "inferenceConfig": {
    "temperature": 0.7,
    "maxTokens": 4096,
    "topP": 0.9
  }
}
```

#### Streaming Response

```python
response = client.invoke_model_with_response_stream(
    modelId='amazon.nova-pro-v1:0',
    body=json.dumps(request_body)
)

for event in response['body']:
    chunk = event.get('chunk')
    if chunk:
        data = json.loads(chunk.get('bytes').decode())
        # Process chunk
```

### Appendix B: Comparison Matrix

| Feature | Ollama | AgentCore | Nova |
|---------|--------|-----------|------|
| **Infrastructure** | Self-hosted | AWS Managed | AWS Managed |
| **Cost** | Hardware only | API calls + Agent | API calls only |
| **Latency** | Low (local) | Medium | Medium |
| **Scalability** | Limited | High | High |
| **Model updates** | Manual | Automatic | Automatic |
| **KB integration** | Custom | Built-in | Built-in |
| **Monitoring** | Custom | CloudWatch | CloudWatch |
| **Maintenance** | High | Low | Low |

### Appendix C: Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Nova Model Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/models-nova.html)
- [Bedrock API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/)
- [Knowledge Bases Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

**Document End**
