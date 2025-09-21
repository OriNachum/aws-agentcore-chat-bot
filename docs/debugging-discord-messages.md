# Debugging Discord Message Processing

This document explains how to use the comprehensive logging system to diagnose why Discord messages might not be picked up and processed by the community bot.

## Quick Start - Enable Debug Logging

1. **Set debug level in your `.env` file:**
   ```env
   LOG_LEVEL=DEBUG
   ```

2. **Run your bot normally:**
   ```bash
   uv run community-bot
   ```

3. **Check the console output for detailed logs** that show exactly what's happening with each message.

## Log Levels

| Level | Purpose | When to Use |
|-------|---------|-------------|
| `DEBUG` | Very detailed information | Troubleshooting message flow issues |
| `INFO` | General operational information | Normal monitoring |
| `WARNING` | Warning messages | Monitor for potential issues |
| `ERROR` | Error messages | When something goes wrong |
| `CRITICAL` | Critical errors | System failures |

## Common Issues and Log Patterns

### 1. **Bot Not Receiving Messages**

**Look for:** Missing "Received message from..." logs

**Possible causes:**
- Bot not connected to Discord
- Missing `message_content` intent
- Network connectivity issues

**Example logs:**
```
2025-09-21 22:13:29 - community_bot.discord - INFO - Bot successfully logged in as YourBot (ID: 123456789)
2025-09-21 22:13:29 - community_bot.discord - DEBUG - Received message from User#1234 in channel 123456789: Hello world...
```

### 2. **Messages from Wrong Channel Ignored**

**Look for:** "Ignoring message from non-monitored channel" logs

**Solution:** Check your `DISCORD_CHANNEL_ID` setting

**Example logs:**
```
2025-09-21 22:13:29 - community_bot.discord - DEBUG - Ignoring message from non-monitored channel 987654321
```

### 3. **Bot Responding to Itself**

**Look for:** "Ignoring bot message" logs

**This is normal behavior** - the bot should ignore its own messages

**Example logs:**
```
2025-09-21 22:13:29 - community_bot.discord - DEBUG - Ignoring bot message from YourBot
```

### 4. **Backend Connection Issues**

**Look for:** Error logs in agent client or model components

**For Ollama issues:**
```
2025-09-21 22:13:29 - community_bot.model.ollama - ERROR - HTTP error communicating with Ollama: ...
```

**For AgentCore issues:**
```
2025-09-21 22:13:29 - community_bot.agent - ERROR - AgentCore invocation failed: ...
```

### 5. **Memory Management Issues**

**Look for:** Memory trimming logs

**Example logs:**
```
2025-09-21 22:13:29 - community_bot.memory - INFO - Memory trimmed: 51 -> 50 messages (kept 1 system + 49 recent)
```

## Message Flow Tracking

With DEBUG logging enabled, you can track a message through the entire system:

1. **Message Received:**
   ```
   community_bot.discord - DEBUG - Received message from User#1234 in channel 123456789: Hello...
   ```

2. **Channel Validation:**
   ```
   community_bot.discord - INFO - Processing message from User#1234 (987654321): Hello...
   ```

3. **Agent Processing:**
   ```
   community_bot.agent - DEBUG - Processing chat request: Hello...
   community_bot.agent - DEBUG - Using LocalAgent framework for Ollama backend
   ```

4. **Model Communication:**
   ```
   community_bot.model.ollama - DEBUG - Starting chat request to http://localhost:11434/api/chat
   community_bot.model.ollama - DEBUG - Ollama response status: 200
   community_bot.model.ollama - DEBUG - Received chunk 1: 15 characters
   ```

5. **Response Sent:**
   ```
   community_bot.discord - INFO - Successfully responded to message from User#1234
   ```

## Testing Your Logging Setup

Run the included test script to verify logging is working:

```bash
python test_logging.py
```

This will test all logging components without requiring Discord or Ollama connections.

## Performance Notes

- **DEBUG level** generates a lot of output and may slow down the bot slightly
- **INFO level** is recommended for production monitoring
- **ERROR level** only shows problems, good for silent operation

## Log File Output (Optional)

You can redirect logs to a file:

```bash
uv run community-bot > bot.log 2>&1
```

Or run in background and monitor:
```bash
uv run community-bot > bot.log 2>&1 &
tail -f bot.log
```

## Troubleshooting Tips

1. **Start with DEBUG level** when diagnosing issues
2. **Look for the last successful log** before things stop working
3. **Check timestamps** to understand timing issues
4. **Watch for HTTP status codes** in Ollama communications
5. **Verify channel IDs** are numeric, not channel names

## Environment Variables

Add to your `.env` file:

```env
# Set logging level
LOG_LEVEL=DEBUG

# Your other existing settings...
DISCORD_BOT_TOKEN=your_token_here
DISCORD_CHANNEL_ID=123456789
BACKEND_MODE=ollama
OLLAMA_MODEL=your_model
```