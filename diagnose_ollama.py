#!/usr/bin/env python3
"""
Advanced diagnostic script for Ollama model loading issues.
This script helps identify specific problems with model loading.
"""

import asyncio
import json
import sys
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://thor.tail0be7e0.ts.net:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

print(f"Advanced Ollama Diagnostics for: {OLLAMA_BASE_URL}")
print(f"Target model: {OLLAMA_MODEL}")
print("-" * 60)


async def check_model_details():
    """Get detailed information about the model."""
    print("1. Checking model details...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE_URL}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for model in data.get('models', []):
                        if model['name'] == OLLAMA_MODEL:
                            print(f"   ✓ Model found: {model['name']}")
                            print(f"   ✓ Size: {model.get('size', 'Unknown')} bytes")
                            print(f"   ✓ Modified: {model.get('modified_at', 'Unknown')}")
                            print(f"   ✓ Digest: {model.get('digest', 'Unknown')[:20]}...")
                            
                            # Check if size is reasonable for a 20B model
                            size = model.get('size', 0)
                            if size > 0:
                                size_gb = size / (1024 ** 3)
                                print(f"   ✓ Size in GB: {size_gb:.2f}")
                                if size_gb < 10:  # 20B model should be much larger
                                    print(f"   ⚠️  WARNING: Model size seems too small for 20B parameters")
                            return True
                    print(f"   ✗ Model {OLLAMA_MODEL} not found in model list")
                    return False
    except Exception as e:
        print(f"   ✗ Failed to check model details: {e}")
        return False


async def try_model_show():
    """Try to get model information using the show endpoint."""
    print("\n2. Trying model show command...")
    
    payload = {"name": OLLAMA_MODEL}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/show", json=payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✓ Model info retrieved successfully")
                    print(f"   ✓ License: {data.get('license', 'Unknown')}")
                    print(f"   ✓ Parameters: {data.get('parameters', 'Unknown')}")
                    
                    # Check for any model configuration issues
                    modelfile = data.get('modelfile', '')
                    if 'FROM' in modelfile:
                        print(f"   ✓ Model has proper FROM declaration")
                    else:
                        print(f"   ⚠️  WARNING: Model might be missing FROM declaration")
                    
                    return True
                else:
                    error_text = await resp.text()
                    print(f"   ✗ Model show failed: {error_text}")
                    return False
    except Exception as e:
        print(f"   ✗ Model show request failed: {e}")
        return False


async def test_model_pull():
    """Test if we can pull/refresh the model."""
    print("\n3. Testing model pull/refresh...")
    
    payload = {"name": OLLAMA_MODEL}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/pull", json=payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    print("   ✓ Model pull started successfully")
                    
                    # Read the streaming response
                    chunk_count = 0
                    async for line_bytes in resp.content:
                        if not line_bytes:
                            continue
                        
                        try:
                            line = line_bytes.decode("utf-8").strip()
                            if line:
                                data = json.loads(line)
                                status = data.get('status', '')
                                if 'pulling' in status.lower():
                                    chunk_count += 1
                                    if chunk_count % 10 == 0:  # Show progress every 10 chunks
                                        print(f"   📥 {status}")
                                elif 'success' in status.lower() or 'complete' in status.lower():
                                    print(f"   ✓ {status}")
                                    return True
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                    
                    return True
                else:
                    error_text = await resp.text()
                    print(f"   ✗ Model pull failed: {error_text}")
                    return False
    except asyncio.TimeoutError:
        print("   ⚠️  Model pull timed out (this is normal for large models)")
        return True
    except Exception as e:
        print(f"   ✗ Model pull request failed: {e}")
        return False


async def test_small_model():
    """Test with a smaller model to see if it's a resource issue."""
    print("\n4. Testing with smaller model (tinyllama)...")
    
    # First try to pull a small model
    payload = {"name": "tinyllama"}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Try chat with tinyllama
            chat_payload = {
                "model": "tinyllama",
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": False
            }
            
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=chat_payload) as resp:
                print(f"   Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✓ Small model works fine - issue is specific to {OLLAMA_MODEL}")
                    return True
                elif resp.status == 404:
                    print(f"   ℹ️  tinyllama not available, but this tells us the API is working")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"   ✗ Small model also fails: {error_text}")
                    return False
    except Exception as e:
        print(f"   ✗ Small model test failed: {e}")
        return False


async def main():
    """Run diagnostics."""
    print("Running advanced Ollama model diagnostics...\n")
    
    tests = [
        check_model_details,
        try_model_show,
        test_model_pull,
        test_small_model
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY:")
    test_names = ["Model Details", "Model Show", "Model Pull", "Small Model Test"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    print("Based on the 'EOF' error during model loading, try these solutions:")
    print()
    print("1. **Re-pull the model** (most likely fix):")
    print("   SSH to thor server and run:")
    print("   $ ollama pull gpt-oss:20b")
    print()
    print("2. **Check available disk space and memory:**")
    print("   $ df -h  # Check disk space")
    print("   $ free -h  # Check memory")
    print("   $ nvidia-smi  # Check GPU memory if using GPU")
    print()
    print("3. **Remove and re-download the model:**")
    print("   $ ollama rm gpt-oss:20b")
    print("   $ ollama pull gpt-oss:20b")
    print()
    print("4. **Check Ollama server logs:**")
    print("   $ journalctl -u ollama -f  # If running as systemd service")
    print("   Or check the Docker container logs if running in Docker")
    print()
    print("5. **Try a different model temporarily:**")
    print("   Update .env to use: OLLAMA_MODEL=llama2:7b")
    print("   This will help confirm if it's model-specific or server-wide")


if __name__ == "__main__":
    asyncio.run(main())