# Source Agents System Design

## Overview

The Source Agents System is a framework for background processes that continuously collect, process, and upload data to S3 to enrich the Discord bot's knowledge base. These agents run independently from the main bot and feed the AWS Bedrock Knowledge Base with up-to-date information.

## Architecture

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   Source Agents Ecosystem                     │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Database  │  │  Browser   │  │    MCP     │            │
│  │   Agent    │  │   Agent    │  │   Agent    │   ...      │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │               │               │                     │
│        └───────────────┴───────────────┘                     │
│                        │                                      │
│                ┌───────▼────────┐                            │
│                │ Agent Registry │                            │
│                │  & Scheduler   │                            │
│                └───────┬────────┘                            │
│                        │                                      │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   S3 Bucket      │
              │  (Knowledge Data)│
              └─────────┬────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Bedrock KB      │
              │  (Sync & Index)  │
              └─────────┬────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Discord Bot     │
              │  (Query & Reply) │
              └──────────────────┘
```

### Components

#### 1. Base Agent Interface

All source agents implement a common interface:

```python
class SourceAgent(ABC):
    """Base class for all source agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Type of agent (database, browser, mcp, script, etc.)."""
        pass
    
    @abstractmethod
    async def collect(self) -> List[Document]:
        """Collect data and return structured documents."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the agent is healthy and can collect data."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata (schedule, dependencies, etc.)."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "version": "1.0.0",
        }
```

#### 2. Document Model

Standardized data format for collected information:

```python
@dataclass
class Document:
    """Represents a piece of knowledge collected by a source agent."""
    
    # Required fields
    content: str                     # The actual text content
    source_type: str                 # Type: database, web, api, etc.
    source_id: str                   # Unique ID from source system
    
    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    
    # S3 organization
    category: str = "general"        # Folder in S3
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_s3_key(self) -> str:
        """Generate S3 key for this document."""
        date_prefix = self.timestamp.strftime("%Y/%m/%d")
        safe_id = self.source_id.replace("/", "_")
        return f"{self.category}/{date_prefix}/{self.source_type}/{safe_id}.json"
    
    def to_bedrock_format(self) -> Dict[str, Any]:
        """Convert to Bedrock KB compatible format."""
        return {
            "content": self.content,
            "metadata": {
                "source_type": self.source_type,
                "source_id": self.source_id,
                "title": self.title or "",
                "timestamp": self.timestamp.isoformat(),
                "tags": ",".join(self.tags),
                "category": self.category,
                **self.metadata,
            }
        }
```

#### 3. S3 Uploader

Handles uploading documents to S3 with proper formatting:

```python
class S3Uploader:
    """Manages uploading documents to S3 for Bedrock KB ingestion."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
        self.logger = get_logger("s3_uploader")
    
    async def upload_document(self, doc: Document) -> str:
        """Upload a single document to S3."""
        s3_key = doc.to_s3_key()
        
        try:
            # Convert to Bedrock-compatible format
            content = json.dumps(doc.to_bedrock_format(), indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source_type': doc.source_type,
                    'category': doc.category,
                    'timestamp': doc.timestamp.isoformat(),
                }
            )
            
            self.logger.info(f"Uploaded document to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Failed to upload document: {e}")
            raise
    
    async def upload_batch(self, docs: List[Document]) -> List[str]:
        """Upload multiple documents."""
        keys = []
        for doc in docs:
            try:
                key = await self.upload_document(doc)
                keys.append(key)
            except Exception as e:
                self.logger.error(f"Failed to upload {doc.source_id}: {e}")
        return keys
