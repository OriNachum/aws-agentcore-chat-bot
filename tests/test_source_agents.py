"""Tests for source agents system."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest

from community_bot.source_agents import (
    SourceAgent,
    Document,
    AgentRegistry,
    AgentScheduler,
)
from community_bot.source_agents.agents.script import ScriptAgent


class MockAgent(SourceAgent):
    """Mock agent for testing."""
    
    def __init__(self, agent_id: str, should_fail: bool = False):
        self._agent_id = agent_id
        self.should_fail = should_fail
        self.collect_called = False
        self.health_check_called = False
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "mock"
    
    async def collect(self):
        self.collect_called = True
        if self.should_fail:
            raise Exception("Mock collection failure")
        
        return [
            Document(
                content="Test content",
                source_type=self.agent_type,
                source_id=f"{self.agent_id}_1",
                title="Test Document",
                category="test",
            )
        ]
    
    async def health_check(self):
        self.health_check_called = True
        return {"healthy": not self.should_fail}


class MockUploader:
    """Mock S3 uploader for testing."""
    
    def __init__(self):
        self.uploaded_docs = []
    
    async def upload_document(self, doc: Document):
        self.uploaded_docs.append(doc)
        return doc.to_s3_key()
    
    async def upload_batch(self, docs):
        keys = []
        for doc in docs:
            key = await self.upload_document(doc)
            keys.append(key)
        return keys


def test_document_to_s3_key():
    """Test S3 key generation."""
    doc = Document(
        content="Test content",
        source_type="test",
        source_id="123",
        category="testing",
    )
    
    key = doc.to_s3_key()
    assert key.startswith("testing/")
    assert "/test/123.json" in key


def test_document_to_bedrock_format():
    """Test Bedrock format conversion."""
    doc = Document(
        content="Test content",
        source_type="test",
        source_id="123",
        title="Test Title",
        category="testing",
        tags=["tag1", "tag2"],
        metadata={"custom": "value"},
    )
    
    bedrock_format = doc.to_bedrock_format()
    assert bedrock_format["content"] == "Test content"
    assert bedrock_format["metadata"]["source_type"] == "test"
    assert bedrock_format["metadata"]["title"] == "Test Title"
    assert bedrock_format["metadata"]["tags"] == "tag1,tag2"
    assert bedrock_format["metadata"]["custom"] == "value"


def test_agent_registry():
    """Test agent registration."""
    registry = AgentRegistry()
    
    agent = MockAgent("test_agent")
    registry.register(agent, schedule="* * * * *")
    
    assert registry.get_agent("test_agent") == agent
    
    agents = registry.list_agents()
    assert len(agents) == 1
    assert agents[0]["agent_id"] == "test_agent"
    assert agents[0]["schedule"] == "* * * * *"


def test_agent_registry_unregister():
    """Test agent unregistration."""
    registry = AgentRegistry()
    
    agent = MockAgent("test_agent")
    registry.register(agent)
    
    assert registry.unregister("test_agent") is True
    assert registry.get_agent("test_agent") is None
    assert registry.unregister("nonexistent") is False


@pytest.mark.asyncio
async def test_scheduler_run_agent_success():
    """Test running a successful agent."""
    registry = AgentRegistry()
    uploader = MockUploader()
    scheduler = AgentScheduler(registry, uploader)
    
    agent = MockAgent("test_agent")
    registry.register(agent)
    
    result = await scheduler.run_agent("test_agent")
    
    assert result["success"] is True
    assert result["agent_id"] == "test_agent"
    assert result["documents_collected"] == 1
    assert result["documents_uploaded"] == 1
    assert agent.collect_called
    assert agent.health_check_called
    assert len(uploader.uploaded_docs) == 1


@pytest.mark.asyncio
async def test_scheduler_run_agent_failure():
    """Test running a failing agent."""
    registry = AgentRegistry()
    uploader = MockUploader()
    scheduler = AgentScheduler(registry, uploader)
    
    agent = MockAgent("failing_agent", should_fail=True)
    registry.register(agent)
    
    result = await scheduler.run_agent("failing_agent")
    
    assert result["success"] is False
    assert result["agent_id"] == "failing_agent"
    assert "error" in result
    assert agent.health_check_called


@pytest.mark.asyncio
async def test_scheduler_run_all_agents():
    """Test running all agents."""
    registry = AgentRegistry()
    uploader = MockUploader()
    scheduler = AgentScheduler(registry, uploader)
    
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    registry.register(agent1)
    registry.register(agent2)
    
    results = await scheduler.run_all_agents()
    
    assert len(results) == 2
    assert all(r["success"] for r in results)
    assert len(uploader.uploaded_docs) == 2


@pytest.mark.asyncio
async def test_script_agent(tmp_path):
    """Test script agent execution."""
    # Create a test script
    script_path = tmp_path / "test_script.py"
    script_content = """
import json
import sys

documents = [
    {
        "content": "Test document from script",
        "id": "script_1",
        "title": "Script Test"
    }
]

print(json.dumps(documents))
sys.exit(0)
"""
    script_path.write_text(script_content)
    
    # Create agent
    agent = ScriptAgent(
        agent_id="test_script",
        script_path=script_path,
        category="test",
    )
    
    # Health check
    health = await agent.health_check()
    assert health["healthy"] is True
    
    # Collect
    docs = await agent.collect()
    assert len(docs) == 1
    assert docs[0].content == "Test document from script"
    assert docs[0].source_id == "script_1"
    assert docs[0].title == "Script Test"


@pytest.mark.asyncio
async def test_script_agent_error(tmp_path):
    """Test script agent with failing script."""
    # Create a failing script
    script_path = tmp_path / "failing_script.py"
    script_content = """
import sys
print("Error message", file=sys.stderr)
sys.exit(1)
"""
    script_path.write_text(script_content)
    
    agent = ScriptAgent(
        agent_id="failing_script",
        script_path=script_path,
    )
    
    docs = await agent.collect()
    assert len(docs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
