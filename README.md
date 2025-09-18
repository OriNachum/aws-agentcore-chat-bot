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
| MAX_REPLY_CHARS | Optional | Max chunk size (<1900) default 1800 |
| MESSAGE_PREFIX | Optional | Prepended to every reply |

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
