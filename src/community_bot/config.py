from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    discord_token: str
    discord_channel_id: int
    backend_mode: str  # 'agentcore', 'ollama', or 'nova'
    # AWS/AgentCore settings (for backward compatibility)
    aws_region: Optional[str] = None
    agent_id: Optional[str] = None  # AgentCore Agent / Knowledge Base identifier
    agent_alias_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    # Ollama settings (enhanced for LocalAgent framework)
    ollama_model: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    # Nova settings
    nova_model_id: str = "us.amazon.nova-pro-v1:0"
    nova_temperature: float = 0.7
    nova_max_tokens: int = 4096
    nova_top_p: float = 0.9
    # Response settings
    max_response_chars: int = 1800
    # LocalAgent framework settings
    memory_max_messages: int = 50  # Maximum messages to keep in memory
    system_prompt: Optional[str] = None  # Custom system prompt override
    # Logging settings
    log_level: str = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    # Prompt management settings
    prompt_profile: str = "default"
    prompt_root: Path = Path.cwd() / "agents"
    prompt_user_role: str = "user"
    # Source Agents settings
    source_agents_enabled: bool = False
    source_agents_s3_bucket: Optional[str] = None
    source_agents_s3_region: str = "us-east-1"
    source_agents_data_source_id: Optional[str] = None
    source_agents_run_on_startup: bool = False
    source_agents_interval: int = 3600  # seconds


REQUIRED_BASE = ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID", "BACKEND_MODE"]


def load_settings() -> Settings:
    load_dotenv()

    missing = [k for k in REQUIRED_BASE if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    backend_mode = os.getenv("BACKEND_MODE", "agentcore").lower()
    if backend_mode not in {"agentcore", "ollama", "nova"}:
        raise RuntimeError("BACKEND_MODE must be 'agentcore', 'ollama', or 'nova'")

    if backend_mode == "agentcore":
        # Minimal required for AgentCore path
        if not os.getenv("AWS_REGION"):
            raise RuntimeError("AWS_REGION is required for AgentCore backend")
        if not os.getenv("AGENT_ID") or not os.getenv("AGENT_ALIAS_ID"):
            # Some flows might use knowledge base only; still require IDs now.
            raise RuntimeError("AGENT_ID and AGENT_ALIAS_ID are required for AgentCore backend")

    if backend_mode == "ollama":
        if not os.getenv("OLLAMA_MODEL"):
            raise RuntimeError("OLLAMA_MODEL is required for Ollama backend")
    
    # Nova validation
    if backend_mode == "nova":
        if not os.getenv("AWS_REGION"):
            raise RuntimeError("AWS_REGION is required for Nova backend")

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
        nova_model_id=os.getenv("NOVA_MODEL_ID", "us.amazon.nova-pro-v1:0"),
        nova_temperature=float(os.getenv("NOVA_TEMPERATURE", "0.7")),
        nova_max_tokens=int(os.getenv("NOVA_MAX_TOKENS", "4096")),
        nova_top_p=float(os.getenv("NOVA_TOP_P", "0.9")),
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
