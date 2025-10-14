"""Test basic Nova-Pro connectivity."""

import boto3
import json
import os
from dotenv import load_dotenv


def test_nova_connection():
    """Test basic Nova-Pro connectivity."""
    load_dotenv()
    
    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = os.getenv("NOVA_MODEL_ID", "us.amazon.nova-pro-v1:0")
    
    print(f"Testing connection to Nova model: {model_id}")
    print(f"Region: {region}")
    print("-" * 80)
    
    client = boto3.client('bedrock-runtime', region_name=region)
    
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello! Can you introduce yourself in one sentence?"}]
            }
        ],
        "inferenceConfig": {
            "temperature": 0.7,
            "maxTokens": 100,
            "topP": 0.9
        }
    })
    
    try:
        print("Invoking Nova model...")
        response = client.invoke_model(
            modelId=model_id,
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        print("✅ Nova-Pro is accessible!")
        print("-" * 80)
        print("Response:")
        print(json.dumps(response_body, indent=2))
        
    except Exception as e:
        print(f"❌ Error connecting to Nova: {e}")
        raise


if __name__ == "__main__":
    test_nova_connection()
