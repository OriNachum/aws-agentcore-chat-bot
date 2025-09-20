# Plan: Ollama-centric Agent Architecture

This document outlines the plan to refactor the application to use Ollama as the primary model source, while structuring the code to mimic the architectural patterns of agent frameworks like AWS AgentCore and Strands. This will create a modular, local-first agent system.

## 1. New `LocalAgent` Framework

A new directory, `src/community_bot/local_agent/`, will be created to house the components of the local agent framework.

### `local_agent/agent.py`

*   **`LocalAgent` class**: The central orchestrator.
    *   **Responsibilities**: Manages the conversation flow, interacts with the model, and uses memory.
    *   **Methods**:
        *   `__init__(self, model, memory)`: Initializes the agent with a model and a memory object.
        *   `chat(self, user_message: str) -> AsyncGenerator[str, None]`: Takes a user message, updates the memory, and uses the model to generate a response.

### `local_agent/model.py`

*   **`OllamaModel` class**: A dedicated wrapper for the Ollama API.
    *   **Responsibilities**: Handles all communication with the Ollama server.
    *   **Methods**:
        *   `__init__(self, settings)`: Takes the application settings to get the Ollama model name and URL.
        *   `chat(self, history: list[dict]) -> AsyncGenerator[str, None]`: Takes a conversation history, sends it to the Ollama `/api/chat` endpoint, and streams the response.

### `local_agent/memory.py`

*   **`ConversationMemory` class**: Manages the conversational context.
    *   **Responsibilities**: Stores and retrieves the history of the conversation.
    *   **Methods**:
        *   `add_message(self, role: str, content: str)`: Adds a message to the history.
        *   `get_history(self) -> list[dict]`: Returns the current conversation history in a format suitable for the `OllamaModel`.

## 2. Refactor Core Components

The existing core components will be updated to use the new `LocalAgent` framework.

### `agent_client.py`

*   This file will be simplified to act as the entry point for the `LocalAgent`.
*   The `AgentClient` class will:
    *   Instantiate the `OllamaModel`, `ConversationMemory`, and `LocalAgent`.
    *   The `chat` method will now delegate directly to the `LocalAgent.chat` method.
    *   The dual-backend logic (`agentcore` vs. `ollama`) will be completely removed.

### `config.py`

*   The `Settings` dataclass and `load_settings` function will be updated to remove all AWS-related and backend-switching variables:
    *   **Remove**: `backend_mode`, `aws_region`, `agent_id`, `agent_alias_id`, `knowledge_base_id`.
    *   The configuration will now only contain settings for Discord and Ollama.

## 3. Update Entrypoint

### `main.py`

*   The `run` function will be simplified to reflect the new, more direct architecture.
*   It will load the simplified settings, instantiate the refactored `AgentClient`, and run the `CommunityBot`.

This refactoring will result in a clean, modular, and extensible local agent framework that uses Ollama as its core, while following the principles of more advanced agent systems.
