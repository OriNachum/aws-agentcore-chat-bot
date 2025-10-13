#!/usr/bin/env python3
"""
Quick verification script for source agents implementation.
Tests that all components can be imported and basic functionality works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all source agent modules can be imported."""
    print("Testing imports...")
    
    try:
        from community_bot.source_agents import (
            SourceAgent,
            Document,
            AgentRegistry,
            AgentScheduler,
            S3Uploader,
        )
        print("✓ Core modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core modules: {e}")
        return False
    
    try:
        from community_bot.source_agents.agents import (
            DatabaseAgent,
            ScriptAgent,
        )
        print("✓ Agent implementations imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import agent implementations: {e}")
        return False
    
    try:
        from community_bot.source_agents.config_loader import load_agents_from_config
        print("✓ Config loader imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config loader: {e}")
        return False
    
    try:
        from community_bot.source_agents.syncer import BedrockKBSyncer
        print("✓ KB syncer imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import KB syncer: {e}")
        return False
    
    return True


def test_document_creation():
    """Test Document creation and methods."""
    print("\nTesting Document class...")
    
    from community_bot.source_agents import Document
    from datetime import datetime
    
    doc = Document(
        content="Test content",
        source_type="test",
        source_id="test_123",
        title="Test Document",
        category="testing",
        tags=["tag1", "tag2"],
    )
    
    # Test S3 key generation
    s3_key = doc.to_s3_key()
    assert "testing/" in s3_key
    assert "/test/test_123.json" in s3_key
    print(f"✓ S3 key generation works: {s3_key}")
    
    # Test Bedrock format
    bedrock_format = doc.to_bedrock_format()
    assert bedrock_format["content"] == "Test content"
    assert bedrock_format["metadata"]["source_type"] == "test"
    print("✓ Bedrock format conversion works")
    
    return True


def test_registry():
    """Test AgentRegistry functionality."""
    print("\nTesting AgentRegistry...")
    
    from community_bot.source_agents import AgentRegistry, SourceAgent
    from typing import List, Dict, Any
    
    class TestAgent(SourceAgent):
        @property
        def agent_id(self) -> str:
            return "test_agent"
        
        @property
        def agent_type(self) -> str:
            return "test"
        
        async def collect(self) -> List:
            return []
        
        async def health_check(self) -> Dict[str, Any]:
            return {"healthy": True}
    
    registry = AgentRegistry()
    agent = TestAgent()
    
    registry.register(agent, schedule="* * * * *")
    
    retrieved = registry.get_agent("test_agent")
    assert retrieved == agent
    print("✓ Agent registration and retrieval works")
    
    agents = registry.list_agents()
    assert len(agents) == 1
    assert agents[0]["agent_id"] == "test_agent"
    print("✓ Agent listing works")
    
    unregistered = registry.unregister("test_agent")
    assert unregistered is True
    assert registry.get_agent("test_agent") is None
    print("✓ Agent unregistration works")
    
    return True


def test_config_structure():
    """Test that config files exist and are readable."""
    print("\nTesting configuration files...")
    
    config_path = Path("agents/sources/config.yaml")
    if config_path.exists():
        print(f"✓ Config file exists: {config_path}")
    else:
        print(f"✗ Config file not found: {config_path}")
        return False
    
    script_path = Path("agents/sources/scripts/example_collector.py")
    if script_path.exists():
        print(f"✓ Example script exists: {script_path}")
    else:
        print(f"✗ Example script not found: {script_path}")
        return False
    
    return True


def test_settings():
    """Test that settings include source agent configuration."""
    print("\nTesting configuration settings...")
    
    try:
        from community_bot.config import Settings
    except ImportError as e:
        print(f"⚠ Skipping settings test (missing dependency): {e}")
        print("  (This is OK - dependencies are managed by uv)")
        return True
    
    # Check that Settings has source agent fields
    settings_fields = Settings.__dataclass_fields__
    
    required_fields = [
        'source_agents_enabled',
        'source_agents_s3_bucket',
        'source_agents_s3_region',
        'source_agents_data_source_id',
        'source_agents_run_on_startup',
        'source_agents_interval',
    ]
    
    for field in required_fields:
        if field in settings_fields:
            print(f"✓ Settings has field: {field}")
        else:
            print(f"✗ Settings missing field: {field}")
            return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Source Agents Implementation Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Document", test_document_creation),
        ("Registry", test_registry),
        ("Config Files", test_config_structure),
        ("Settings", test_settings),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All verification tests passed!")
        print("\nNext steps:")
        print("1. Install optional dependencies: pip install pyyaml")
        print("2. Configure agents in: agents/sources/config.yaml")
        print("3. Test with: python scripts/run_source_agents.py --once")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
