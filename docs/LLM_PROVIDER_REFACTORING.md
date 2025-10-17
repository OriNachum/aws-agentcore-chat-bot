# LLM_PROVIDER Configuration Refactoring

## Problem

The `LLM_PROVIDER` was being read directly from the environment as a global variable in `agentcore_app.py`, which meant:
- ❌ It was read at module import time, not when needed
- ❌ It wasn't part of the centralized configuration system
- ❌ It couldn't be easily overridden or tested
- ❌ It was inconsistent with how other settings were managed

## Solution

Moved `LLM_PROVIDER` into the `Settings` configuration system:

### 1. Added to Settings Class (`config.py`)

```python
@dataclass
class Settings:
    # ... other fields ...
    # LLM Provider (for agentcore mode)
    llm_provider: str = "bedrock"  # 'ollama' or 'bedrock'
```

### 2. Load from Environment (`config.py`)

```python
return Settings(
    # ... other fields ...
    llm_provider=os.getenv("LLM_PROVIDER", "bedrock"),
)
```

### 3. Use Settings in agentcore_app.py

**Before:**
```python
# Global variable read at module load time
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "bedrock")

# Later in code
provider = _force_provider or LLM_PROVIDER
logger.info(f"Environment LLM_PROVIDER: {LLM_PROVIDER}")
```

**After:**
```python
# Read through settings
provider = _force_provider or settings.llm_provider
logger.info(f"Settings LLM Provider: {settings.llm_provider}")
```

## Benefits

✅ **Centralized Configuration**: All settings in one place (`Settings` class)
✅ **Consistent Pattern**: Same as other settings (aws_region, ollama_model, etc.)
✅ **Testable**: Can be easily mocked or overridden in tests
✅ **Type-Safe**: Part of the typed `Settings` dataclass
✅ **Late Binding**: Read when `load_settings()` is called, not at import time
✅ **Clear Flow**: Config → Settings → Agent initialization

## Configuration Flow

```
Environment Variable (LLM_PROVIDER)
    ↓
load_settings() in config.py
    ↓
Settings.llm_provider
    ↓
get_agent() in agentcore_app.py
    ↓
provider = _force_provider or settings.llm_provider
    ↓
Model initialization (Ollama or Bedrock)
```

## Files Changed

1. **`src/community_bot/config.py`**
   - Added `llm_provider` field to `Settings` dataclass
   - Added loading from `LLM_PROVIDER` environment variable

2. **`src/community_bot/agentcore_app.py`**
   - Removed global `LLM_PROVIDER` variable
   - Updated all references to use `settings.llm_provider`
   - Updated logging to reflect new pattern

## Testing

```powershell
# Set environment
$env:LLM_PROVIDER = "bedrock"
$env:BACKEND_MODE = "agentcore"

# Test configuration loading
uv run python -c "from community_bot.config import load_settings; s=load_settings(); print(s.llm_provider)"

# Output: bedrock ✅
```

## Backward Compatibility

✅ **Fully backward compatible** - The environment variable name (`LLM_PROVIDER`) remains the same
✅ **Same default** - Still defaults to "bedrock" if not set
✅ **No breaking changes** - All existing configurations continue to work

## Usage Examples

### Setting LLM Provider

**Option 1: Environment Variable**
```powershell
$env:LLM_PROVIDER = "bedrock"  # or "ollama"
```

**Option 2: .env File**
```bash
LLM_PROVIDER=bedrock
```

**Option 3: Programmatic Override**
```python
# For special cases (testing, dynamic switching)
set_provider("ollama")  # Still supported via _force_provider
```

## Related Settings

The LLM provider works together with model-specific settings:

### When `llm_provider = "ollama"`
```bash
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

### When `llm_provider = "bedrock"`
```bash
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=4096
BEDROCK_STREAMING=true
AWS_REGION=us-east-1
```

## Summary

This refactoring improves the architecture by:
- ✅ Centralizing all configuration in the `Settings` class
- ✅ Following the existing configuration pattern
- ✅ Making the code more maintainable and testable
- ✅ Maintaining full backward compatibility

The `LLM_PROVIDER` is now properly integrated into the configuration system and flows cleanly through the application.
