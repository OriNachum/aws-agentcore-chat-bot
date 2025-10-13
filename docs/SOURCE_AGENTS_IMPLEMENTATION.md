# Source Agents Implementation Summary

## Overview

Successfully implemented the Source Agents system for automatically collecting and uploading data to the knowledge base, as designed in `docs/plan/sub-agents.md`.

## What Was Implemented

### Core Framework

1. **Base Infrastructure** (`src/community_bot/source_agents/`)
   - `base.py` - Abstract `SourceAgent` interface
   - `document.py` - `Document` data model for knowledge content
   - `registry.py` - `AgentRegistry` for managing agents
   - `scheduler.py` - `AgentScheduler` for running agents on intervals
   - `uploader.py` - `S3Uploader` for uploading to S3
   - `syncer.py` - `BedrockKBSyncer` for triggering KB ingestion
   - `config_loader.py` - YAML configuration loader

### Agent Implementations

2. **Agent Types** (`src/community_bot/source_agents/agents/`)
   - `script.py` - `ScriptAgent` - Run custom Python scripts
   - `database.py` - `DatabaseAgent` - Query PostgreSQL databases (requires asyncpg)

### Integration

3. **Main Bot Integration** (`src/community_bot/`)
   - Updated `config.py` with source agent settings
   - Updated `main.py` to start agents with bot
   - Agents run in background when enabled

### Scripts

4. **Entry Points**
   - `scripts/run_source_agents.py` - Standalone runner
   - Supports `--once` flag for single run
   - Supports `--agent-id` for specific agent
   - Added to `pyproject.toml` as `source-agents` command

### Configuration

5. **Configuration Files**
   - `agents/sources/config.yaml` - Agent definitions
   - `agents/sources/scripts/example_collector.py` - Example script
   - Updated `.env.example` with source agent variables

### Documentation

6. **Documentation**
   - `docs/SOURCE_AGENTS_QUICKSTART.md` - Quick start guide
   - `agents/sources/README.md` - Agent directory guide
   - Updated main `README.md` with source agents section

### Tests

7. **Test Suite** (`tests/test_source_agents.py`)
   - Unit tests for Document, Registry, Scheduler
   - Integration tests for ScriptAgent
   - Mock implementations for testing

## File Structure

```
mike-et-al-community-bot/
├── src/community_bot/
│   ├── source_agents/
│   │   ├── __init__.py
│   │   ├── base.py              # SourceAgent interface
│   │   ├── document.py          # Document model
│   │   ├── registry.py          # AgentRegistry
│   │   ├── scheduler.py         # AgentScheduler
│   │   ├── uploader.py          # S3Uploader
│   │   ├── syncer.py            # BedrockKBSyncer
│   │   ├── config_loader.py     # YAML loader
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── script.py        # ScriptAgent
│   │       └── database.py      # DatabaseAgent
│   ├── config.py                # Updated with source agent settings
│   └── main.py                  # Integrated with bot startup
├── scripts/
│   └── run_source_agents.py     # Standalone runner
├── agents/sources/
│   ├── config.yaml              # Agent configuration
│   ├── README.md
│   └── scripts/
│       └── example_collector.py
├── tests/
│   └── test_source_agents.py
├── docs/
│   └── SOURCE_AGENTS_QUICKSTART.md
├── pyproject.toml               # Updated dependencies
└── .env.example                 # Updated with new vars
```

## Configuration Variables

Added to `.env`:

```bash
SOURCE_AGENTS_ENABLED=false              # Enable/disable
SOURCE_AGENTS_S3_BUCKET=                 # S3 bucket for documents
SOURCE_AGENTS_S3_REGION=us-east-1        # AWS region
SOURCE_AGENTS_DATA_SOURCE_ID=            # Bedrock KB data source
SOURCE_AGENTS_RUN_ON_STARTUP=false       # Run on bot start
SOURCE_AGENTS_INTERVAL=3600              # Collection interval (seconds)
```

## Usage Examples

### Run with Discord Bot

```bash
# Enable in .env
SOURCE_AGENTS_ENABLED=true
SOURCE_AGENTS_S3_BUCKET=my-kb-bucket

# Start bot (agents run automatically)
uv run community-bot
```

### Run Standalone

