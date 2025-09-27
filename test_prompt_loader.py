from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from community_bot.config import Settings
from community_bot.prompt_loader import load_prompt_bundle


def _base_settings(prompt_root: Path, profile: str, system_override: str | None = None) -> Settings:
    return Settings(
        discord_token="token",
        discord_channel_id=123456789,
        backend_mode="ollama",
        ollama_model="test-model",
        ollama_base_url="http://localhost:11434",
        max_response_chars=1800,
        memory_max_messages=10,
        system_prompt=system_override,
        log_level="INFO",
        prompt_profile=profile,
        prompt_root=prompt_root,
        prompt_user_role="user",
    )


class PromptLoaderTests(unittest.TestCase):
    def test_load_prompt_bundle_happy_path(self) -> None:
        with TemporaryDirectory() as tmp:
            prompt_root = Path(tmp) / "agents"
            profile_dir = prompt_root / "support"
            profile_dir.mkdir(parents=True)

            (profile_dir / "support.system.md").write_text("system prompt", encoding="utf-8")
            (profile_dir / "support.user.md").write_text("user prompt", encoding="utf-8")
            (profile_dir / "support.tool.md").write_text("tool prompt", encoding="utf-8")

            settings = _base_settings(prompt_root, "support")
            bundle = load_prompt_bundle(settings)

            self.assertEqual(bundle.profile, "support")
            self.assertEqual(bundle.system, "system prompt")
            self.assertEqual(bundle.user, "user prompt")
            self.assertEqual(bundle.extras, {"tool": "tool prompt"})

    def test_load_prompt_bundle_missing_user(self) -> None:
        with TemporaryDirectory() as tmp:
            prompt_root = Path(tmp) / "agents"
            profile_dir = prompt_root / "default"
            profile_dir.mkdir(parents=True)

            (profile_dir / "default.system.md").write_text("only system", encoding="utf-8")

            settings = _base_settings(prompt_root, "default")
            bundle = load_prompt_bundle(settings)

            self.assertIsNone(bundle.user)
            self.assertEqual(bundle.system, "only system")

    def test_load_prompt_bundle_missing_system_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            prompt_root = Path(tmp) / "agents"
            profile_dir = prompt_root / "broken"
            profile_dir.mkdir(parents=True)

            settings = _base_settings(prompt_root, "broken")

            with self.assertRaises(FileNotFoundError):
                load_prompt_bundle(settings)

    def test_load_prompt_bundle_override_precedence(self) -> None:
        with TemporaryDirectory() as tmp:
            prompt_root = Path(tmp) / "agents"
            profile_dir = prompt_root / "override"
            profile_dir.mkdir(parents=True)

            (profile_dir / "override.system.md").write_text("file system", encoding="utf-8")

            settings = _base_settings(prompt_root, "override", system_override="env system")
            bundle = load_prompt_bundle(settings)

            self.assertEqual(bundle.system, "env system")

    def test_load_prompt_bundle_refresh_reloads_disk(self) -> None:
        with TemporaryDirectory() as tmp:
            prompt_root = Path(tmp) / "agents"
            profile_dir = prompt_root / "cached"
            profile_dir.mkdir(parents=True)

            system_path = profile_dir / "cached.system.md"
            system_path.write_text("first", encoding="utf-8")

            settings = _base_settings(prompt_root, "cached")

            first = load_prompt_bundle(settings)
            self.assertEqual(first.system, "first")

            system_path.write_text("second", encoding="utf-8")

            # Without refresh we still see the cached value
            second = load_prompt_bundle(settings)
            self.assertEqual(second.system, "first")

            # With refresh we pick up new disk contents
            refreshed = load_prompt_bundle(settings, refresh=True)
            self.assertEqual(refreshed.system, "second")


if __name__ == "__main__":
    unittest.main()