from __future__ import annotations

import asyncio
from pathlib import Path

from .config import load_settings
from .agent_client import AgentClient
from .discord_bot import CommunityBot
from .logging_config import setup_logging, get_logger


async def start_source_agents(settings):
    """Start source agents if enabled."""
    if not settings.source_agents_enabled:
        return None
    
    logger = get_logger("source_agents")
    logger.info("Source agents enabled, starting background collection")
    
    try:
        from .source_agents import AgentRegistry, AgentScheduler, S3Uploader
        from .source_agents.config_loader import load_agents_from_config
        
        # Initialize components
        uploader = S3Uploader(
            bucket_name=settings.source_agents_s3_bucket,
            region=settings.source_agents_s3_region,
        )
        
        registry = AgentRegistry()
        scheduler = AgentScheduler(registry, uploader)
        
        # Load agents from config
        config_path = Path("agents/sources/config.yaml")
        registered_count = load_agents_from_config(config_path, registry)
        logger.info(f"Registered {registered_count} source agents")
        
        if registered_count > 0:
            # Run once on startup if configured
            if settings.source_agents_run_on_startup:
                logger.info("Running source agents on startup")
                await scheduler.run_all_agents()
            
            # Start background scheduler
            await scheduler.start(interval_seconds=settings.source_agents_interval)
            logger.info(f"Source agents scheduler started (interval: {settings.source_agents_interval}s)")
            return scheduler
        else:
            logger.warning("No source agents registered")
            return None
            
    except Exception as e:
        logger.error(f"Failed to start source agents: {e}", exc_info=True)
        return None


def run():
    # Load settings first
    settings = load_settings()
    
    # Setup logging with configured level
    setup_logging(settings.log_level)
    logger = get_logger("community_bot.main")
    
    logger.info("="*50)
    logger.info("Starting Community Bot")
    logger.info("="*50)
    logger.info(f"Backend mode: {settings.backend_mode}")
    logger.info(f"Discord channel ID: {settings.discord_channel_id}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Source agents enabled: {settings.source_agents_enabled}")
    
    # Store scheduler reference for cleanup
    scheduler = None
    
    try:
        logger.info("Initializing agent client")
        agent_client = AgentClient(settings)
        
        logger.info("Initializing Discord bot")
        bot = CommunityBot(settings, agent_client)
        
        # Start source agents in background if enabled
        if settings.source_agents_enabled:
            async def setup_hook():
                nonlocal scheduler
                scheduler = await start_source_agents(settings)
            
            bot.setup_hook = setup_hook
        
        logger.info("Starting Discord bot...")
        bot.run(settings.discord_token)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup source agents
        if scheduler:
            logger.info("Stopping source agents scheduler")
            asyncio.run(scheduler.stop())


if __name__ == "__main__":
    run()
