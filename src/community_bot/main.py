from __future__ import annotations

import asyncio

from .config import load_settings
from .agent_client import AgentClient
from .discord_bot import CommunityBot


def run():
    settings = load_settings()
    agent_client = AgentClient(settings)
    bot = CommunityBot(settings, agent_client)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    run()
