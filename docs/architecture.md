# Architecture

This document describes the architecture of the Mike et al Community Bot.

## Overview

The community bot is a Python application that connects to Discord and responds to messages in a designated channel. It uses a configurable backend to generate responses, which can be either a local Ollama model or an AWS Bedrock Agent.

The application is designed to be simple to run and configure, with all settings managed through a `.env` file.

## Components

The system is composed of three main components:

1.  **Discord Bot (`discord_bot.py`)**: This is the main entry point for the application. It uses the `discord.py` library to connect to the Discord API and listen for messages. When a message is received in the configured channel, it passes the message content to the Agent Client.

2.  **Agent Client (`agent_client.py`)**: This component acts as a bridge between the Discord bot and the AI backend. It has two modes of operation:
    *   **Ollama Mode**: It sends the user's message to a local Ollama instance using an HTTP request and streams the response back.
    *   **AgentCore Mode**: It uses the `boto3` library to invoke an AWS Bedrock Agent and returns the agent's response.

3.  **Configuration (`config.py`)**: This module is responsible for loading and validating the application's configuration from a `.env` file. It ensures that all necessary settings are present for the selected backend mode.

## Data Flow

1.  A user sends a message in the configured Discord channel.
2.  The `CommunityBot` instance receives the message.
3.  The bot calls the `AgentClient.chat()` method with the message content.
4.  The `AgentClient` determines which backend to use based on the `BACKEND_MODE` setting.
5.  It calls the appropriate backend (Ollama or AWS Bedrock Agent).
6.  The backend processes the message and returns a response.
7.  The `AgentClient` returns the response to the `CommunityBot`.
8.  The `CommunityBot` sends the response back to the Discord channel.

## Simplifications from Initial Plan

The current architecture is a simplified version of the one described in `docs/plan/initial-dev.md`. The key simplifications are:

*   **No API Gateway or Lambda**: The bot is a standalone Python application, not a serverless function. This makes it easier to run and debug locally.
*   **Generic Bedrock Agent Interaction**: The bot interacts with the Bedrock Agent using the standard `boto3` library, rather than any "Strands" specific SDKs. This makes the bot more generic and compatible with any Bedrock Agent.
