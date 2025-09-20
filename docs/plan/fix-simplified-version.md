# Plan to Address Architectural Simplifications

This document outlines a plan to address the two main architectural simplifications identified during the project review:

1.  The use of a single-process application instead of the planned serverless architecture with API Gateway and Lambda.
2.  The lack of streaming support for the AWS AgentCore backend.

Implementing these changes will make the bot more scalable, robust, and align it with the original design goals.

## 1. Refactor to a Serverless Architecture

The current single-process design is simple but not ideal for a production environment. A serverless architecture with API Gateway and Lambda will provide better scalability and resilience.

### Plan:

1.  **Create a Lambda Handler:**
    *   Create a new file, `lambda_handler.py`, which will contain the main Lambda handler function.
    *   This function will parse the incoming event from API Gateway, which will contain the Discord message.
    *   It will instantiate the `AgentClient` and call the appropriate backend to get a response.
    *   The function will return the response in the format expected by API Gateway.

2.  **Modify the Discord Bot:**
    *   The existing `discord_bot.py` will be modified to act as a thin client.
    *   Instead of processing messages directly, it will forward them to the new API Gateway endpoint via an HTTP POST request.
    *   It will then receive the response from the API Gateway and post it to the Discord channel.
    *   This separates the Discord interaction logic from the core message processing logic.

3.  **Infrastructure as Code (IaC):**
    *   Use a tool like AWS CDK or Terraform to define the necessary AWS resources:
        *   An API Gateway with a `/chat` endpoint.
        *   A Lambda function configured with the Python runtime and the necessary environment variables.
        *   The required IAM roles and permissions for the Lambda function to access the Bedrock Agent.

## 2. Implement Streaming for AgentCore

Currently, only the Ollama backend supports streaming responses. Adding streaming support to the AgentCore backend will improve the user experience by providing faster, more responsive feedback.

### Plan:

1.  **Update `_chat_agentcore`:**
    *   Modify the `_chat_agentcore` method in `agent_client.py` to be an `async generator`.
    *   Use `boto3`'s `invoke_agent` method, which supports streaming responses from Bedrock Agents.
    *   The method will iterate over the response stream and `yield` each chunk of the response as it is received.

2.  **Handle Streaming in the Lambda:**
    *   The Lambda handler will need to be able to handle the streaming response from the `AgentClient`.
    *   Depending on the API Gateway configuration, the Lambda can either stream the response back to the client or collect the full response before returning it.

By completing these two tasks, the bot will be more robust, scalable, and provide a better user experience, fully realizing the initial vision for the project.
