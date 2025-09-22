# Integrating AgentCore for a Flexible and Scalable Community Bot

This document outlines the strategy for refactoring the community bot to leverage **Amazon Bedrock AgentCore**. This will allow for a more robust, scalable, and flexible architecture that supports both local development with models like Ollama and cloud deployment using Amazon Bedrock, all while utilizing AgentCore's powerful features like managed knowledge bases.

### 1. Why AgentCore?

The initial design was based on a more traditional, monolithic agent structure. AgentCore offers a modular, serverless approach with several key advantages:

*   **Model-Agnostic**: AgentCore is not tied to Amazon Bedrock. You can run agents that use any LLM, including local models served via Ollama. This is perfect for flexible development and testing.
*   **Framework-Agnostic**: It supports various agent-building frameworks like Strands, LangChain, CrewAI, etc.
*   **Managed Infrastructure**: It handles the "undifferentiated heavy lifting" of deploying, scaling, and managing agent infrastructure.
*   **Local and Cloud Workflow**: The `bedrock-agentcore-starter-toolkit` provides a seamless experience for running agents locally for development and deploying them to a scalable, serverless AWS environment.
*   **Composable Services**: AgentCore provides modular services like `Memory` (for knowledge bases), `Gateway` (for tools), and `Identity` that can be used together or independently.

### 2. Key Concepts for Our Use Case

*   **AgentCore Runtime**: This is the serverless environment where our agent will be deployed. It handles scaling and execution. For local development, the starter toolkit simulates this runtime.
*   **AgentCore Memory**: This is the managed service for short-term and long-term memory. We can connect this to an S3 bucket to create a RAG knowledge base. Crucially, **the agent can query this memory service regardless of whether the agent itself is using a Bedrock model or an Ollama model**.
*   **`bedrock-agentcore-starter-toolkit`**: This is the CLI tool we will use to manage the local development and deployment lifecycle.

### 3. How to Adapt the Current Application

Here is a step-by-step guide to refactoring the existing `community-bot` to be compatible with AgentCore.

#### Step 1: Restructure the Agent Code

The core logic of our agent needs to be wrapped in a `BedrockAgentCoreApp`. This makes it compatible with the AgentCore runtime (both local and deployed).

Instead of the current `local_agent/agent.py`, we would create a new entrypoint, let's call it `agentcore_app.py`:

```python
# src/community_bot/agentcore_app.py

import os
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, StrandsOllama # Or your preferred model provider

# --- Model Configuration ---
# This is where we can switch between Ollama and Bedrock
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama") # 'ollama' or 'bedrock'

if LLM_PROVIDER == "ollama":
    # Assumes Ollama is running locally
    model = StrandsOllama(model="llama3", base_url="http://localhost:11434")
else:
    # Configure for Bedrock (e.g., Claude)
    # model = StrandsBedrock(model_id="anthropic.claude-3-sonnet-20240229-v1:0")
    # For now, let's keep it simple
    raise NotImplementedError("Bedrock model configuration not yet implemented.")

# --- AgentCore Application ---
app = BedrockAgentCoreApp()
agent = Agent(llm=model)

@app.entrypoint
def invoke(payload):
    """
    This function is the entrypoint for the AgentCore runtime.
    'payload' will contain the input from the client.
    """
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    
    # Here you can add logic to use AgentCore Memory (Knowledge Base)
    # For example: result = agent.query(user_message, tools=[knowledge_base_tool])
    
    result = agent(user_message)
    
    return {"result": result.message}

if __name__ == "__main__":
    # This allows us to run the agent locally for testing
    app.run()

```

#### Step 2: Update Dependencies

We need to add the AgentCore toolkit to our project's dependencies in `pyproject.toml`.

```toml
# pyproject.toml

[project]
# ... existing config ...
dependencies = [
    "discord.py",
    "requests",
    "boto3",
    "uvicorn",
    "fastapi",
    "python-dotenv",
    "bedrock-agentcore-starter-toolkit",
    "strands-agents",
    "strands-ollama" # If using the StrandsOllama adapter
]
# ...
```
Then, run `uv pip install -r requirements.txt` or `uv sync` to update the environment.

#### Step 3: Local Development Workflow

This is where the power of the toolkit comes in.

1.  **Run the Agent Locally**:
    Set the environment variable and run the app.
    ```bash
    # In your terminal
    $env:LLM_PROVIDER="ollama"
    python src/community_bot/agentcore_app.py
    ```
    This will start a local server on `http://localhost:8080`.

2.  **Test the Local Agent**:
    You can now send requests to it using `curl` or any HTTP client.
    ```bash
    curl -X POST http://localhost:8080/invocations \
      -H "Content-Type: application/json" \
      -d '{"prompt": "Hello, who are you?"}'
    ```

#### Step 4: Deployment to AWS

When you are ready to deploy the agent to a scalable AWS environment:

1.  **Configure for Deployment**:
    The toolkit will inspect your entrypoint file and prepare it for deployment.
    ```bash
    agentcore configure -e src/community_bot/agentcore_app.py
    ```

2.  **Launch to AWS**:
    This command packages your agent, creates the necessary IAM roles and other resources, and deploys it to the AgentCore Runtime.
    ```bash
    agentcore launch
    ```

3.  **Invoke the Deployed Agent**:
    After deployment, you can invoke the agent running on AWS.
    ```bash
    agentcore invoke '{"prompt": "How does deployment work?"}'
    ```

### 4. Integrating the Knowledge Base with Ollama

This is a key requirement. AgentCore's services are modular. The `AgentCore Memory` service, which provides the knowledge base, can be used by any agent, regardless of the LLM it uses.

1.  **Create a Knowledge Base**: In the AWS console, you would set up an AgentCore Memory/Knowledge Base and point it to your S3 bucket.
2.  **Give the Agent Access**: The deployed agent would be given IAM permissions to access this knowledge base.
3.  **Use in Code**: The agent code would use a tool provided by AgentCore to query the knowledge base. The agent's LLM (Ollama) would decide *when* to use the tool, but the actual search and retrieval would be performed by the `AgentCore Memory` service.

This architecture correctly separates the "thinking" part (the LLM, e.g., Ollama) from the "knowledge retrieval" part (AgentCore Memory), allowing you to combine the flexibility of local models with the power of managed AWS services.
