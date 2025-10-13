#!/usr/bin/env python3
"""
Test script to debug Ollama server connectivity and the HTTP 500 error.
This script will test various scenarios to identify what's causing the issue.
"""

import asyncio
import json
import sys
from typing import Dict, List

import aiohttp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://thor.tail0be7e0.ts.net:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")

print(f"Testing Ollama server at: {OLLAMA_BASE_URL}")
print(f"Using model: {OLLAMA_MODEL}")
print("-" * 50)


async def test_server_health():
    """Test if the Ollama server is reachable."""
    print("1. Testing server health...")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{OLLAMA_BASE_URL}/api/version") as resp:
                print(f"   ✓ Server is reachable (status: {resp.status})")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✓ Server version: {data}")
                return True
    except Exception as e:
        print(f"   ✗ Server health check failed: {e}")
        return False


async def test_list_models():
    """Test listing available models."""
    print("\n2. Testing model listing...")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{OLLAMA_BASE_URL}/api/tags") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    models = [model['name'] for model in data.get('models', [])]
                    print(f"   ✓ Available models: {models}")
                    
                    if OLLAMA_MODEL in models:
                        print(f"   ✓ Target model '{OLLAMA_MODEL}' is available")
                        return True
                    else:
                        print(f"   ✗ Target model '{OLLAMA_MODEL}' is NOT available")
                        print(f"   Available models: {models}")
                        return False
                else:
                    print(f"   ✗ Failed to list models: {resp.status}")
                    text = await resp.text()
                    print(f"   Response: {text}")
                    return False
    except Exception as e:
        print(f"   ✗ Model listing failed: {e}")
        return False


async def test_simple_chat():
    """Test a simple chat request (non-streaming)."""
    print("\n3. Testing simple chat (non-streaming)...")
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": "Hello, can you respond with just 'OK'?"}
        ],
        "stream": False  # Non-streaming first
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    message = data.get('message', {})
                    content = message.get('content', 'No content')
                    print(f"   ✓ Response: {content}")
                    return True
                else:
                    print(f"   ✗ Chat failed with status: {resp.status}")
                    try:
                        error_text = await resp.text()
                        print(f"   Error response: {error_text}")
                    except:
                        print("   Could not read error response")
                    return False
    except Exception as e:
        print(f"   ✗ Simple chat failed: {e}")
        return False


async def test_streaming_chat():
    """Test streaming chat request (same as the bot uses)."""
    print("\n4. Testing streaming chat (same as bot)...")
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": "Hello, please respond with a short greeting."}
        ],
        "stream": True  # Streaming like the bot uses
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    print("   ✓ Streaming response started")
                    chunk_count = 0
                    content_parts = []
                    
                    async for line_bytes in resp.content:
                        if not line_bytes:
                            continue
                        
                        try:
                            line = line_bytes.decode("utf-8").strip()
                            if not line:
                                continue
                            
                            data = json.loads(line)
                            
                            if data.get("done"):
                                print(f"   ✓ Streaming completed after {chunk_count} chunks")
                                break
                            
                            message = data.get("message", {})
                            content = message.get("content")
                            
                            if content:
                                chunk_count += 1
                                content_parts.append(content)
                                
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            print(f"   Warning: Skipping malformed line: {e}")
                            continue
                    
                    full_response = "".join(content_parts)
                    print(f"   ✓ Full response: {full_response}")
                    return True
                else:
                    print(f"   ✗ Streaming chat failed with status: {resp.status}")
                    try:
                        error_text = await resp.text()
                        print(f"   Error response: {error_text}")
                    except:
                        print("   Could not read error response")
                    return False
    except Exception as e:
        print(f"   ✗ Streaming chat failed: {e}")
        return False


async def test_with_system_message():
    """Test with system message like the bot uses."""
    print("\n5. Testing with system message (like the bot)...")
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful Discord community assistant."},
            {"role": "user", "content": "test..."}  # Same message from the logs
        ],
        "stream": True
    }
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    print("   ✓ System message test successful")
                    # Just read first chunk to verify it works
                    async for line_bytes in resp.content:
                        if line_bytes:
                            try:
                                line = line_bytes.decode("utf-8").strip()
                                if line:
                                    data = json.loads(line)
                                    if data.get("message", {}).get("content"):
                                        print("   ✓ Received content in response")
                                        break
                            except:
                                continue
                    return True
                else:
                    print(f"   ✗ System message test failed with status: {resp.status}")
                    try:
                        error_text = await resp.text()
                        print(f"   Error response: {error_text}")
                    except:
                        print("   Could not read error response")
                    return False
    except Exception as e:
        print(f"   ✗ System message test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting Ollama connectivity and debugging tests...\n")
    
    tests = [
        test_server_health,
        test_list_models,
        test_simple_chat,
        test_streaming_chat,
        test_with_system_message
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    test_names = ["Server Health", "Model Listing", "Simple Chat", "Streaming Chat", "System Message"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if not all(results):
        print("\n🔍 DEBUGGING TIPS:")
        if not results[0]:  # Server health
            print("- Check if the Ollama server is running on thor.tail0be7e0.ts.net:11434")
            print("- Verify network connectivity and Tailscale connection")
        if not results[1]:  # Model listing
            print("- The model 'gpt-oss:20b' might not be loaded or available")
            print("- Try loading the model: ollama pull gpt-oss:20b")
        if results[0] and results[1] and not any(results[2:]):
            print("- Server and model are OK, but chat requests fail")
            print("- This suggests a configuration or request format issue")
            print("- Check Ollama server logs for more details")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_ollama.py")
        print("This script tests connectivity to the Ollama server and debugs the HTTP 500 error.")
        print("Make sure you have a .env file with OLLAMA_BASE_URL and OLLAMA_MODEL set.")
        sys.exit(0)
    
    asyncio.run(main())