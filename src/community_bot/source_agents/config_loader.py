"""Configuration loader for source agents."""

import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from ..logging_config import get_logger
from .agents.database import DatabaseAgent
from .agents.script import ScriptAgent
from .base import SourceAgent
from .registry import AgentRegistry


logger = get_logger("agent_config")


def load_agents_from_config(config_path: Path, registry: AgentRegistry) -> int:
    """
    Load agents from YAML configuration file.
    
    Args:
        config_path: Path to the configuration YAML file
        registry: Agent registry to register agents to
        
    Returns:
        Number of agents registered
    """
    if not YAML_AVAILABLE:
        logger.error("PyYAML is required to load agent configurations. Install with: pip install pyyaml")
        return 0
    
    if not config_path.exists():
        logger.warning(f"Agent configuration file not found: {config_path}")
        return 0
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration file: {e}")
        return 0
    
    if not config or 'agents' not in config:
        logger.warning("No agents defined in configuration file")
        return 0
    
    registered_count = 0
    
    for agent_config in config['agents']:
        try:
            if not agent_config.get('enabled', True):
                logger.info(f"Skipping disabled agent: {agent_config.get('id')}")
                continue
            
            agent = create_agent_from_config(agent_config)
            if agent:
                schedule = agent_config.get('schedule', '0 */6 * * *')
                registry.register(agent, schedule)
                registered_count += 1
                logger.info(f"Registered agent: {agent.agent_id}")
        except Exception as e:
            logger.error(f"Failed to create agent {agent_config.get('id')}: {e}")
    
    return registered_count


def create_agent_from_config(config: Dict[str, Any]) -> SourceAgent:
    """
    Create an agent from configuration dictionary.
    
    Args:
        config: Agent configuration dictionary
        
    Returns:
        Instantiated SourceAgent
    """
    agent_id = config['id']
    agent_type = config['type']
    agent_config = config.get('config', {})
    
    # Replace environment variables in config
    agent_config = _replace_env_vars(agent_config)
    
    if agent_type == 'database':
        return DatabaseAgent(
            agent_id=agent_id,
            connection_string=agent_config['connection_string'],
            query=agent_config['query'],
            category=agent_config.get('category', 'database'),
            id_column=agent_config.get('id_column', 'id'),
            title_column=agent_config.get('title_column'),
            content_columns=agent_config.get('content_columns'),
        )
    
    elif agent_type == 'script':
        return ScriptAgent(
            agent_id=agent_id,
            script_path=Path(agent_config['script_path']),
            category=agent_config.get('category', 'script'),
            script_args=agent_config.get('script_args', []),
        )
    
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def _replace_env_vars(config: Any) -> Any:
    """Recursively replace ${VAR_NAME} with environment variables."""
    if isinstance(config, str):
        # Replace ${VAR_NAME} patterns
        if config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    
    elif isinstance(config, dict):
        return {k: _replace_env_vars(v) for k, v in config.items()}
    
    elif isinstance(config, list):
        return [_replace_env_vars(item) for item in config]
    
    else:
        return config
