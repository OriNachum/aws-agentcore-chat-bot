#!/usr/bin/env python3
"""
Example data collection script.

This script demonstrates the expected output format for ScriptAgent.
The script should output JSON to stdout with the following structure:

Single document:
{
    "content": "Document content here",
    "id": "unique-id",
    "title": "Optional title",
    "category": "optional-category",
    "metadata": {"key": "value"}
}

Or list of documents:
[
    {"content": "...", "id": "1"},
    {"content": "...", "id": "2"}
]
"""

import json
import sys
from datetime import datetime


def collect_data():
    """Collect data and return as documents."""
    # This is an example - replace with actual data collection logic
    documents = [
        {
            "content": "This is an example document collected by the script agent.",
            "id": f"example_{datetime.utcnow().isoformat()}",
            "title": "Example Document",
            "category": "examples",
            "metadata": {
                "collected_at": datetime.utcnow().isoformat(),
                "source": "example_collector",
            }
        }
    ]
    
    return documents


def main():
    """Main entry point."""
    try:
        documents = collect_data()
        # Output JSON to stdout
        print(json.dumps(documents, indent=2))
        sys.exit(0)
    except Exception as e:
        # Log errors to stderr
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
