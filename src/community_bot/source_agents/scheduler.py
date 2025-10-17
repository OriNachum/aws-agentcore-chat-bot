"""Schedules and executes source agents."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from ..logging_config import get_logger
from .registry import AgentRegistry
from .uploader import S3Uploader


class AgentScheduler:
    """Schedules and executes source agents."""
    
    def __init__(self, registry: AgentRegistry, uploader: S3Uploader):
        self.registry = registry
        self.uploader = uploader
        self.logger = get_logger("agent_scheduler")
        self.running = False
        self._task = None
    
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
                    "agent_id": agent_id,
                    "error": "Health check failed",
                    "details": health,
                    "timestamp": start_time.isoformat(),
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
            duration = (datetime.utcnow() - start_time).total_seconds()
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
            }
    
    async def run_all_agents(self) -> List[Dict[str, Any]]:
        """Run all registered agents."""
        results = []
        for agent_id in self.registry.agents.keys():
            try:
                result = await self.run_agent(agent_id)
                results.append(result)
                self.logger.info(f"Agent {agent_id} result: {result}")
            except Exception as e:
                self.logger.error(f"Scheduler error for {agent_id}: {e}")
                results.append({
                    "success": False,
                    "agent_id": agent_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return results
    
    async def _scheduler_loop(self, interval_seconds: int = 3600):
        """Main scheduler loop."""
        self.logger.info(f"Scheduler loop started with interval {interval_seconds}s")
        
        while self.running:
            try:
                results = await self.run_all_agents()
                successful = sum(1 for r in results if r.get("success"))
                self.logger.info(
                    f"Scheduler cycle complete: {successful}/{len(results)} agents succeeded"
                )
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}", exc_info=True)
            
            # Wait before next cycle
            await asyncio.sleep(interval_seconds)
    
    async def start(self, interval_seconds: int = 3600):
        """Start the scheduler (background task)."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.logger.info("Agent scheduler started")
        self._task = asyncio.create_task(self._scheduler_loop(interval_seconds))
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Agent scheduler stopped")
