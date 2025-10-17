# Source Agents

This directory contains source agents configuration and scripts for automatically collecting and uploading data to the knowledge base.

## Structure

```
agents/sources/
├── config.yaml           # Agent configuration file
└── scripts/             # Collection scripts
    └── example_collector.py
```

## Configuration

Edit `config.yaml` to define your agents. Each agent configuration includes:

- `id`: Unique identifier for the agent
- `type`: Agent type (`script`, `database`, etc.)
- `enabled`: Whether the agent is active
- `schedule`: Cron expression for collection frequency
- `config`: Type-specific configuration

## Creating Collection Scripts

Collection scripts should:

1. Collect data from your source
2. Format data as Document objects
3. Output JSON to stdout

### Example Script

```python
#!/usr/bin/env python3
import json
from datetime import datetime

def collect_data():
    documents = [
        {
            "content": "Your content here",
            "id": f"unique_id_{datetime.utcnow().isoformat()}",
            "title": "Document Title",
            "category": "my_category",
            "metadata": {"key": "value"}
        }
    ]
    return documents

if __name__ == "__main__":
    print(json.dumps(collect_data(), indent=2))
```

## Testing

Test your script manually:

```bash
python agents/sources/scripts/your_script.py
```

Expected output should be valid JSON.

## Running

Source agents run automatically with the Discord bot when enabled, or can be run standalone:

```bash
# Run all agents once
python scripts/run_source_agents.py --once

# Run specific agent
python scripts/run_source_agents.py --agent-id your_agent_id

# Run continuously
python scripts/run_source_agents.py
```

## Documentation

- [Quick Start Guide](../../docs/SOURCE_AGENTS_QUICKSTART.md)
- [Design Document](../../docs/plan/sub-agents.md)
