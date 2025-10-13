# Mike et al Community Bot

Discord community bot that can answer questions using either:

1. **AWS AgentCore (Strands agent with RAG / Knowledge Base)**
2. **Local Ollama model** for quick local experimentation

The bot watches a single configured Discord channel and replies to each user message with the selected backend's response.

## Features

- Dual backend: `AgentCore` (production) or `Ollama` (local dev)
- **Source Agents**: Automatically collect and update knowledge base from multiple sources
- Simple environment-based configuration
- Safe channel filtering (hard-coded channel ID)
- Automatic long message splitting to respect Discord 2000 char limit
- Lightweight abstraction layer for future tools (streaming, etc.)

## Quick Start (Ollama Local Mode)

1. Install uv (if not already):
	```bash
	curl -LsSf https://astral.sh/uv/install.sh | sh
	```
2. Copy and edit environment file:
	```bash
	cp .env.example .env
	```
	Set:
	```env
	BACKEND_MODE=ollama
	DISCORD_BOT_TOKEN=your_discord_bot_token
	DISCORD_CHANNEL_ID=123456789012345678
	OLLAMA_MODEL=llama3.1
	```
3. Ensure Ollama is running and model is pulled:
	```bash
	ollama pull llama3.1
	```
4. Install deps & run:
	```bash
	uv sync
	uv run community-bot
	```

## AgentCore Mode (AWS Bedrock)

Prerequisites:
- AWS account with Bedrock + AgentCore access in region you plan to use
- Created Bedrock Agent with an Alias (and optionally Knowledge Base for RAG)
- IAM credentials available locally (e.g., via `aws configure`, SSO, or environment vars)

Configure `.env`:
```env
BACKEND_MODE=agentcore
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=123456789012345678
AWS_REGION=us-east-1
AGENT_ID=your_agent_id
AGENT_ALIAS_ID=your_agent_alias_id

# Optional: AWS Bedrock Knowledge Base
KNOWLEDGE_BASE_ID=your_kb_id
KB_DIRECT_ENDPOINT=https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/YOUR_KB_ID/retrieve-and-generate
```

Run:
```bash
uv sync
uv run community-bot
```

### AWS Bedrock Knowledge Base Integration

The bot supports querying AWS Bedrock Knowledge Bases for RAG (Retrieval Augmented Generation). When configured, the agent can automatically search your knowledge base to find relevant information.

**Setup**:
1. Create a Knowledge Base in AWS Bedrock console
2. Upload documents to S3 and sync with your KB
3. Add the KB configuration to your `.env` file (see above)
4. Ensure your IAM user/role has `bedrock:Retrieve` permission

**Testing**:
```powershell
# Quick test of KB integration
uv run python test_kb_bedrock.py

# Full bot test
uv run community-bot
```

