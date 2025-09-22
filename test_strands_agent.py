#!/usr/bin/env python3
"""
Test script for Strands Agents with Ollama
This script tests the basic functionality without relative imports.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from strands import Agent
from strands.models.ollama import OllamaModel

def test_ollama_agent():
    """Test the Ollama agent setup."""
    print("Testing Strands Agent with Ollama...")
    
    # Configure Ollama model (using defaults for testing)
    try:
        model = OllamaModel(
            host="http://localhost:11434",
            model_id="llama3"  # You can change this to whatever model you have
        )
        print("✓ OllamaModel created successfully")
        
        # Create agent
        agent = Agent(model=model)
        print("✓ Strands Agent created successfully")
        
        # Test a simple interaction (this will fail if Ollama is not running)
        try:
            response = agent("Hello! Can you tell me what 2+2 equals?")
            print(f"✓ Agent response: {response}")
            return True
        except Exception as e:
            print(f"✗ Agent interaction failed: {e}")
            print("Note: This is expected if Ollama is not running locally")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create model or agent: {e}")
        return False

def test_bedrock_agent():
    """Test the Bedrock agent setup (without actual AWS call)."""
    print("\nTesting Strands Agent with Bedrock (configuration only)...")
    
    try:
        from strands.models import BedrockModel
        
        # Just test that we can create the model object
        model = BedrockModel(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0.3,
            streaming=True
        )
        print("✓ BedrockModel created successfully")
        
        agent = Agent(model=model)
        print("✓ Strands Agent with Bedrock created successfully")
        
        # Don't test actual interaction since it requires AWS credentials
        print("Note: Actual Bedrock calls require proper AWS credentials")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create Bedrock model or agent: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Strands Agents Test")
    print("=" * 60)
    
    ollama_success = test_ollama_agent()
    bedrock_success = test_bedrock_agent()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Ollama Agent: {'✓ PASS' if ollama_success else '✗ FAIL'}")
    print(f"  Bedrock Agent: {'✓ PASS' if bedrock_success else '✗ FAIL'}")
    print("=" * 60)