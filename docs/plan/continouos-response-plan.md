# Continuous Response Plan

## Summary
We need to extend `CommunityBot` so it can deliver long agent responses that exceed Discord's message length tolerance (`settings.max_response_chars`). Instead of truncating, the bot should split the response into logical chunks, respect newline boundaries when possible, and keep code blocks intact across chunks while signaling continuity.

## Functional Requirements
- When the formatted response exceeds `settings.max_response_chars`, split it into multiple Discord messages.
- Prefer splitting on the last newline that keeps a chunk within the limit; if none exist, hard-wrap at the limit.
- Every chunk after the first must start with `"</ continuing>\n"`.
- Handle fenced code blocks (` ``` `). If a chunk ends inside a code block, close the fence in that chunk and reopen it at the beginning of the next.
- Preserve current threading behavior (respond in existing thread or newly created thread) and the existing "Processing..." placeholder message flow.

## Proposed Implementation
- Refactor `_truncate` into a new helper (e.g., `_split_response`) that yields chunks adhering to the rules above; keep `_truncate` as a compatibility shell calling the new helper for single-chunk cases.
- Update `on_message` to replace `thinking_msg.edit` with:
  - Edit the placeholder to the first chunk.
  - Send follow-up messages for the remaining chunks in the same channel/thread, ensuring order is preserved.
- Implement code-block-aware splitting:
  - Track open code blocks while scanning for split points.
  - When splitting inside a code block, terminate the current chunk with ```` ``` ```` before appending `</ continuing>` and reopen the block in the next chunk.
- Add structured logging to trace chunk counts, sizes, and code-block state transitions for easier debugging.

## Testing Strategy
- Unit-test the new splitting helper with cases:
  - Single chunk (no split).
  - Multi-chunk with newline-friendly boundaries.
  - Hard wrap when no newline exists.
  - Responses containing fenced code blocks that span chunks.
  - Max length edge cases (exact limit, limit minus one, limit plus one).
- Extend an integration test (e.g., `test_logging.py` or create a new one) to verify Discord message sending logic is invoked per chunk using mocks.

## Deployment Considerations
- No configuration changes required; relies on existing `max_response_chars` setting.
- Backwards-compatible with current behavior for short responses.
- Document the new behavior in `docs/agentcore-use.md` after implementation (future follow-up).
