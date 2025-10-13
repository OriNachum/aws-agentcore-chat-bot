# Source Agents Quick Start Guide

## Overview

Source Agents are background processes that continuously collect data and upload it to S3 to enrich the Bedrock Knowledge Base. This enables your Discord bot to have access to up-to-date information from various sources.

## Quick Start

### 1. Enable Source Agents

Add to your `.env` file:

```bash
# Enable source agents
SOURCE_AGENTS_ENABLED=true

# S3 configuration
SOURCE_AGENTS_S3_BUCKET=my-knowledge-base-bucket
SOURCE_AGENTS_S3_REGION=us-east-1

# Optional: Bedrock KB sync
SOURCE_AGENTS_DATA_SOURCE_ID=your-data-source-id

# Optional: Run agents on bot startup
SOURCE_AGENTS_RUN_ON_STARTUP=false

# Optional: Collection interval in seconds (default: 3600 = 1 hour)
SOURCE_AGENTS_INTERVAL=3600
```

### 2. Configure Agents

Edit `agents/sources/config.yaml`:

```yaml
agents:
  # Script-based agent (simplest option)
  - id: "my_collector"
    type: "script"
    enabled: true
    schedule: "0 */1 * * *"  # Hourly
    config:
      script_path: "./agents/sources/scripts/my_collector.py"
      category: "my_data"
```

### 3. Create a Collection Script

Create `agents/sources/scripts/my_collector.py`:

```python
#!/usr/bin/env python3
import json
from datetime import datetime

def collect_data():
    """Collect your data here."""
    documents = [
        {
            "content": "Your document content",
            "id": f"doc_{datetime.utcnow().isoformat()}",
            "title": "Document Title",
            "category": "my_data",
            "metadata": {
                "source": "my_system",
                "collected_at": datetime.utcnow().isoformat(),
            }
        }
    ]
    return documents

if __name__ == "__main__":
    documents = collect_data()
    print(json.dumps(documents, indent=2))
```

### 4. Run Source Agents

**Option 1: Integrated with Discord Bot**

The source agents will run automatically in the background when you start the bot:

```bash
uv run community-bot
```

**Option 2: Standalone**

Run source agents separately:

```bash
# Run continuously
python scripts/run_source_agents.py

# Run once and exit
python scripts/run_source_agents.py --once

# Run specific agent
python scripts/run_source_agents.py --agent-id my_collector
```

## Agent Types

### Script Agent

The simplest type - runs any Python script that outputs JSON.

**Configuration:**
```yaml
- id: "my_script"
  type: "script"
  enabled: true
  schedule: "0 */6 * * *"
  config:
    script_path: "./agents/sources/scripts/my_script.py"
    category: "scripts"
    script_args: ["--arg1", "value1"]  # Optional
```

**Script Output Format:**
```python
# Single document
{
    "content": "Document text",
    "id": "unique-id",
    "title": "Optional title",
    "category": "optional-category",
    "metadata": {"key": "value"}
}

# Or multiple documents
[
    {"content": "...", "id": "1"},
    {"content": "...", "id": "2"}
]
```

### Database Agent

Collects data from PostgreSQL databases.

**Prerequisites:**
```bash
pip install asyncpg
```

**Configuration:**
```yaml
- id: "postgres_data"
  type: "database"
  enabled: true
  schedule: "0 */6 * * *"
  config:
    connection_string: "${DATABASE_URL}"
    query: "SELECT * FROM articles WHERE updated_at > NOW() - INTERVAL '6 hours'"
    category: "database"
    id_column: "id"
    title_column: "title"
    content_columns: ["title", "body", "tags"]  # Optional
```

## Document Format

All agents produce `Document` objects with this structure:

