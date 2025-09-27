# Agents Prompt Management Plan

## Context
- The `LocalAgent` currently seeds the conversation memory with an inline string defaulting to a hard-coded system prompt.
- `Settings.system_prompt` allows overriding this prompt, but it requires embedding long Markdown in environment variables, which is hard to author, version, or reuse.
- There is no notion of a reusable "agent profile" that bundles a system prompt with a companion user prompt or other structured assets.
- Goal: externalize prompts into versioned Markdown files under an agent-specific directory so that prompts can be managed, reviewed, and iterated safely.

## Goals
- Allow selecting an agent profile that maps to a folder under `agents/<agent-name>/`.
- Load the system prompt from `<agent-name>.system.md` and an optional user priming prompt from `<agent-name>.user.md`.
- Preserve backwards compatibility with existing environment variable based prompt overrides.
- Provide a clean integration point so both the LocalAgent and (eventually) AgentCore paths can use the same prompt loader.
- Keep prompt consumption flexible (e.g., allow future addition of tool, developer, or safety prompts).

## Non-Goals
- Changing the runtime storage for conversation history.
- Shipping the prompt files for existing AgentCore hosted agents (still controlled externally).
- Building a hot-reload layer for prompts.

## Terminology
- **Agent profile**: The logical name identifying the prompt set (directory name).
- **System prompt**: Markdown file seeded as the `system` role message when initializing the conversation.
- **User primer**: Optional Markdown guidance inserted as the first `user` role message before the live user input.

## Proposed Directory Layout
```
project-root/
  agents/
    default/
      default.system.md
      default.user.md  # optional; omit if not needed
    community-support/
      community-support.system.md
      community-support.user.md
```
- Folder name == agent profile.
- File names follow `<profile>.system.md` / `<profile>.user.md` to keep local conventions obvious.
- Additional files (`*.tool.md`, `*.safety.md`) can be ignored for now but the loader should be written to discover them.

## Configuration & Settings Updates
1. Introduce new settings entries:
   - `prompt_profile` (env: `PROMPT_PROFILE`, default: `default`).
   - `prompt_root` (env: `PROMPT_ROOT`, default: `<repo>/agents`). Resolve to absolute at runtime.
   - `prompt_user_role` (optional, default: `user`) in case we need to treat primers as `system` or `user` roles.
2. `Settings` dataclass gains corresponding fields. Ensure `load_settings()` resolves relative paths via `Path.cwd()`.
3. Maintain `SYSTEM_PROMPT` env variable override. When set, it supersedes file-based system prompt but still allows user primer from disk.

## Prompt Loader Component
Create `src/community_bot/prompt_loader.py`:
- Data model:
  ```python
  @dataclass
  class PromptBundle:
      profile: str
      system: str
      user: str | None = None
      extras: dict[str, str] = field(default_factory=dict)
  ```
- `load_prompt_bundle(settings: Settings) -> PromptBundle` steps:
  1. Resolve `settings.prompt_root / settings.prompt_profile`.
  2. Read `<profile>.system.md` (required). If missing, raise `FileNotFoundError` with friendly message.
  3. Attempt to read `<profile>.user.md`; store `None` when absent.
  4. Optionally glob for other `*.md` files and place them in `extras` keyed by suffix (e.g., `tool`, `safety`).
  5. If `settings.system_prompt` is set, override `bundle.system` with that text.
  6. Cache results per profile using `functools.lru_cache` to avoid repetitive disk reads per request.
- Provide helper `load_system_prompt(settings)` and `load_user_primer(settings)` wrappers for callers needing just a string.

## LocalAgent Integration
- At agent construction time, call `load_prompt_bundle(settings)` and seed memory accordingly:
  1. Add `bundle.system` as the initial `system` role message (matching current behavior).
  2. If `bundle.user` exists, add it as a synthetic `user` message **before** appending the real user input.
- Update `LocalAgent.clear_memory()` to use the loader again so the latest file changes apply post-clear.
- Consider extending `LocalAgent.chat()` to ensure the primer doesnt push out real messages when `memory_max_messages` is low (e.g., reserve slots or document recommendation to keep limit >= 3).

## AgentClient & Backend Considerations
- `AgentClient` already logs the selected backend; extend initialization when `backend_mode == "ollama"`:
  - After loading prompts, log the profile name and whether a user primer was detected.
  - Provide method `get_prompt_profile()` for debugging / health checks.
- For `backend_mode == "agentcore"`, no immediate change, but the prompt loader can still supply prompts if we later bridge them into AgentCore request payloads.

## Error Handling & Diagnostics
- Fail fast with a clear error if the system prompt file is missing.
- When the user primer is missing, log at DEBUG and continue.
- Include file paths in logs so operators can detect misconfiguration quickly.
- Add unit tests covering missing profile directory, missing system file, and override precedence.

## Testing Plan
- New tests under `tests/test_prompt_loader.py`:
  - Happy path: create temp profile with both files, assert loader contents.
  - Missing user primer: ensure `bundle.user` is `None`.
  - Missing system prompt: expect `FileNotFoundError`.
  - Override via `settings.system_prompt`.
  - Cache behavior: loader called twice returns same object without rereading (can patch `Path.read_text`).
- Extend `test_agent_client_async.py` or create new tests to confirm primer injection at chat start.

## Migration Strategy
1. Introduce default profile files (`agents/default/default.system.md` + optional `.user.md`) matching the current hard-coded prompt.
2. Update documentation (`docs/agentcore-use.md`, `examples/README.md`) to explain the new folder structure.
3. Encourage storing prompts in source control and PR reviews.
4. Provide sample PowerShell and POSIX commands to create new profiles.
5. Ensure `README` references `PROMPT_PROFILE` env variable when instructing users to run the bot locally.

## Future Enhancements
- Support prompt templating tokens (e.g., `{channel_name}`) with runtime substitution.
- Permit per-channel overrides selecting different profiles dynamically.
- Watch filesystem for prompt changes and auto-refresh without restart.
- Surface prompt metadata (version, author, last-updated) in health endpoints.