```

#### 4. Agent Registry & Scheduler

Manages registered agents and their execution schedules:

```python
class AgentRegistry:
    """Central registry for all source agents."""
    
    def __init__(self):
        self.agents: Dict[str, SourceAgent] = {}
        self.schedules: Dict[str, str] = {}  # agent_id -> cron expression
        self.logger = get_logger("agent_registry")
    
    def register(
        self, 
        agent: SourceAgent, 
        schedule: str = "0 */6 * * *"  # Default: every 6 hours
    ):
        """Register a new source agent."""
        agent_id = agent.agent_id
        
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} already registered, replacing")
        
        self.agents[agent_id] = agent
        self.schedules[agent_id] = schedule
        self.logger.info(f"Registered agent {agent_id} with schedule {schedule}")
    
    def get_agent(self, agent_id: str) -> Optional[SourceAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their metadata."""
        return [
            {
                **agent.get_metadata(),
                "schedule": self.schedules.get(agent.agent_id),
            }
            for agent in self.agents.values()
        ]


class AgentScheduler:
    """Schedules and executes source agents."""
    
    def __init__(self, registry: AgentRegistry, uploader: S3Uploader):
        self.registry = registry
        self.uploader = uploader
        self.logger = get_logger("agent_scheduler")
        self.running = False
    
    async def run_agent(self, agent_id: str) -> Dict[str, Any]:
        """Execute a single agent collection cycle."""
        agent = self.registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        self.logger.info(f"Running agent {agent_id}")
        start_time = datetime.utcnow()
        
        try:
            # Health check
            health = await agent.health_check()
            if not health.get("healthy", False):
                return {
                    "success": False,
                    "error": "Health check failed",
                    "details": health,
                }
            
            # Collect documents
            documents = await agent.collect()
            self.logger.info(f"Agent {agent_id} collected {len(documents)} documents")
            
            # Upload to S3
            if documents:
                uploaded_keys = await self.uploader.upload_batch(documents)
                self.logger.info(f"Uploaded {len(uploaded_keys)} documents to S3")
            else:
                uploaded_keys = []
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "agent_id": agent_id,
                "documents_collected": len(documents),
                "documents_uploaded": len(uploaded_keys),
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Agent {agent_id} failed: {e}", exc_info=True)
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "timestamp": start_time.isoformat(),
            }
    
    async def start(self):
        """Start the scheduler (background task)."""
        self.running = True
        self.logger.info("Agent scheduler started")
        
        # In production, use APScheduler or similar
        # For now, simple loop
        while self.running:
            for agent_id in self.registry.agents.keys():
                try:
                    result = await self.run_agent(agent_id)
                    self.logger.info(f"Agent {agent_id} result: {result}")
                except Exception as e:
                    self.logger.error(f"Scheduler error for {agent_id}: {e}")
            
            # Wait before next cycle
            await asyncio.sleep(3600)  # 1 hour
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        self.logger.info("Agent scheduler stopped")
```

## Agent Types & Examples

### 1. Database Agent

Collects data from SQL databases:

```python
class DatabaseAgent(SourceAgent):
    """Collects data from a database."""
    
    def __init__(
        self, 
        agent_id: str,
        connection_string: str,
        query: str,
        category: str = "database"
    ):
        self._agent_id = agent_id
        self.connection_string = connection_string
        self.query = query
        self.category = category
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "database"
    
    async def collect(self) -> List[Document]:
        """Execute query and convert results to documents."""
        # Example with asyncpg for PostgreSQL
        conn = await asyncpg.connect(self.connection_string)
        
        try:
            rows = await conn.fetch(self.query)
            documents = []
            
            for row in rows:
                doc = Document(
                    content=self._row_to_text(row),
                    source_type=self.agent_type,
                    source_id=f"{self.agent_id}_{row['id']}",
                    title=row.get('title'),
                    category=self.category,
                    metadata=dict(row),
                )
                documents.append(doc)
            
            return documents
            
        finally:
            await conn.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            conn = await asyncpg.connect(self.connection_string)
            await conn.close()
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _row_to_text(self, row: dict) -> str:
        """Convert database row to readable text."""
        # Customize based on your schema
        return json.dumps(dict(row), indent=2)
```

### 2. Browser Agent

Uses browser automation to collect web data:

```python
class BrowserAgent(SourceAgent):
    """Collects data by browsing websites."""
    
    def __init__(
        self, 
        agent_id: str,
        urls: List[str],
        selectors: Dict[str, str],  # CSS selectors for content
        category: str = "web"
    ):
        self._agent_id = agent_id
        self.urls = urls
        self.selectors = selectors
        self.category = category
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "browser"
    
    async def collect(self) -> List[Document]:
        """Browse websites and extract content."""
        from playwright.async_api import async_playwright
        
        documents = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            for url in self.urls:
                try:
                    await page.goto(url)
                    
                    # Extract content using selectors
                    content_parts = []
                    for name, selector in self.selectors.items():
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            content_parts.append(f"{name}: {text}")
                    
                    content = "\n\n".join(content_parts)
                    
                    doc = Document(
                        content=content,
                        source_type=self.agent_type,
                        source_id=self._url_to_id(url),
                        title=await page.title(),
                        category=self.category,
                        metadata={"url": url},
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    self.logger.error(f"Failed to browse {url}: {e}")
            
            await browser.close()
        
        return documents
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if browser automation is available."""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                await browser.close()
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _url_to_id(self, url: str) -> str:
        """Convert URL to safe ID."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.netloc}_{parsed.path}".replace("/", "_")
```

### 3. MCP (Model Context Protocol) Agent

Integrates with MCP servers to collect structured data:

```python
class MCPAgent(SourceAgent):
    """Collects data from MCP servers."""
    
    def __init__(
        self, 
        agent_id: str,
        mcp_server_url: str,
        resource_patterns: List[str],  # Resource URIs to fetch
        category: str = "mcp"
    ):
        self._agent_id = agent_id
        self.mcp_server_url = mcp_server_url
        self.resource_patterns = resource_patterns
        self.category = category
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "mcp"
    
    async def collect(self) -> List[Document]:
        """Fetch resources from MCP server."""
        # Use MCP client library
        from mcp import ClientSession, StdioServerParameters
        
        documents = []
        
        async with ClientSession(
            StdioServerParameters(
                command="npx",
                args=["-y", f"@modelcontextprotocol/server-{self.agent_id}"],
            )
        ) as session:
            await session.initialize()
            
            # List available resources
            resources = await session.list_resources()
            
            for resource in resources.resources:
                # Check if matches patterns
                if not any(pattern in resource.uri for pattern in self.resource_patterns):
                    continue
                
                # Read resource
                content = await session.read_resource(resource.uri)
                
                doc = Document(
                    content=content.contents[0].text if content.contents else "",
                    source_type=self.agent_type,
                    source_id=resource.uri,
                    title=resource.name or resource.uri,
                    category=self.category,
                    metadata={
                        "uri": resource.uri,
                        "description": resource.description,
                    },
                )
                documents.append(doc)
        
        return documents
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server availability."""
        try:
            # Attempt connection
            from mcp import ClientSession, StdioServerParameters
            async with ClientSession(
                StdioServerParameters(
                    command="npx",
                    args=["-y", f"@modelcontextprotocol/server-{self.agent_id}"],
                )
            ) as session:
                await session.initialize()
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
```

### 4. AI-Powered Strands Agent

Uses Strands framework to intelligently collect and process data:

```python
class StrandsSourceAgent(SourceAgent):
    """AI-powered data collection using Strands agents."""
    
    def __init__(
        self, 
        agent_id: str,
        agent: Agent,  # Strands agent instance
        collection_prompt: str,
        category: str = "ai_generated"
    ):
        self._agent_id = agent_id
        self.agent = agent
        self.collection_prompt = collection_prompt
        self.category = category
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "strands"
    
    async def collect(self) -> List[Document]:
        """Use AI agent to collect and synthesize information."""
        # Invoke the Strands agent
        result = self.agent(self.collection_prompt)
        
        # Parse agent response into documents
        # This depends on how you structure the collection_prompt
        # Example: asking agent to gather information from web/APIs
        
        doc = Document(
            content=result.message,
            source_type=self.agent_type,
            source_id=f"{self.agent_id}_{datetime.utcnow().isoformat()}",
            title=f"AI Collection: {self.agent_id}",
            category=self.category,
            metadata={
                "prompt": self.collection_prompt,
                "model": str(self.agent.llm),
            },
        )
        
        return [doc]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if AI agent is responsive."""
        try:
            test_result = self.agent("Say 'healthy' if you can respond")
            return {"healthy": "healthy" in test_result.message.lower()}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
```

### 5. Simple Script Agent

Wraps any Python script as a source agent:

```python
class ScriptAgent(SourceAgent):
    """Runs a Python script to collect data."""
    
    def __init__(
        self, 
        agent_id: str,
        script_path: Path,
        category: str = "script"
    ):
        self._agent_id = agent_id
        self.script_path = script_path
        self.category = category
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "script"
    
    async def collect(self) -> List[Document]:
        """Execute script and parse output."""
        # Run the script
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(self.script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            self.logger.error(f"Script failed: {stderr.decode()}")
            return []
        
        # Parse JSON output from script
        # Expected format: list of {"content": str, "title": str, ...}
        try:
            data = json.loads(stdout.decode())
            documents = []
            
            for item in data:
                doc = Document(
                    content=item.get("content", ""),
                    source_type=self.agent_type,
                    source_id=item.get("id", f"{self.agent_id}_{uuid.uuid4()}"),
                    title=item.get("title"),
                    category=self.category,
                    metadata=item.get("metadata", {}),
                )
                documents.append(doc)
            
            return documents
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse script output: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if script exists and is executable."""
        if not self.script_path.exists():
            return {"healthy": False, "error": "Script not found"}
        
        if not os.access(self.script_path, os.X_OK):
            return {"healthy": False, "error": "Script not executable"}
        
        return {"healthy": True}
```

## Configuration

### Environment Variables

```bash
# S3 Configuration
SOURCE_AGENTS_S3_BUCKET=my-knowledge-base-bucket
SOURCE_AGENTS_S3_REGION=us-east-1

# Scheduler Configuration
SOURCE_AGENTS_ENABLED=true
SOURCE_AGENTS_RUN_ON_STARTUP=false

# Bedrock KB Sync
SOURCE_AGENTS_AUTO_SYNC_KB=true
SOURCE_AGENTS_SYNC_INTERVAL=3600  # seconds
```

### Agent Configuration File

`agents/sources/config.yaml`:

```yaml
agents:
  - id: "company_database"
    type: "database"
    enabled: true
    schedule: "0 */6 * * *"  # Every 6 hours
    config:
      connection_string: "${DATABASE_URL}"
      query: "SELECT * FROM knowledge_articles WHERE updated_at > NOW() - INTERVAL '6 hours'"
      category: "database/articles"
  
  - id: "documentation_scraper"
    type: "browser"
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2am
    config:
      urls:
        - "https://docs.example.com/api"
        - "https://docs.example.com/guides"
      selectors:
        title: "h1"
        content: "article"
      category: "documentation"
  
  - id: "slack_mcp"
    type: "mcp"
    enabled: true
    schedule: "0 * * * *"  # Hourly
    config:
      mcp_server: "slack"
      resource_patterns:
        - "slack://channels/*/messages"
      category: "slack/messages"
  
  - id: "ai_researcher"
    type: "strands"
    enabled: false
    schedule: "0 8 * * 1"  # Weekly on Monday at 8am
    config:
      model: "bedrock/claude-3-5-sonnet"
      prompt: "Research the latest developments in AI and summarize key findings"
      category: "research/ai"
  
  - id: "custom_collector"
    type: "script"
    enabled: true
    schedule: "*/30 * * * *"  # Every 30 minutes
    config:
      script_path: "./agents/sources/scripts/custom_collector.py"
      category: "custom"
```

## Integration with Existing Bot

### 1. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Infrastructure                      │
│                                                              │
│  ┌──────────────────┐                                       │
│  │   Discord Bot    │ (existing)                            │
│  │   (EC2/ECS)      │                                       │
│  └────────┬─────────┘                                       │
│           │ queries                                          │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │  Bedrock KB      │                                       │
│  └────────┬─────────┘                                       │
│           ▲ syncs from                                       │
│           │                                                  │
│  ┌────────┴─────────┐                                       │
│  │   S3 Bucket      │                                       │
│  │  (kb-documents)  │                                       │
│  └────────▲─────────┘                                       │
│           │ uploads                                          │
│           │                                                  │
│  ┌────────┴──────────┐                                      │
│  │ Source Agents     │ (new)                                │
│  │ (Lambda/ECS)      │                                      │
│  └───────────────────┘                                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2. Project Structure

```
mike-et-al-community-bot/
├── src/
│   └── community_bot/
│       ├── discord_bot.py          # Existing bot
│       ├── agentcore_app.py        # Existing agent
│       └── source_agents/          # NEW
│           ├── __init__.py
│           ├── base.py             # SourceAgent base class
│           ├── document.py         # Document model
│           ├── uploader.py         # S3Uploader
│           ├── registry.py         # AgentRegistry
│           ├── scheduler.py        # AgentScheduler
│           └── agents/             # Specific agent implementations
│               ├── database.py
│               ├── browser.py
│               ├── mcp.py
│               ├── strands.py
│               └── script.py
├── agents/
│   └── sources/
│       ├── config.yaml            # Agent configurations
│       └── scripts/               # Custom scripts
│           └── example_collector.py
├── tests/
│   └── test_source_agents.py
└── scripts/
    ├── run_source_agents.py       # Main entry point
    └── deploy_source_agents.sh    # Deployment script
```

### 3. Main Entry Point

`scripts/run_source_agents.py`:

```python
#!/usr/bin/env python3
"""
Main entry point for source agents system.
Can be run as a standalone service or deployed to AWS Lambda/ECS.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from community_bot.source_agents.registry import AgentRegistry
from community_bot.source_agents.scheduler import AgentScheduler
from community_bot.source_agents.uploader import S3Uploader
from community_bot.source_agents.agents.database import DatabaseAgent
from community_bot.source_agents.agents.browser import BrowserAgent
from community_bot.source_agents.agents.mcp import MCPAgent
from community_bot.config import load_settings

async def main():
    """Initialize and run source agents."""
    settings = load_settings()
    
    # Initialize components
    uploader = S3Uploader(
        bucket_name=os.getenv("SOURCE_AGENTS_S3_BUCKET"),
        region=settings.aws_region,
    )
    
    registry = AgentRegistry()
    scheduler = AgentScheduler(registry, uploader)
    
    # Load agents from config
    # (In production, load from YAML file)
    
    # Example: Register a database agent
    if os.getenv("DATABASE_AGENT_ENABLED") == "true":
        db_agent = DatabaseAgent(
            agent_id="company_database",
            connection_string=os.getenv("DATABASE_URL"),
            query=os.getenv("DATABASE_QUERY"),
        )
        registry.register(db_agent, schedule="0 */6 * * *")
    
    # Start scheduler
    await scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## Deployment Options

### Option 1: AWS Lambda (Serverless)

For lightweight, periodic collection:

- Deploy each agent as a separate Lambda function
- Use EventBridge (CloudWatch Events) for scheduling
- Lambda writes directly to S3
- Cost-effective for infrequent collection

### Option 2: ECS Task (Long-Running)

For continuous or complex collection:

- Run scheduler as ECS Fargate task
- Supports long-running agents (web scraping, streaming)
- Better for agents that need persistent connections
- More control over resources

### Option 3: EC2 Instance (Same as Discord Bot)

For simplicity:

- Run source agents on same instance as Discord bot
- Separate systemd service or background process
- Easy to manage, share environment
- Good for development/testing

## Bedrock Knowledge Base Sync

### Automatic Sync Process

```python
class BedrockKBSyncer:
    """Triggers Bedrock KB sync after S3 uploads."""
    
    def __init__(self, knowledge_base_id: str, region: str):
        self.kb_id = knowledge_base_id
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=region
        )
        self.logger = get_logger("kb_syncer")
    
    async def trigger_sync(self):
        """Trigger KB ingestion job."""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=self._get_data_source_id(),
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            self.logger.info(f"Started KB sync job: {job_id}")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to trigger sync: {e}")
            raise
    
    def _get_data_source_id(self) -> str:
        """Get the S3 data source ID for the KB."""
        response = self.bedrock_agent.list_data_sources(
            knowledgeBaseId=self.kb_id
        )
        
        # Assuming first data source is our S3 bucket
        return response['dataSourceSummaries'][0]['dataSourceId']
```

## Monitoring & Observability

### Metrics to Track

```python
@dataclass
class AgentMetrics:
    """Metrics for agent execution."""
    
    agent_id: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_documents: int = 0
    total_bytes_uploaded: int = 0
    avg_duration_seconds: float = 0.0
    last_execution: Optional[datetime] = None
    last_error: Optional[str] = None
```

### CloudWatch Integration

```python
class MetricsPublisher:
    """Publish metrics to CloudWatch."""
    
    def __init__(self, namespace: str = "SourceAgents"):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
    
    def publish_execution(self, result: Dict[str, Any]):
        """Publish agent execution metrics."""
        metrics = []
        
        # Success/failure
        metrics.append({
            'MetricName': 'ExecutionSuccess',
            'Value': 1 if result['success'] else 0,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'AgentId', 'Value': result['agent_id']}
            ],
        })
        
        # Documents collected
        if result.get('documents_collected'):
            metrics.append({
                'MetricName': 'DocumentsCollected',
                'Value': result['documents_collected'],
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'AgentId', 'Value': result['agent_id']}
                ],
            })
        
        # Duration
        if result.get('duration_seconds'):
            metrics.append({
                'MetricName': 'ExecutionDuration',
                'Value': result['duration_seconds'],
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'AgentId', 'Value': result['agent_id']}
                ],
            })
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=metrics
        )
```

## Testing

### Unit Tests

```python
# tests/test_source_agents.py

import pytest
from community_bot.source_agents.document import Document
from community_bot.source_agents.registry import AgentRegistry

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

def test_agent_registry():
    """Test agent registration."""
    registry = AgentRegistry()
    
    # Mock agent
    class TestAgent(SourceAgent):
        @property
        def agent_id(self): return "test"
        @property
        def agent_type(self): return "test"
        async def collect(self): return []
        async def health_check(self): return {"healthy": True}
    
    agent = TestAgent()
    registry.register(agent, schedule="* * * * *")
    
    assert registry.get_agent("test") == agent
    assert len(registry.list_agents()) == 1
```

### Integration Tests

```python
@pytest.mark.integration
async def test_database_agent_collection():
    """Test database agent can collect data."""
    agent = DatabaseAgent(
        agent_id="test_db",
        connection_string=os.getenv("TEST_DATABASE_URL"),
        query="SELECT * FROM test_table LIMIT 10",
    )
    
    # Health check
    health = await agent.health_check()
    assert health["healthy"]
    
    # Collect
    docs = await agent.collect()
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
```

## Security Considerations

### 1. Credentials Management

- Use AWS Secrets Manager for database credentials
- Use IAM roles instead of access keys where possible
- Rotate credentials regularly

### 2. S3 Bucket Security

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSourceAgentsUpload",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/SourceAgentsRole"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::kb-bucket/*"
    },
    {
      "Sid": "AllowBedrockKBRead",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::kb-bucket",
        "arn:aws:s3:::kb-bucket/*"
      ]
    }
  ]
}
```

### 3. Network Security

- Run agents in private subnets
- Use VPC endpoints for AWS services
- Restrict outbound traffic to necessary services

## Migration Path

### Phase 1: Infrastructure Setup (Week 1)

- [ ] Create S3 bucket for knowledge documents
- [ ] Set up IAM roles and policies
- [ ] Configure Bedrock KB to sync from S3

### Phase 2: Core Framework (Week 2)

- [ ] Implement base SourceAgent interface
- [ ] Implement Document model
- [ ] Implement S3Uploader
- [ ] Implement AgentRegistry and Scheduler
- [ ] Add configuration loading

### Phase 3: Agent Implementations (Week 3-4)

- [ ] Implement DatabaseAgent
- [ ] Implement BrowserAgent
- [ ] Implement ScriptAgent
- [ ] Implement MCPAgent (optional)
- [ ] Implement StrandsAgent (optional)

### Phase 4: Integration & Testing (Week 5)

- [ ] Integration tests with real S3
- [ ] Integration tests with Bedrock KB
- [ ] End-to-end testing with Discord bot
- [ ] Performance testing

### Phase 5: Deployment (Week 6)

- [ ] Deploy to AWS (Lambda or ECS)
- [ ] Set up monitoring and alerting
- [ ] Configure scheduled runs
- [ ] Documentation and runbooks

## Future Enhancements

### 1. Agent Marketplace

Allow community to contribute custom agents:

```python
# agents/marketplace/reddit_agent.py
class RedditAgent(SourceAgent):
    """Collects posts from specific subreddits."""
    # Implementation...
```

### 2. Real-Time Streaming

For high-velocity data sources:

```python
class StreamingAgent(SourceAgent):
    """Continuously streams data to S3."""
    
    async def stream(self):
        """Stream data continuously instead of batch collection."""
        while True:
            event = await self.fetch_next_event()
            doc = self.event_to_document(event)
            await self.uploader.upload_document(doc)
```

### 3. Smart Deduplication

Avoid uploading duplicate content:

```python
class DeduplicatingUploader(S3Uploader):
    """Checks for duplicates before uploading."""
    
    async def upload_document(self, doc: Document) -> Optional[str]:
        content_hash = self._hash_content(doc.content)
        
        # Check if hash exists in DynamoDB
        if await self._content_exists(content_hash):
            self.logger.info(f"Skipping duplicate: {doc.source_id}")
            return None
        
        # Upload and record hash
        key = await super().upload_document(doc)
        await self._record_hash(content_hash, key)
        return key
```

### 4. Content Enrichment

Use AI to enhance collected content:

```python
class ContentEnricher:
    """Enriches documents with AI-generated metadata."""
    
    def __init__(self, agent: Agent):
        self.agent = agent
    
    async def enrich(self, doc: Document) -> Document:
        """Add AI-generated tags, summary, etc."""
        prompt = f"Analyze this content and provide: 1) 5 relevant tags, 2) 2-sentence summary\n\n{doc.content}"
        result = self.agent(prompt)
        
        # Parse AI response and update document
        doc.tags.extend(self._extract_tags(result.message))
        doc.metadata['summary'] = self._extract_summary(result.message)
        
        return doc
```

## Conclusion

The Source Agents System provides a flexible, extensible framework for continuously enriching the Discord bot's knowledge base. By supporting multiple agent types (database, browser, MCP, AI-powered, and scripts), the system can collect data from diverse sources and make it available through the existing Bedrock Knowledge Base integration.

Key benefits:

- **Automated Knowledge Collection**: Runs in background without manual intervention
- **Flexible Architecture**: Easy to add new agent types
- **AWS Integration**: Works seamlessly with existing Bedrock KB setup
- **Observable**: Built-in metrics and monitoring
- **Scalable**: Can deploy as serverless or long-running services

The system is designed to complement the existing Discord bot, not replace it, creating a complete knowledge management pipeline from data collection to user interaction.
