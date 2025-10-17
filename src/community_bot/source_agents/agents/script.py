"""Script agent for running custom Python scripts."""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...logging_config import get_logger
from ..base import SourceAgent
from ..document import Document


class ScriptAgent(SourceAgent):
    """Runs a Python script to collect data."""
    
    def __init__(
        self, 
        agent_id: str,
        script_path: Path,
        category: str = "script",
        script_args: Optional[List[str]] = None,
    ):
        """
        Initialize script agent.
        
        Args:
            agent_id: Unique identifier for this agent
            script_path: Path to the Python script
            category: S3 category for documents
            script_args: Additional arguments to pass to the script
        """
        self._agent_id = agent_id
        self.script_path = Path(script_path)
        self.category = category
        self.script_args = script_args or []
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
        cmd = [sys.executable, str(self.script_path)] + self.script_args
        
        self.logger.info(f"Running script: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            self.logger.error(f"Script failed with exit code {process.returncode}: {error_msg}")
            return []
        
        # Parse JSON output from script
        # Expected format: list of {"content": str, "title": str, ...}
        try:
            output = stdout.decode()
            if not output.strip():
                self.logger.warning("Script produced no output")
                return []
            
            data = json.loads(output)
            
            # Handle both single dict and list of dicts
            if isinstance(data, dict):
                data = [data]
            
            documents = []
            
            for item in data:
                doc = Document(
                    content=item.get("content", ""),
                    source_type=self.agent_type,
                    source_id=item.get("id", f"{self.agent_id}_{uuid.uuid4()}"),
                    title=item.get("title"),
                    category=item.get("category", self.category),
                    metadata=item.get("metadata", {}),
                )
                documents.append(doc)
            
            self.logger.info(f"Collected {len(documents)} documents from script")
            return documents
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse script output as JSON: {e}")
            self.logger.debug(f"Script output: {stdout.decode()[:500]}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if script exists and is executable."""
        if not self.script_path.exists():
            return {"healthy": False, "error": "Script not found"}
        
        if not self.script_path.is_file():
            return {"healthy": False, "error": "Script path is not a file"}
        
        # Check if we can read the file
        if not os.access(self.script_path, os.R_OK):
            return {"healthy": False, "error": "Script is not readable"}
        
        return {"healthy": True}
