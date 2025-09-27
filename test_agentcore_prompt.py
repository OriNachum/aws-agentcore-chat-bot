"""Unit tests ensuring AgentCore backend uses prompt bundle configuration."""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Prepare a dedicated prompt bundle on disk before importing the app module
_PROMPT_ROOT = Path(tempfile.mkdtemp(prefix="agentcore-prompts-"))
_PROFILE = "default"
_PROFILE_DIR = _PROMPT_ROOT / _PROFILE
_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

_SYSTEM_PROMPT = "You are a precise analyst for the community bot."
_USER_PRIMER = "Always greet users politely before answering questions."
_EXTRA_GUIDE = "Provide responses with clear bullet points when sharing procedures."
_EXTRA_FAQ = "If the question matches FAQ topics, reference the knowledge base succinctly."

(_PROFILE_DIR / f"{_PROFILE}.system.md").write_text(_SYSTEM_PROMPT, encoding="utf-8")
(_PROFILE_DIR / f"{_PROFILE}.user.md").write_text(_USER_PRIMER, encoding="utf-8")
(_PROFILE_DIR / f"{_PROFILE}.guidelines.md").write_text(_EXTRA_GUIDE, encoding="utf-8")
(_PROFILE_DIR / f"{_PROFILE}.faq.md").write_text(_EXTRA_FAQ, encoding="utf-8")

# Required environment for loading settings on module import
os.environ.setdefault("DISCORD_BOT_TOKEN", "unit-test-token")
os.environ.setdefault("DISCORD_CHANNEL_ID", "123456789")
os.environ.setdefault("BACKEND_MODE", "agentcore")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AGENT_ID", "agent-123")
os.environ.setdefault("AGENT_ALIAS_ID", "alias-456")
os.environ.setdefault("OLLAMA_MODEL", "llama3")
os.environ.setdefault("PROMPT_PROFILE", _PROFILE)
os.environ.setdefault("PROMPT_ROOT", str(_PROMPT_ROOT))
os.environ.setdefault("PROMPT_USER_ROLE", "analyst")
os.environ.setdefault("LOG_LEVEL", "INFO")

# Import after the prompt files and environment are ready
from community_bot import agentcore_app  # noqa: E402
from community_bot.agent_client import AgentClient  # noqa: E402
from community_bot.config import Settings  # noqa: E402

import importlib

# Reload module so that it picks up the temporary prompt root configured above.
agentcore_app = importlib.reload(agentcore_app)


class AgentCorePromptCompositionTests(unittest.TestCase):
    """Validate prompt composition for AgentCore backend."""

    def test_compose_prompt_includes_bundle_sections(self) -> None:
        memory_context = "User previously asked about deployment details."
        knowledge_context = "Knowledge Doc: Deployment steps are in README section 3."
        user_message = "How do I redeploy the bot after updating prompts?"

        prompt = agentcore_app._compose_agentcore_prompt(
            user_message=user_message,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )

        self.assertIn("[System Instructions]\n" + _SYSTEM_PROMPT, prompt)
        self.assertIn("[Analyst Primer]\n" + _USER_PRIMER, prompt)
        self.assertIn("[faq]\n" + _EXTRA_FAQ, prompt)
        self.assertIn("[guidelines]\n" + _EXTRA_GUIDE, prompt)
        self.assertIn("[Conversation Memory]\n" + memory_context, prompt)
        self.assertIn("[Relevant Knowledge]\n" + knowledge_context, prompt)
        self.assertIn("[Analyst Message]\n" + user_message, prompt)

        # Ensure memory and knowledge context appear only once
        self.assertEqual(prompt.count("[Conversation Memory]"), 1)
        self.assertEqual(prompt.count("[Relevant Knowledge]"), 1)

    def test_compose_prompt_omits_optional_sections_when_missing(self) -> None:
        user_message = "Summarize the onboarding flow."

        prompt = agentcore_app._compose_agentcore_prompt(
            user_message=user_message,
            memory_context=None,
            knowledge_context="",
        )

        self.assertIn("[System Instructions]\n" + _SYSTEM_PROMPT, prompt)
        self.assertIn("[Analyst Primer]\n" + _USER_PRIMER, prompt)
        self.assertIn("[Analyst Message]\n" + user_message, prompt)
        self.assertNotIn("[Conversation Memory]", prompt)
        self.assertNotIn("[Relevant Knowledge]", prompt)


class AgentCoreAgentClientTests(unittest.TestCase):
    """Ensure AgentClient loads prompt bundle when using AgentCore backend."""

    def test_agentcore_client_attaches_prompt_bundle(self) -> None:
        settings = Settings(
            discord_token="test-token",
            discord_channel_id=987654321,
            backend_mode="agentcore",
            aws_region="us-west-2",
            agent_id="agent-abc",
            agent_alias_id="alias-def",
            knowledge_base_id=None,
            ollama_model="llama3",
            ollama_base_url="http://localhost:11434",
            max_response_chars=1800,
            memory_max_messages=10,
            system_prompt=None,
            log_level="INFO",
            prompt_profile=_PROFILE,
            prompt_root=_PROMPT_ROOT,
            prompt_user_role="analyst",
        )

        client = AgentClient(settings)

        self.assertEqual(client.agent, "agentcore")
        bundle = client.prompt_bundle
        self.assertIsNotNone(bundle)
        assert bundle is not None  # Narrow type for static analyzers
        self.assertEqual(bundle.profile, _PROFILE)
        self.assertEqual(bundle.system.strip(), _SYSTEM_PROMPT)
        self.assertIsNotNone(bundle.user)
        assert bundle.user is not None
        self.assertEqual(bundle.user.strip(), _USER_PRIMER)
        self.assertSetEqual(set(bundle.extras.keys()), {"faq", "guidelines"})


def _cleanup() -> None:
    shutil.rmtree(_PROMPT_ROOT, ignore_errors=True)


atexit.register(_cleanup)


if __name__ == "__main__":
    unittest.main()
