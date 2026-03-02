"""
Simple test to check if Claude 3 Sonnet is accessible.
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def test_claude():
    """Test Claude 3 Sonnet with a simple message."""
    
    print(f"\n{'='*70}")
    print(f"  TESTING CLAUDE 3 SONNET")
    print(f"{'='*70}\n")
    
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
    
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Simple test message
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello, I am working!' in one sentence."
            }
        ]
    })
    
    print(f"📤 Sending test message to Claude 3 Sonnet...")
    print(f"   Model: {model_id}")
    print(f"   Region: {AWS_REGION}\n")
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']
        
        print(f"✅ SUCCESS! Model is accessible!\n")
        print(f"📝 Response from Claude:")
        print(f"   {answer}\n")
        
        print(f"{'='*70}")
        print(f"🎉 CLAUDE 3 SONNET IS WORKING!")
        print(f"{'='*70}\n")
        print(f"✨ You can now run the full chat test:")
        print(f"   ./venv/Scripts/python test_chat_questions.py\n")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        print(f"❌ Error: {error_msg}\n")
        
        if "use case details" in error_msg.lower() or "404" in error_msg:
            print(f"{'='*70}")
            print(f"⚠️  USE CASE FORM REQUIRED")
            print(f"{'='*70}\n")
            print(f"AWS needs you to submit use case details for Anthropic models.\n")
            print(f"📝 How to submit:\n")
            print(f"1. Go to: https://console.aws.amazon.com/bedrock/")
            print(f"2. Click 'Playgrounds' → 'Chat'")
            print(f"3. Select 'Claude 3 Sonnet' from dropdown")
            print(f"4. Type 'Hello' and click 'Run'")
            print(f"5. Fill out the use case form that appears")
            print(f"6. Submit and wait 5-15 minutes")
            print(f"7. Run this script again to verify\n")
            print(f"{'='*70}\n")
        else:
            print(f"Unexpected error. Please check your AWS credentials and permissions.\n")
        
        return False

if __name__ == "__main__":
    test_claude()
