# Mike et al Community Bot

Discord community bot that can answer questions using either:

1. **AWS AgentCore (Strands agent with RAG / Knowledge Base)**
2. **Local Ollama model** for quick local experimentation

The bot watches a single configured Discord channel and replies to each user message with the selected backend's response.

## Features

- Dual backend: `AgentCore` (production) or `Ollama` (local dev)
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
```

Run:
```bash
uv sync
uv run community-bot
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DISCORD_BOT_TOKEN | Always | Discord bot token from Developer Portal |
| DISCORD_CHANNEL_ID | Always | Channel ID to monitor (numeric) |
| BACKEND_MODE | Always | agentcore or ollama |
| AWS_REGION | AgentCore | AWS region (e.g., us-east-1) |
| AGENT_ID | AgentCore | Bedrock Agent ID |
| AGENT_ALIAS_ID | AgentCore | Bedrock Agent Alias ID |
| OLLAMA_MODEL | Ollama | Local model name (e.g., llama3.1) |
| OLLAMA_BASE_URL | Ollama optional | Defaults http://localhost:11434 |
| LOG_LEVEL | Optional | Default INFO |
| MAX_RESPONSE_CHARS | Optional | Max chunk size (<1900) default 1800 |
| SYSTEM_PROMPT | Optional | Inline system prompt override (bypasses file) |
| PROMPT_PROFILE | Optional | Prompt folder to load (default `default`) |
| PROMPT_ROOT | Optional | Directory containing prompt profiles (default `<repo>/agents`) |
| PROMPT_USER_ROLE | Optional | Role used for primer message (default `user`) |
| MESSAGE_PREFIX | Optional | Prepended to every reply |

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

## Troubleshooting

| Problem | Suggestion |
|---------|------------|
| No response | Check agent alias deployment / permissions |
| AccessDenied | Ensure IAM allows bedrock:InvokeAgent |
| Ollama 404 | Update Ollama; verify /api/chat endpoint |
| Bot silent | Confirm channel ID numeric & correct |

## License

See LICENSE.
