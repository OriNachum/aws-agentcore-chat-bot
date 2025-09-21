from __future__ import annotations

import asyncio

from .config import load_settings
from .agent_client import AgentClient
from .discord_bot import CommunityBot
from .logging_config import setup_logging, get_logger


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
    
    try:
        logger.info("Initializing agent client")
        agent_client = AgentClient(settings)
        
        logger.info("Initializing Discord bot")
        bot = CommunityBot(settings, agent_client)
        
        logger.info("Starting Discord bot...")
        bot.run(settings.discord_token)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()
