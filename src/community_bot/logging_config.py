"""Logging configuration for the community bot."""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Set up logging configuration for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, defaults to INFO
    """
    log_level = level or "INFO"
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("discord").setLevel(logging.WARNING)  # Reduce discord.py noise
    logging.getLogger("aiohttp").setLevel(logging.WARNING)  # Reduce aiohttp noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce boto3 noise
    
    # Create application-specific loggers
    app_logger = logging.getLogger("community_bot")
    app_logger.setLevel(numeric_level)
    
    discord_logger = logging.getLogger("community_bot.discord")
    discord_logger.setLevel(numeric_level)
    
    agent_logger = logging.getLogger("community_bot.agent")
    agent_logger.setLevel(numeric_level)
    
    model_logger = logging.getLogger("community_bot.model")
    model_logger.setLevel(numeric_level)
    
    memory_logger = logging.getLogger("community_bot.memory")
    memory_logger.setLevel(numeric_level)
    
    # Log the setup completion
    app_logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)