#!/usr/bin/env python3
"""
Main entry point for source agents system.

This script can be run standalone or integrated with the Discord bot.
It loads agent configurations, registers agents, and runs them on a schedule.

Usage:
    python scripts/run_source_agents.py              # Run with default config
    python scripts/run_source_agents.py --once        # Run once and exit
    python scripts/run_source_agents.py --agent-id example_collector  # Run specific agent
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from community_bot.config import load_settings
from community_bot.logging_config import setup_logging, get_logger
from community_bot.source_agents import (
    AgentRegistry,
    AgentScheduler,
    S3Uploader,
)
from community_bot.source_agents.config_loader import load_agents_from_config
from community_bot.source_agents.syncer import BedrockKBSyncer


async def main(args):
    """Initialize and run source agents."""
    settings = load_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    logger = get_logger("source_agents_main")
    
    # Check if source agents are enabled
    if not settings.source_agents_enabled:
        logger.error("Source agents are not enabled. Set SOURCE_AGENTS_ENABLED=true")
        return 1
    
    # Validate required settings
    if not settings.source_agents_s3_bucket:
        logger.error("SOURCE_AGENTS_S3_BUCKET is required")
        return 1
    
    logger.info("Initializing source agents system")
    
    # Initialize components
    uploader = S3Uploader(
        bucket_name=settings.source_agents_s3_bucket,
        region=settings.source_agents_s3_region,
    )
    
    registry = AgentRegistry()
    scheduler = AgentScheduler(registry, uploader)
    
    # Load agents from config
    config_path = Path("agents/sources/config.yaml")
    if args.config:
        config_path = Path(args.config)
    
    registered_count = load_agents_from_config(config_path, registry)
    logger.info(f"Registered {registered_count} agents")
    
    if registered_count == 0:
        logger.warning("No agents registered, exiting")
        return 0
    
    # Run mode
    if args.once:
        # Run all agents once and exit
        logger.info("Running all agents once")
        results = await scheduler.run_all_agents()
        
        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Completed: {successful}/{len(results)} agents succeeded")
        
        # Trigger KB sync if configured
        if settings.knowledge_base_id and settings.source_agents_data_source_id:
            syncer = BedrockKBSyncer(
                knowledge_base_id=settings.knowledge_base_id,
                data_source_id=settings.source_agents_data_source_id,
                region=settings.aws_region or settings.source_agents_s3_region,
            )
            job_id = await syncer.trigger_sync()
            logger.info(f"Triggered KB sync job: {job_id}")
        
        return 0 if successful == len(results) else 1
    
    elif args.agent_id:
        # Run specific agent once
        logger.info(f"Running agent: {args.agent_id}")
        result = await scheduler.run_agent(args.agent_id)
        
        if result["success"]:
            logger.info(f"Agent succeeded: {result}")
            return 0
        else:
            logger.error(f"Agent failed: {result}")
            return 1
    
    else:
        # Run scheduler continuously
        logger.info(f"Starting scheduler with interval {settings.source_agents_interval}s")
        
        try:
            await scheduler.start(interval_seconds=settings.source_agents_interval)
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        finally:
            await scheduler.stop()
            logger.info("Scheduler stopped")
        
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run source agents for knowledge base updates")
    parser.add_argument("--once", action="store_true", help="Run all agents once and exit")
    parser.add_argument("--agent-id", type=str, help="Run specific agent by ID")
    parser.add_argument("--config", type=str, help="Path to agent configuration file")
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)