```python
{
    "content": str,          # Main text content (required)
    "source_type": str,      # Agent type (auto-set)
    "source_id": str,        # Unique identifier (required)
    "title": str,            # Display title (optional)
    "timestamp": datetime,   # Collection time (auto-set)
    "category": str,         # S3 folder (default: "general")
    "tags": [str],          # Searchable tags (optional)
    "metadata": dict,        # Additional data (optional)
}
```

## S3 Structure

Documents are organized in S3 like this:

```
s3://my-bucket/
  category/
    YYYY/MM/DD/
      agent_type/
        source_id.json
```

Example:
```
s3://kb-bucket/
  my_data/
    2024/10/13/
      script/
        doc_12345.json
```

## Monitoring

### Check Agent Status

```python
from community_bot.source_agents import AgentRegistry

registry = AgentRegistry()
# ... register agents ...

# List all agents
for agent_info in registry.list_agents():
    print(f"{agent_info['agent_id']}: {agent_info['schedule']}")
```

### View Logs

Source agents log to the same logger as the bot:

```
[source_agents] Registered 3 source agents
[agent.my_collector] Collected 5 documents from script
[s3_uploader] Uploaded document to s3://kb-bucket/my_data/2024/10/13/script/doc_1.json
[agent_scheduler] Agent my_collector result: {'success': True, ...}
```

## Bedrock KB Sync

If you configure `SOURCE_AGENTS_DATA_SOURCE_ID`, the system can automatically trigger Bedrock KB ingestion jobs after uploading documents.

**Setup:**

1. Get your data source ID from AWS Console:
   - Go to Bedrock > Knowledge Bases
   - Select your KB
   - Go to Data Sources tab
   - Copy the Data Source ID

2. Add to `.env`:
   ```bash
   SOURCE_AGENTS_DATA_SOURCE_ID=your-data-source-id
   ```

3. Run with sync:
   ```bash
   python scripts/run_source_agents.py --once
   # Will trigger KB sync after uploading
   ```

## Troubleshooting

### Agents Not Running

1. Check `SOURCE_AGENTS_ENABLED=true` in `.env`
2. Verify agent config exists: `agents/sources/config.yaml`
3. Check logs for registration errors
4. Ensure S3 bucket exists and credentials are valid

### Script Agent Errors

1. Test script manually:
   ```bash
   python agents/sources/scripts/my_script.py
   ```
2. Ensure script outputs valid JSON to stdout
3. Check script has read permissions
4. Verify Python dependencies are installed

### S3 Upload Failures

1. Check AWS credentials are configured
2. Verify S3 bucket exists and is accessible
3. Check IAM permissions for `s3:PutObject`
4. Review CloudWatch logs for detailed errors

### No Documents Collected

1. Verify your collection logic is working
2. Check script/query returns data
3. Enable debug logging: `LOG_LEVEL=DEBUG`
4. Test agent manually with `--agent-id`

## Advanced Usage

### Custom Schedules

Use cron expressions for scheduling:

```yaml
schedule: "0 */6 * * *"   # Every 6 hours
schedule: "0 2 * * *"     # Daily at 2 AM
schedule: "0 * * * *"     # Every hour
schedule: "*/30 * * * *"  # Every 30 minutes
schedule: "0 8 * * 1"     # Weekly on Monday at 8 AM
```

### Environment Variables in Config

Use `${VAR_NAME}` syntax:

```yaml
config:
  connection_string: "${DATABASE_URL}"
  api_key: "${MY_API_KEY}"
  base_url: "${API_BASE_URL}"
```

### Multiple Agents

Run different agents for different data sources:

```yaml
agents:
  - id: "database_articles"
    type: "database"
    # ...
  
  - id: "api_scraper"
    type: "script"
    # ...
  
  - id: "file_watcher"
    type: "script"
    # ...
```

## Next Steps

- Create custom collection scripts for your data sources
- Set up database agents for SQL databases
- Configure automatic KB sync
- Monitor agent performance with CloudWatch
- Scale with AWS Lambda for serverless collection

For more details, see the full [Source Agents Design Document](../plan/sub-agents.md).
