# AI-Generated Thread Names - Quick Reference

## What Changed?

**Before**: Thread names were generic patterns
```
"Chat with Alice"
"Re: Can you explain Python decorat..."
```

**After**: Thread names are AI-generated based on content
```
"Python Decorators Explanation"
"Docker Deployment Troubleshooting"
"Machine Learning Fundamentals"
```

## How It Works

1. User posts message in monitored channel
2. Bot asks AI agent to generate a descriptive title
3. AI creates short, relevant thread name (max 100 chars)
4. Thread is created with the AI-generated name

## Key Features

✅ Context-aware names  
✅ Works with both Ollama and Bedrock  
✅ Automatic fallback on errors  
✅ Respects Discord's 100-char limit  
✅ No configuration needed  

## Performance

- **Timing**: +1-3 seconds for thread creation
- **Cost**: 1 additional API call per new thread
- **Impact**: Only affects new threads, not existing ones

## Testing

```bash
# Run unit tests
uv run python test_thread_name_generation.py

# Run demo (requires running agent)
uv run python demo_thread_names.py
```

## Examples

| User Message | Generated Thread Name |
|--------------|----------------------|
| "Can you explain transformers in ML?" | "Transformer Models in Machine Learning" |
| "I'm having Docker issues" | "Docker Troubleshooting" |
| "What's the difference between async and sync?" | "Async vs Sync Programming" |
| "Hello!" | "Chat with User" (fallback) |

## Troubleshooting

**Issue**: Thread names are generic  
**Solution**: Check logs for `_generate_thread_name()` errors

**Issue**: Slow thread creation  
**Expected**: AI inference adds 1-3 seconds

**Issue**: Names truncated oddly  
**Cause**: Discord's 100-char limit enforced

## Files

- Implementation: `src/community_bot/discord_bot.py`
- Tests: `test_thread_name_generation.py`
- Docs: `docs/AI_GENERATED_THREAD_NAMES.md`
- Summary: `THREAD_NAME_FEATURE_SUMMARY.md`

## Related Methods

```python
# Generate thread name
async def _generate_thread_name(
    user_message: str, 
    author_name: str
) -> str

# Used in on_message() when creating threads
thread_name = await self._generate_thread_name(
    message.content,
    message.author.display_name
)
```

## Configuration

No additional environment variables required. Uses existing:
- `BACKEND_MODE` (ollama or agentcore)
- `OLLAMA_MODEL` or `BEDROCK_MODEL_ID`
- All other agent settings

## Logging

```python
# Success
INFO - Generated thread name: {name}

# Fallback
WARNING - Agent returned empty thread name, using fallback
ERROR - Failed to generate thread name with agent: {error}
```

## Deployment

Feature is production-ready:
- ✅ All tests pass
- ✅ Error handling robust
- ✅ Backward compatible
- ✅ No breaking changes

Simply deploy and run as normal:
```bash
uv run community-bot
```
