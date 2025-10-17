# AI-Generated Thread Names Feature

## Overview

The Discord bot now uses the configured AI agent to generate intelligent, context-aware thread names when creating new conversation threads. This provides more descriptive and meaningful thread titles compared to the previous generic naming scheme.

## How It Works

### Previous Behavior
- Thread names were generic: `"Chat with {username}"` or `"Re: {first 50 chars}..."`
- No semantic understanding of the conversation content

### New Behavior
- When a new thread is created (user messages in the main channel), the bot:
  1. Sends the user's message to the AI agent with a specialized prompt
  2. The agent generates a concise, descriptive title (max 100 characters)
  3. The generated title is used as the thread name
  4. Falls back to the old naming scheme if the AI generation fails

## Implementation Details

### Key Components

#### `_generate_thread_name()` Method
Located in `src/community_bot/discord_bot.py`

```python
async def _generate_thread_name(self, user_message: str, author_name: str) -> str:
    """Generate a thread name using the agent for inference."""
```

**Features:**
- Sends a carefully crafted prompt to the agent
- Handles streaming responses (chunks)
- Cleans up the response (removes quotes, takes first line only)
- Enforces Discord's 100-character limit
- Provides robust fallback on errors

**Error Handling:**
- Empty responses → Falls back to `"Chat with {username}"`
- Exceptions → Falls back to `"Chat with {username}"`
- Too long → Truncates to 97 chars + "..."
- Multiline responses → Takes only first line

### Integration Point

The thread name generation is called in `on_message()` when creating a new thread:

```python
# Generate thread name using the agent
thread_name = await self._generate_thread_name(
    message.content, 
    message.author.display_name
)

response_channel = await message.create_thread(name=thread_name)
```

## Testing

Comprehensive test suite in `test_thread_name_generation.py`:

- ✅ Basic thread name generation
- ✅ Quote stripping from responses
- ✅ Truncation of long names (>100 chars)
- ✅ Empty response handling (fallback)
- ✅ Exception handling (fallback)
- ✅ Multiline response cleanup
- ✅ Chunked response assembly

Run tests:
```bash
uv run python test_thread_name_generation.py
```

## Configuration

No additional configuration required. The feature:
- Works with both `ollama` and `agentcore` backends
- Uses the same agent configured for regular chat responses
- Respects existing prompt profiles and settings

## Performance Considerations

**Latency:**
- Adds one additional AI inference call per new thread
- Typically adds 1-3 seconds to thread creation time
- Does not affect messages in existing threads

**Cost:**
- One additional API call per new thread (not per message)
- Prompt is small (~150 tokens)
- Responses are constrained to be brief

## Examples

### Example 1: Technical Question
**User Message:**
```
Can you explain how gradient descent works in neural networks?
```

**Generated Thread Name:**
```
Gradient Descent in Neural Networks
```

### Example 2: General Discussion
**User Message:**
```
I'm having trouble with my Python code that's supposed to parse JSON files
```

**Generated Thread Name:**
```
Python JSON Parsing Issue
```

### Example 3: Fallback Scenario
**User Message:**
```
Hello!
```

**Agent Response:** (empty or error)

**Generated Thread Name:**
```
Chat with John
```
(Falls back to username)

## Future Enhancements

Potential improvements for future versions:

1. **Caching**: Cache thread names for similar messages
2. **Customization**: Allow users to customize thread naming via config
3. **Language Detection**: Generate names in the same language as the message
4. **Emoji Support**: Add relevant emojis to thread names
5. **Category Prefixes**: Auto-add category prefixes (e.g., "Bug:", "Question:")

## Troubleshooting

### Thread names are still generic
- Check logs for errors in `_generate_thread_name()`
- Verify agent is responding correctly to regular messages
- Ensure no network/API issues

### Thread creation is slow
- This is expected - AI inference adds 1-3 seconds
- Consider whether all threads need AI-generated names
- Could add a config option to disable the feature

### Thread names are truncated oddly
- Discord enforces a 100-character limit
- Names longer than 100 chars get truncated with "..."
- Agent should generate shorter names, but fallback handles long ones

## Logging

The feature provides detailed logging:

```python
logger.debug(f"Requesting thread name from agent for message: {user_message[:100]}...")
logger.info(f"Generated thread name: {thread_name}")
logger.warning("Agent returned empty thread name, using fallback")
logger.error(f"Failed to generate thread name with agent: {e}")
```

Log level can be controlled via `LOG_LEVEL` environment variable.

## Related Files

- **Implementation**: `src/community_bot/discord_bot.py`
- **Tests**: `test_thread_name_generation.py`
- **Documentation**: `docs/AI_GENERATED_THREAD_NAMES.md` (this file)
