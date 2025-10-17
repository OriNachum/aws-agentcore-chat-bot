"""Test script for Nova Pro with AgentCore mode."""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_configuration():
    """Test that configuration is set up correctly for Nova Pro."""
    print("=" * 80)
    print("Testing Nova Pro Configuration")
    print("=" * 80)
    
    # Check required environment variables
    required_vars = {
        "BACKEND_MODE": "agentcore",
        "LLM_PROVIDER": "bedrock",
        "AWS_REGION": None,
    }
    
    optional_vars = {
        "BEDROCK_MODEL_ID": "us.amazon.nova-pro-v1:0",
        "BEDROCK_TEMPERATURE": "0.7",
        "BEDROCK_MAX_TOKENS": "4096",
        "BEDROCK_STREAMING": "true",
    }
    
    print("\n1. Checking Required Environment Variables:")
    print("-" * 80)
    
    all_good = True
    for var, expected in required_vars.items():
        value = os.getenv(var)
        if value:
            if expected and value != expected:
                print(f"  ⚠️  {var}={value} (expected: {expected})")
            else:
                print(f"  ✅ {var}={value}")
        else:
            print(f"  ❌ {var} is not set!")
            all_good = False
    
    print("\n2. Checking Optional Environment Variables:")
    print("-" * 80)
    
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        if value == default:
            print(f"  ⚙️  {var}={value} (default)")
        else:
            print(f"  ✅ {var}={value}")
    
    print("\n3. Checking AWS Credentials:")
    print("-" * 80)
    
    # Check AWS credentials
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_key and aws_secret:
        print(f"  ✅ AWS_ACCESS_KEY_ID is set ({aws_key[:10]}...)")
        print(f"  ✅ AWS_SECRET_ACCESS_KEY is set (***)")
    else:
        print("  ⚙️  Environment variables not set, checking ~/.aws/credentials")
        
        # Check credentials file
        aws_dir = Path.home() / ".aws"
        creds_file = aws_dir / "credentials"
        
        if creds_file.exists():
            print(f"  ✅ AWS credentials file found: {creds_file}")
        else:
            print(f"  ⚠️  No AWS credentials file found at {creds_file}")
            print("     You may need to configure AWS credentials!")
            all_good = False
    
    if not all_good:
        print("\n" + "=" * 80)
        print("❌ Configuration Issues Found!")
        print("=" * 80)
        print("\nPlease set the required environment variables:")
        print("  $env:BACKEND_MODE = 'agentcore'")
        print("  $env:LLM_PROVIDER = 'bedrock'")
        print("  $env:AWS_REGION = 'us-east-1'")
        print("\nAnd configure AWS credentials (one of):")
        print("  1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  2. Create ~/.aws/credentials file")
        return False
    
    print("\n" + "=" * 80)
    print("✅ Configuration looks good!")
    print("=" * 80)
    return True


def test_imports():
    """Test that required modules can be imported."""
    print("\n4. Testing Module Imports:")
    print("-" * 80)
    
    try:
        from community_bot.config import load_settings
        print("  ✅ config module imported")
        
        settings = load_settings()
        print(f"  ✅ Settings loaded successfully")
        print(f"     - Backend mode: {settings.backend_mode}")
        print(f"     - AWS region: {settings.aws_region}")
        print(f"     - Bedrock model: {settings.bedrock_model_id}")
        print(f"     - Temperature: {settings.bedrock_temperature}")
        print(f"     - Max tokens: {settings.bedrock_max_tokens}")
        print(f"     - Streaming: {settings.bedrock_streaming}")
        
    except Exception as e:
        print(f"  ❌ Failed to load settings: {e}")
        return False
    
    try:
        from community_bot.agentcore_app import get_agent
        print("  ✅ agentcore_app module imported")
    except Exception as e:
        print(f"  ❌ Failed to import agentcore_app: {e}")
        return False
    
    try:
        from strands.models import BedrockModel
        print("  ✅ Strands BedrockModel imported")
    except Exception as e:
        print(f"  ⚠️  Failed to import BedrockModel: {e}")
        print("     This may be normal if strands is not installed")
    
    return True


def test_agent_initialization():
    """Test that the agent can be initialized."""
    print("\n5. Testing Agent Initialization:")
    print("-" * 80)
    
    try:
        from community_bot.agentcore_app import get_agent
        
        print("  Initializing agent...")
        agent = get_agent()
        print("  ✅ Agent initialized successfully!")
        print(f"     Agent type: {type(agent)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_query():
    """Test a simple query to Nova Pro."""
    print("\n6. Testing Simple Query to Nova Pro:")
    print("-" * 80)
    
    try:
        from community_bot.agentcore_app import chat_with_agent
        
        test_message = "Say 'Hello from Nova Pro!' and nothing else."
        print(f"  Sending test message: {test_message}")
        print("  Waiting for response...")
        
        response = chat_with_agent(test_message, use_knowledge_base=False)
        
        print(f"\n  ✅ Response received!")
        print(f"\n  Response ({len(response)} chars):")
        print("  " + "-" * 76)
        print("  " + response[:500])
        if len(response) > 500:
            print("  ...")
        print("  " + "-" * 76)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to query agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Nova Pro Configuration Test" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run tests
    tests = [
        ("Configuration Check", test_configuration),
        ("Module Imports", test_imports),
        ("Agent Initialization", test_agent_initialization),
        ("Simple Query", test_simple_query),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n")
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 80)
    if all_passed:
        print("🎉 All tests passed! Nova Pro is ready to use.")
        print("\nYou can now:")
        print("  1. Run interactive mode: python src/community_bot/agentcore_app.py")
        print("  2. Start the Discord bot: uv run community-bot")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
