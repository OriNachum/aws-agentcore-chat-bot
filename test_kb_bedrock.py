#!/usr/bin/env python3
"""Quick test of Bedrock KB integration with boto3."""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()

from community_bot.agentcore_app import _query_bedrock_kb

def test_bedrock_kb():
    """Test Bedrock KB query."""
    
    kb_endpoint = os.getenv("KB_DIRECT_ENDPOINT")
    if not kb_endpoint:
        print("❌ KB_DIRECT_ENDPOINT not set")
        return
    
    print(f"Testing Bedrock KB: {kb_endpoint}")
    print("=" * 80)
    
    # Test query
    query = "What are word embeddings?"
    print(f"Query: {query}")
    print("-" * 80)
    
    result = _query_bedrock_kb(kb_endpoint, query, max_results=3)
    
    if result:
        print(f"✅ Got result!")
        print(f"Type: {type(result)}")
        print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            if "error" in result:
                print(f"\n❌ Error: {result.get('error')}")
                print(f"Message: {result.get('message')}")
            elif "results" in result:
                print(f"\n✅ Success! Found {len(result['results'])} results")
                for idx, res in enumerate(result['results']):
                    content = res.get('content', '')
                    score = res.get('score', 0)
                    print(f"\nResult {idx+1} (score: {score:.3f}):")
                    print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print("❌ No result returned")

if __name__ == "__main__":
    test_bedrock_kb()