```bash
# Run all agents once
python scripts/run_source_agents.py --once

# Run specific agent
python scripts/run_source_agents.py --agent-id example_collector

# Run continuously
python scripts/run_source_agents.py
```

### Configure Custom Agent

Edit `agents/sources/config.yaml`:

```yaml
agents:
  - id: "my_custom_agent"
    type: "script"
    enabled: true
    schedule: "0 */6 * * *"
    config:
      script_path: "./agents/sources/scripts/my_script.py"
      category: "custom_data"
```

## Key Features

1. **Flexible Agent Types**: Script and Database agents implemented, easy to add more
2. **Automatic Scheduling**: Agents run on configurable intervals
3. **S3 Integration**: Documents uploaded to S3 in organized structure
4. **Bedrock KB Sync**: Optional automatic KB ingestion triggering
5. **Bot Integration**: Runs alongside Discord bot or standalone
6. **Configuration-Driven**: YAML config with environment variable support
7. **Monitoring**: Comprehensive logging and error handling
8. **Testing**: Full test suite with mocks

## S3 Document Structure

Documents are organized in S3:

```
s3://bucket/
  category/
    YYYY/MM/DD/
      agent_type/
        source_id.json
```

Example:
```
s3://my-kb-bucket/
  examples/
    2024/10/13/
      script/
        example_2024-10-13T12:00:00.json
```

## Document Format

Documents follow a standard structure:

```json
{
  "content": "Document text content",
  "metadata": {
    "source_type": "script",
    "source_id": "example_123",
    "title": "Example Document",
    "timestamp": "2024-10-13T12:00:00Z",
    "tags": "tag1,tag2",
    "category": "examples"
  }
}
```

## Dependencies

Required:
- `boto3` - AWS S3 and Bedrock integration (already in project)

Optional:
- `pyyaml` - YAML config loading
- `asyncpg` - PostgreSQL database agents

Added to `pyproject.toml`:
```toml
[project.optional-dependencies]
source-agents = [
    "pyyaml>=6.0",
    "asyncpg>=0.29.0",
]
```

## Testing

Run tests:

```bash
# All tests
pytest tests/test_source_agents.py -v

# Specific test
pytest tests/test_source_agents.py::test_document_to_s3_key -v
```

## Future Enhancements

The design document (`docs/plan/sub-agents.md`) includes specifications for:

- **BrowserAgent**: Web scraping with Playwright
- **MCPAgent**: Model Context Protocol integration
- **StrandsAgent**: AI-powered collection with Strands
- **Content Enrichment**: AI-generated tags and summaries
- **Deduplication**: Avoid uploading duplicate content
- **Streaming Agents**: Real-time data collection
- **CloudWatch Metrics**: Detailed monitoring
- **Lambda Deployment**: Serverless agent execution

These can be added incrementally as needed.

## Migration Path

For existing users:

1. **Optional Feature**: Source agents are disabled by default
2. **No Breaking Changes**: Existing functionality unchanged
3. **Gradual Adoption**: Enable agents when ready
4. **Backward Compatible**: Works with existing KB setup

## Next Steps

1. **Install Dependencies** (if using YAML config):
   ```bash
   pip install pyyaml
   ```

2. **Configure Agents**: Edit `agents/sources/config.yaml`

3. **Create Collection Scripts**: Add scripts to `agents/sources/scripts/`

4. **Enable and Test**:
   ```bash
   # Test single run
   python scripts/run_source_agents.py --once
   
   # Enable in .env
   SOURCE_AGENTS_ENABLED=true
   
   # Run with bot
   uv run community-bot
   ```

5. **Monitor**: Check logs for agent execution

6. **Scale**: Add more agents, configure scheduling, deploy to AWS

## Documentation

- **Quick Start**: `docs/SOURCE_AGENTS_QUICKSTART.md`
- **Design Document**: `docs/plan/sub-agents.md`
- **Agent Directory**: `agents/sources/README.md`
- **Main README**: Updated with source agents section

## Summary

The Source Agents system is now fully implemented and ready to use. It provides a flexible, extensible framework for automatically keeping the knowledge base up-to-date with data from various sources. The system integrates seamlessly with the existing Discord bot while also supporting standalone operation.
