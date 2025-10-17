"""Document model for knowledge base content."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


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
        safe_id = self.source_id.replace("/", "_").replace("\\", "_")
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
