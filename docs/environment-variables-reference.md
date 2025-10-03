# Environment Variables Quick Reference

## Required Variables

### Backend Configuration
```powershell
# Which backend to use: "ollama" or "agentcore"
$env:BACKEND_MODE = "agentcore"

# LLM provider: "ollama" or "bedrock"
$env:LLM_PROVIDER = "ollama"
```

### Ollama Configuration (if using Ollama)
```powershell
# Ollama model name
$env:OLLAMA_MODEL = "llama3"

# Ollama API endpoint
$env:OLLAMA_BASE_URL = "http://localhost:11434"
```

## Knowledge Base Configuration

Choose ONE of these approaches:

### Option 1: AgentCore Gateway (Recommended)
```powershell
# Gateway ID from AgentCore
$env:KB_GATEWAY_ID = "your-gateway-id"

# Gateway endpoint URL
$env:KB_GATEWAY_ENDPOINT = "https://your-gateway.aws.amazon.com"
```

### Option 2: Direct API (Fallback)
```powershell
# Direct KB API endpoint
$env:KB_DIRECT_ENDPOINT = "https://your-kb-api.example.com"

# API key (optional, if required by your KB)
$env:KB_DIRECT_API_KEY = "your-api-key"
```

### Option 3: Legacy Configuration
```powershell
# These may be used by setup functions
$env:KNOWLEDGE_BASE_ENDPOINT = "https://your-kb-api.example.com"
$env:KNOWLEDGE_BASE_API_KEY = "your-api-key"
```

## Optional Variables

### Logging
```powershell
# Log level: DEBUG, INFO, WARNING, ERROR
$env:LOG_LEVEL = "DEBUG"
```

### AgentCore Deployment
```powershell
# Run in AgentCore deployment mode
$env:AGENTCORE_MODE = "true"
```

### AWS Credentials (for deployment)
```powershell
$env:AWS_ACCESS_KEY_ID = "your-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

## Complete Setup Examples

### Example 1: Local Development with Direct KB
```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:KB_DIRECT_ENDPOINT = "https://your-kb.example.com"
$env:KB_DIRECT_API_KEY = "your-key"
$env:LOG_LEVEL = "DEBUG"
```

### Example 2: AgentCore Gateway
```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:KB_GATEWAY_ID = "gw-abc123"
$env:KB_GATEWAY_ENDPOINT = "https://gateway.aws.amazon.com"
$env:LOG_LEVEL = "DEBUG"
```

### Example 3: Ollama Only (No KB)
```powershell
$env:BACKEND_MODE = "ollama"
$env:OLLAMA_MODEL = "llama3"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:LOG_LEVEL = "INFO"
```

### Example 4: AWS Bedrock with KB
```powershell
$env:BACKEND_MODE = "agentcore"
$env:LLM_PROVIDER = "bedrock"
$env:KB_GATEWAY_ID = "gw-abc123"
$env:KB_GATEWAY_ENDPOINT = "https://gateway.aws.amazon.com"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:LOG_LEVEL = "INFO"
```

## Checking Current Configuration

```powershell
# List all relevant environment variables
Get-ChildItem Env: | Where-Object { 
    $_.Name -like "*OLLAMA*" -or 
    $_.Name -like "*KB_*" -or 
    $_.Name -like "*BACKEND*" -or
    $_.Name -like "*LLM*" -or
    $_.Name -like "*KNOWLEDGE*"
}

# Or use the diagnostic tool
python diagnose_kb_integration.py
```

## Clearing Configuration

```powershell
# Clear all KB-related variables
Remove-Item Env:KB_GATEWAY_ID -ErrorAction SilentlyContinue
Remove-Item Env:KB_GATEWAY_ENDPOINT -ErrorAction SilentlyContinue
Remove-Item Env:KB_DIRECT_ENDPOINT -ErrorAction SilentlyContinue
Remove-Item Env:KB_DIRECT_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:KNOWLEDGE_BASE_ENDPOINT -ErrorAction SilentlyContinue
Remove-Item Env:KNOWLEDGE_BASE_API_KEY -ErrorAction SilentlyContinue
```

## Configuration Priority

The code checks for KB configuration in this order:

1. **Gateway** (if both KB_GATEWAY_ID and KB_GATEWAY_ENDPOINT are set)
2. **Direct API** (if KB_DIRECT_ENDPOINT is set)
3. **No KB** (if none are configured)

## Troubleshooting

### Variable not being recognized?
```powershell
# Check if set
$env:VARIABLE_NAME

# Set temporarily (current session only)
$env:VARIABLE_NAME = "value"

# Set permanently (user level)
[System.Environment]::SetEnvironmentVariable("VARIABLE_NAME", "value", "User")
```

### Configuration conflicts?
```powershell
# See what's actually being used
python -c "from community_bot.config import load_settings; s = load_settings(); print(f'Backend: {s.backend_mode}'); print(f'Model: {s.ollama_model}'); print(f'URL: {s.ollama_base_url}')"
```

## Tips

1. **Use DEBUG logging** during setup and troubleshooting
2. **Keep credentials secure** - don't commit API keys to git
3. **Test incrementally** - start without KB, then add it
4. **Use diagnostic tools** before assuming configuration issues
5. **Check logs** - they now show which variables are set/used
