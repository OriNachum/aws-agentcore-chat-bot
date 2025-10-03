# Troubleshooting Knowledge Base Integration

This guide helps you diagnose and fix issues with AWS Strands + AgentCore knowledge base integration.

## Problem: Agent Works in Console But Not in Code

If your agent works fine when testing directly on the AWS console but returns empty results or no KB data when running through your code, this is a common integration issue. The enhanced logging will help you track down where the problem occurs.

## New Diagnostic Tools

### 1. Enhanced Logging

All critical components now have detailed logging with visual markers:

- `[KB QUERY]` - Knowledge base query operations
- `[GATEWAY]` - AgentCore Gateway operations
- `[DIRECT API]` - Direct KB API calls
- `[EXTRACT]` - Content extraction from KB results
- `[KB TOOL]` - Strands tool invocation
- `[AGENT INIT]` - Agent initialization
- `[CHAT]` - Chat processing flow
- `[AGENT CLIENT]` - Client-side processing

Look for these markers in your logs to track the flow:
- ✅ = Success
- ❌ = Error
- ⚠️ = Warning

### 2. Diagnostic Script

Run the comprehensive diagnostic:

```powershell
python diagnose_kb_integration.py
```

This will test each component separately:
1. Environment variables
2. AgentCore services availability
3. Gateway client initialization
4. Direct KB API query
5. Gateway KB query
6. KB tool execution
7. Agent initialization
8. Simple chat (without KB)
9. Chat with KB enabled

### 3. Simple Test Script

Quick test of basic functionality:

```powershell
python test_kb_integration.py
```

## Setup Your Environment

Before running diagnostics, ensure you have the right environment variables:

### For AgentCore Gateway

```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3"
$env:OLLAMA_BASE_URL = "http://localhost:11434"

# AgentCore Gateway (preferred method)
$env:KB_GATEWAY_ID = "your-gateway-id"
$env:KB_GATEWAY_ENDPOINT = "your-gateway-endpoint"
```

### For Direct API (Fallback)

```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3"
$env:OLLAMA_BASE_URL = "http://localhost:11434"

# Direct KB API
$env:KB_DIRECT_ENDPOINT = "https://your-kb-api.example.com"
$env:KB_DIRECT_API_KEY = "your-api-key"  # Optional
```

## Common Issues & Solutions

### Issue 1: Empty Responses from Agent

**Symptoms:**
- Agent returns empty string or very short response
- Console shows `[AGENT CLIENT] ❌ EMPTY RESPONSE from AgentCore!`

**Diagnosis:**
```powershell
python diagnose_kb_integration.py
```

Look for where the chain breaks:
1. Check if KB query returns results: `[KB QUERY] ✅`
2. Check if content extracted: `[EXTRACT] ✅`
3. Check if KB tool receives data: `[KB TOOL] ✅`
4. Check if agent processes it: `[CHAT] ✅`

**Common causes:**
- KB endpoint not configured (missing env vars)
- KB endpoint unreachable
- Wrong API format/response structure
- Agent not invoking the KB tool

### Issue 2: KB Tool Not Being Called

**Symptoms:**
- No `[KB TOOL]` logs appearing
- Agent responds without using KB data

**Solution:**
1. Verify agent has the tool:
   ```powershell
   python -c "from community_bot.agentcore_app import get_agent; a = get_agent(); print(f'Tools: {len(a._tools)}')"
   ```

2. Check if the tool is properly registered in Strands

3. Verify the tool description is clear for the LLM to understand when to use it

### Issue 3: Gateway Client Fails

**Symptoms:**
- `[GATEWAY] ❌ Gateway query failed`
- Falls back to direct API

**Solution:**
1. Check AgentCore services installation:
   ```powershell
   python -c "from bedrock_agentcore.services.gateway import GatewayClient; print('OK')"
   ```

2. Update bedrock-agentcore if needed:
   ```powershell
   pip install --upgrade bedrock-agentcore
   ```

3. If gateway is not available, configure direct API as fallback

### Issue 4: Content Extraction Fails

**Symptoms:**
- `[EXTRACT] ❌ Could not extract content from result`
- KB query succeeds but no content available

**Solution:**
1. Check the KB response format in logs
2. The extraction function expects:
   - String responses
   - Dict with keys: `content`, `text`, or `answer`
   - Dict with `results` array containing items with `content`/`text`

3. If your KB has a different format, update `_extract_content_from_result()` in `agentcore_app.py`

### Issue 5: Agent Initialized But Tool Not Working

**Symptoms:**
- Agent starts successfully
- Tool is registered
- But KB queries never happen

**Diagnosis:**
Enable maximum logging:
```powershell
$env:LOG_LEVEL = "DEBUG"
python test_kb_integration.py
```

Look for:
1. Is `use_knowledge_base=True`? Check `[CHAT] Knowledge base augmentation enabled`
2. Is query attempted? Check for `[CHAT] Querying knowledge base for context...`
3. Does Strands agent actually call the tool? Check for `[KB TOOL] kb-query-tool invoked`

## Understanding the Logging Flow

When a chat request comes in with KB enabled, you should see this sequence:

```
[AGENT CLIENT] Processing chat request...
[CHAT] Processing user message...
[CHAT] Knowledge base augmentation enabled
[CHAT] Querying knowledge base for context...
[KB QUERY] Starting knowledge base query...
[GATEWAY]/[DIRECT API] (one of these)
[EXTRACT] Extracting content...
[CHAT] ✅ Knowledge base context retrieved
[CHAT] Invoking Strands agent...
================================================================================
[KB TOOL] kb-query-tool invoked by Strands agent  <-- Agent uses the tool
[KB QUERY] Starting knowledge base query...
... (KB query repeats)
[KB TOOL] ✅ Found content
================================================================================
[CHAT] Agent invocation completed
[AGENT CLIENT] ✅ AgentCore response received
```

**Key point:** The KB might be queried TWICE:
1. First in `chat_with_agent()` to get context for the prompt
2. Second by the Strands agent itself via the `kb-query-tool`

If you only see #1 but not #2, the agent isn't invoking the tool - this could be:
- LLM not understanding when to use the tool
- Tool description needs improvement
- Model capabilities issue

## Testing Locally vs Console

The main difference between console and code:

**Console:**
- AWS manages the runtime
- AgentCore handles KB integration automatically
- Tools are auto-configured

**Your Code:**
- You must configure everything manually
- Environment variables must be set correctly
- Tools must be registered with the agent
- KB endpoints must be accessible from your machine

## Next Steps

1. **Run diagnostics:**
   ```powershell
   python diagnose_kb_integration.py > diagnostic.log
   ```

2. **Review the log** - look for the first ❌ or ⚠️ in the chain

3. **Fix the issue** based on the section above

4. **Test again:**
   ```powershell
   python test_kb_integration.py
   ```

5. **If still failing**, share your diagnostic log for further help

## Helpful Debug Commands

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test KB endpoint directly
curl -X POST https://your-kb-endpoint/query -H "Content-Type: application/json" -d '{\"query\":\"test\"}'

# View real-time logs
$env:LOG_LEVEL = "DEBUG"
python src/community_bot/agentcore_app.py

# Test with Python directly
python -c "from community_bot.agentcore_app import chat_with_agent; print(chat_with_agent('hello'))"
```

## Still Having Issues?

If the diagnostic tools don't resolve your issue:

1. Capture full logs with DEBUG level
2. Check the specific error messages
3. Compare KB response format between console and code
4. Verify network access to KB endpoint
5. Test each component in isolation

The enhanced logging should now give you much better visibility into where exactly the integration is failing.
