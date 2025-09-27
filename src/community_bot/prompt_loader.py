from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .config import Settings
from .logging_config import get_logger

logger = get_logger("community_bot.agents")


@dataclass(slots=True)
class PromptBundle:
    profile: str
    system: str
    user: Optional[str] = None
    extras: dict[str, str] = field(default_factory=dict)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"Failed reading prompt file: {path}") from exc


def _load_prompt_bundle_from_disk(prompt_root: Path, profile: str) -> PromptBundle:
    profile_dir = prompt_root / profile
    if not profile_dir.exists():
        raise FileNotFoundError(
            f"Prompt profile directory not found for '{profile}': {profile_dir}"
        )

    system_path = profile_dir / f"{profile}.system.md"
    if not system_path.exists():
        raise FileNotFoundError(
            f"Missing system prompt file for profile '{profile}': {system_path}"
        )

    system_prompt = _read_text(system_path)
    logger.debug("Loaded system prompt for profile '%s' from %s", profile, system_path)

    user_path = profile_dir / f"{profile}.user.md"
    user_prompt: Optional[str] = None
    if user_path.exists():
        user_prompt = _read_text(user_path)
        logger.debug("Loaded user primer for profile '%s' from %s", profile, user_path)
    else:
        logger.debug(
            "No user primer found for profile '%s'; expected optional file %s",
            profile,
            user_path,
        )

    extras: dict[str, str] = {}
    for extra_path in profile_dir.glob(f"{profile}.*.md"):
        if extra_path in {system_path, user_path}:
            continue

        stem = extra_path.stem
        suffix_start = len(profile) + 1
        if not stem.startswith(f"{profile}.") or suffix_start >= len(stem):
            continue

        suffix = stem[suffix_start:]
        if suffix in {"system", "user"}:
            continue

        extras[suffix] = _read_text(extra_path)
        logger.debug(
            "Loaded extra prompt '%s' for profile '%s' from %s",
            suffix,
            profile,
            extra_path,
        )

    return PromptBundle(profile=profile, system=system_prompt, user=user_prompt, extras=extras)


@lru_cache(maxsize=16)
def _load_prompt_bundle_cached(prompt_root: str, profile: str) -> PromptBundle:
    prompt_root_path = Path(prompt_root)
    return _load_prompt_bundle_from_disk(prompt_root_path, profile)


def load_prompt_bundle(settings: Settings, *, refresh: bool = False) -> PromptBundle:
    prompt_root = settings.prompt_root
    profile = settings.prompt_profile

    if refresh:
        _load_prompt_bundle_cached.cache_clear()

    bundle = _load_prompt_bundle_cached(str(prompt_root), profile)

    if settings.system_prompt:
        logger.debug(
            "Applying system prompt override from settings for profile '%s'", profile
        )
        bundle = replace(bundle, system=settings.system_prompt)

    return bundle


def load_system_prompt(settings: Settings, *, refresh: bool = False) -> str:
    bundle = load_prompt_bundle(settings, refresh=refresh)
    return bundle.system


def load_user_primer(settings: Settings, *, refresh: bool = False) -> Optional[str]:
    bundle = load_prompt_bundle(settings, refresh=refresh)
    return bundle.user
