"""Database agent for collecting data from SQL databases."""

import json
from typing import Any, Dict, List, Optional

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from ...logging_config import get_logger
from ..base import SourceAgent
from ..document import Document


class DatabaseAgent(SourceAgent):
    """Collects data from a database."""
    
    def __init__(
        self, 
        agent_id: str,
        connection_string: str,
        query: str,
        category: str = "database",
        id_column: str = "id",
        title_column: Optional[str] = None,
        content_columns: Optional[List[str]] = None,
    ):
        """
        Initialize database agent.
        
        Args:
            agent_id: Unique identifier for this agent
            connection_string: Database connection string
            query: SQL query to execute
            category: S3 category for documents
            id_column: Column to use as source_id
            title_column: Column to use as title (optional)
            content_columns: Columns to include in content (all if None)
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for DatabaseAgent. Install with: pip install asyncpg"
            )
        
        self._agent_id = agent_id
        self.connection_string = connection_string
        self.query = query
        self.category = category
        self.id_column = id_column
        self.title_column = title_column
        self.content_columns = content_columns
        self.logger = get_logger(f"agent.{agent_id}")
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> str:
        return "database"
    
    async def collect(self) -> List[Document]:
        """Execute query and convert results to documents."""
        conn = await asyncpg.connect(self.connection_string)
        
        try:
            rows = await conn.fetch(self.query)
            documents = []
            
            for row in rows:
                row_dict = dict(row)
                
                # Generate content
                if self.content_columns:
                    content_dict = {k: row_dict[k] for k in self.content_columns if k in row_dict}
                else:
                    content_dict = row_dict
                
                content = self._row_to_text(content_dict)
                
                # Get ID
                source_id = f"{self.agent_id}_{row_dict.get(self.id_column, 'unknown')}"
                
                # Get title
                title = None
                if self.title_column and self.title_column in row_dict:
                    title = str(row_dict[self.title_column])
                
                doc = Document(
                    content=content,
                    source_type=self.agent_type,
                    source_id=source_id,
                    title=title,
                    category=self.category,
                    metadata=row_dict,
                )
                documents.append(doc)
            
            self.logger.info(f"Collected {len(documents)} documents from database")
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
        return json.dumps(row, indent=2, default=str)