**Documentation**:
- 📚 **[Complete KB Setup Guide](docs/BEDROCK_KB_SETUP.md)** - Step-by-step setup
- 📐 **[Architecture Overview](docs/KB_ARCHITECTURE.md)** - How it works
- 📋 **[Quick Reference](docs/KB_QUICK_REFERENCE.md)** - Cheat sheet
- 🐛 **[Troubleshooting](docs/BEDROCK_KB_SETUP.md#troubleshooting)** - Common issues

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DISCORD_BOT_TOKEN | Always | Discord bot token from Developer Portal |
| DISCORD_CHANNEL_ID | Always | Channel ID to monitor (numeric) |
| BACKEND_MODE | Always | agentcore or ollama |
| AWS_REGION | AgentCore | AWS region (e.g., us-east-1) |
| AGENT_ID | AgentCore | Bedrock Agent ID |
| AGENT_ALIAS_ID | AgentCore | Bedrock Agent Alias ID |
| KNOWLEDGE_BASE_ID | Optional | Bedrock Knowledge Base ID for RAG |
| KB_DIRECT_ENDPOINT | Optional | Bedrock KB endpoint URL (for RAG queries) |
| OLLAMA_MODEL | Ollama | Local model name (e.g., llama3.1) |
| OLLAMA_BASE_URL | Ollama optional | Defaults http://localhost:11434 |
| LOG_LEVEL | Optional | Default INFO |
| MAX_RESPONSE_CHARS | Optional | Max chunk size (<1900) default 1800 |
| SYSTEM_PROMPT | Optional | Inline system prompt override (bypasses file) |
| PROMPT_PROFILE | Optional | Prompt folder to load (default `default`) |
| PROMPT_ROOT | Optional | Directory containing prompt profiles (default `<repo>/agents`) |
| PROMPT_USER_ROLE | Optional | Role used for primer message (default `user`) |
| MESSAGE_PREFIX | Optional | Prepended to every reply |
| SOURCE_AGENTS_ENABLED | Optional | Enable automatic KB updates (default `false`) |
| SOURCE_AGENTS_S3_BUCKET | Source Agents | S3 bucket for KB documents |
| SOURCE_AGENTS_S3_REGION | Source Agents | AWS region for S3 (default `us-east-1`) |
| SOURCE_AGENTS_DATA_SOURCE_ID | Optional | Bedrock KB data source ID for sync |
| SOURCE_AGENTS_RUN_ON_STARTUP | Optional | Run agents on bot startup (default `false`) |
| SOURCE_AGENTS_INTERVAL | Optional | Collection interval in seconds (default `3600`) |

## Prompt Profiles

Prompts now live on disk under the `agents/` directory and are grouped by **profile**. Each profile folder contains at least a `<profile>.system.md` file and can optionally include `<profile>.user.md` (primer) plus other structured prompts (`<profile>.tool.md`, `<profile>.safety.md`, etc.). The bot selects a profile via the `PROMPT_PROFILE` environment variable (default: `default`).

- System prompt precedence: `SYSTEM_PROMPT` env var → `<profile>.system.md`
- Optional primer: `<profile>.user.md` is injected before the live user message using role `PROMPT_USER_ROLE`
- Additional prompt files are exposed via the loader for future tooling integrations

### Creating a profile directory

```pwsh
$profile = "community-support"
$root = Join-Path (Get-Location) "agents"
New-Item -ItemType Directory -Path (Join-Path $root $profile) -Force | Out-Null
Set-Content -Path (Join-Path $root $profile "$profile.system.md") -Value "You are a helpful assistant for our community."
Set-Content -Path (Join-Path $root $profile "$profile.user.md") -Value "Please ask follow-up questions before answering if details are missing."
```

```bash
profile=community-support
root="agents"
mkdir -p "$root/$profile"
cat <<'EOF' > "$root/$profile/$profile.system.md"
You are a helpful assistant for our community.
EOF
cat <<'EOF' > "$root/$profile/$profile.user.md"
Please ask follow-up questions before answering if details are missing.
EOF
```

When running locally, ensure your `.env` (or shell) includes:

```
PROMPT_PROFILE=community-support
```

## RAG Knowledge Base (High Level)

1. Create S3 bucket for documents.
2. Create Knowledge Base in Bedrock referencing bucket.
3. Attach KB to AgentCore agent (tool permission) and deploy alias.
4. Upload docs, sync KB, then ask questions referencing content.

## Source Agents (Automatic KB Updates)

Source Agents are background processes that continuously collect data from various sources and upload it to S3 to keep your knowledge base up-to-date.

**Quick Start:**

1. Enable in `.env`:
   ```env
   SOURCE_AGENTS_ENABLED=true
   SOURCE_AGENTS_S3_BUCKET=my-kb-bucket
   SOURCE_AGENTS_DATA_SOURCE_ID=your-data-source-id
   ```

2. Configure agents in `agents/sources/config.yaml`:
   ```yaml
   agents:
     - id: "my_collector"
       type: "script"
       enabled: true
       schedule: "0 */1 * * *"  # Hourly
       config:
         script_path: "./agents/sources/scripts/my_collector.py"
         category: "my_data"
   ```

3. Run integrated with bot or standalone:
   ```bash
   # With Discord bot
   uv run community-bot
   
   # Standalone
   python scripts/run_source_agents.py --once
   ```

**Documentation:**
- 📚 **[Source Agents Quick Start](docs/SOURCE_AGENTS_QUICKSTART.md)** - Getting started
- 📐 **[Design Document](docs/plan/sub-agents.md)** - Architecture and detailed design
- 📁 **[Agent Directory](agents/sources/README.md)** - Configuration examples

**Supported Agent Types:**
- **Script**: Run custom Python scripts to collect data
- **Database**: Query PostgreSQL databases
- More types planned (Browser, MCP, API, etc.)

## Troubleshooting

| Problem | Suggestion |
|---------|------------|
| No response | Check agent alias deployment / permissions |
| AccessDenied | Ensure IAM allows bedrock:InvokeAgent |
| KB 403 Forbidden | Ensure IAM allows bedrock:Retrieve and AWS credentials configured |
| KB No results | Check KB has indexed documents; try broader queries |
| Ollama 404 | Update Ollama; verify /api/chat endpoint |
| Bot silent | Confirm channel ID numeric & correct |

For Knowledge Base issues, see **[KB Troubleshooting Guide](docs/BEDROCK_KB_SETUP.md#troubleshooting)**

## License

See LICENSE.
