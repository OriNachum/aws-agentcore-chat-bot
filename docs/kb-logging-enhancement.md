# Knowledge Base Integration Logging Enhancement

## Summary of Changes

Enhanced logging has been added throughout the AgentCore and knowledge base integration code to help diagnose issues where the agent works on AWS console but not in your local code.

## Files Modified

### 1. `src/community_bot/agentcore_app.py`
Added comprehensive logging to:
- `query_knowledge_base_via_gateway()` - Main KB query orchestration
- `_query_via_agentcore_gateway()` - Gateway-specific queries
- `_query_via_direct_api()` - Direct API queries
- `_extract_content_from_result()` - Content extraction logic
- `kb_query_tool()` - Strands tool function
- `get_agent()` - Agent initialization
- `chat_with_agent()` - Main chat processing

**Log markers added:**
- `[KB QUERY]` - Knowledge base operations
- `[GATEWAY]` - AgentCore Gateway calls
- `[DIRECT API]` - Direct KB API calls
- `[EXTRACT]` - Content extraction
- `[KB TOOL]` - Tool invocation by agent
- `[AGENT INIT]` - Agent setup
- `[CHAT]` - Chat flow processing

### 2. `src/community_bot/agent_client.py`
Enhanced logging in:
- `chat()` method - Added detailed tracking of backend selection and response handling
- Added explicit empty response detection

**Log markers added:**
- `[AGENT CLIENT]` - Client-side processing

## Files Created

### 1. `diagnose_kb_integration.py`
Comprehensive diagnostic tool that tests:
- Environment variable configuration
- AgentCore services availability
- Gateway client initialization
- Direct KB API connectivity
- Gateway KB query
- KB tool execution
- Agent initialization
- Simple chat (KB disabled)
- Chat with KB enabled

**Usage:**
```powershell
python diagnose_kb_integration.py
```

### 2. `test_kb_integration.py`
Simple test script for quick verification:
- Tests basic chat without KB
- Tests chat with KB enabled
- Shows configuration and results

**Usage:**
```powershell
python test_kb_integration.py
```

### 3. `docs/troubleshooting-kb-integration.md`
Complete troubleshooting guide covering:
- Common issues and solutions
- Understanding log flow
- Environment setup
- Diagnostic tool usage
- Differences between console and code execution

## How to Use

### Quick Test
```powershell
# Set up environment
$env:BACKEND_MODE = "agentcore"
$env:KB_DIRECT_ENDPOINT = "https://your-kb-api.example.com"

# Run quick test
python test_kb_integration.py
```

### Full Diagnostics
```powershell
# Run comprehensive diagnostic
python diagnose_kb_integration.py > diagnostic.log

# Review the log
cat diagnostic.log
```

### Enable Debug Logging
```powershell
$env:LOG_LEVEL = "DEBUG"
python src/community_bot/agentcore_app.py
```

## Log Output Examples

### Successful KB Query
```
[KB QUERY] Starting knowledge base query with: tell me about...
[KB QUERY] Gateway configuration: gateway_id=None, endpoint=None
[KB QUERY] Attempting direct API query...
[DIRECT API] Querying knowledge base endpoint: https://...
[DIRECT API] Response status: 200
[DIRECT API] ✅ Received successful response
[EXTRACT] Result is dict with keys: ['results', 'metadata']
[EXTRACT] Found 'results' array with 3 items
[EXTRACT] ✅ Combined 3 snippets - 1234 total characters
[KB QUERY] ✅ Successfully queried via direct API - 1234 characters
```

### Failed KB Query
```
[KB QUERY] Starting knowledge base query with: tell me about...
[KB QUERY] Gateway configuration: gateway_id=None, endpoint=None
[KB QUERY] Direct endpoint: None
[KB QUERY] ❌ No knowledge base configured or available
[KB QUERY] Configuration check:
  - KB_GATEWAY_ID: NOT SET
  - KB_GATEWAY_ENDPOINT: NOT SET
  - KB_DIRECT_ENDPOINT: NOT SET
  - Gateway client: NOT AVAILABLE
```

### Empty Response Detection
```
[AGENT CLIENT] Using AgentCore Strands framework
[CHAT] Processing user message: hello...
[CHAT] Invoking Strands agent...
[CHAT] Agent response: 0 characters
[AGENT CLIENT] ❌ EMPTY RESPONSE from AgentCore!
[AGENT CLIENT] This is likely the issue - agent returned nothing
```

## Debugging Strategy

1. **Run diagnostic tool** to identify which component fails
2. **Check environment variables** are correctly set
3. **Enable DEBUG logging** for detailed output
4. **Follow log markers** to trace execution flow
5. **Look for first ❌ or ⚠️** in the log chain
6. **Compare with console behavior** using the same queries

## Common Issues Identified

The logging will help identify:

1. **Missing configuration** - ENV vars not set
2. **Network issues** - KB endpoint unreachable
3. **Response format mismatch** - KB returns unexpected format
4. **Tool not invoked** - Agent doesn't use the KB tool
5. **Empty responses** - Agent processes but returns nothing
6. **Gateway vs Direct** - Which method is being used/failing

## Benefits

- **Visual flow tracking** with markers and separators
- **Success/failure indicators** with ✅/❌/⚠️
- **Detailed context** at each step
- **Error stack traces** for exceptions
- **Configuration verification** logs
- **Response size tracking** to detect empty results
- **Comparative analysis** between different code paths

## Next Steps

1. Run the diagnostic on your setup
2. Review the troubleshooting guide
3. Check logs for the specific failure point
4. Fix configuration or code based on findings
5. Re-test with the simple test script

The enhanced logging should now make it much easier to identify exactly where and why the KB integration differs between console and code execution.
