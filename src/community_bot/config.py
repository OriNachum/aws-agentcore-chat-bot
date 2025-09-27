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
    backend_mode: str  # 'agentcore' or 'ollama'
    # AWS/AgentCore settings (for backward compatibility)
    aws_region: Optional[str] = None
    agent_id: Optional[str] = None  # AgentCore Agent / Knowledge Base identifier
    agent_alias_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    # Ollama settings (enhanced for LocalAgent framework)
    ollama_model: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
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


REQUIRED_BASE = ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID", "BACKEND_MODE"]


def load_settings() -> Settings:
    load_dotenv()

    missing = [k for k in REQUIRED_BASE if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    backend_mode = os.getenv("BACKEND_MODE", "agentcore").lower()
    if backend_mode not in {"agentcore", "ollama"}:
        raise RuntimeError("BACKEND_MODE must be 'agentcore' or 'ollama'")

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
        max_response_chars=int(os.getenv("MAX_RESPONSE_CHARS", "1800")),
        memory_max_messages=int(os.getenv("MEMORY_MAX_MESSAGES", "50")),
        system_prompt=os.getenv("SYSTEM_PROMPT"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        prompt_profile=prompt_profile,
        prompt_root=prompt_root,
        prompt_user_role=prompt_user_role,
    )
