"""
Check if Claude 3 Sonnet model access has been granted.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def check_model_access():
    """Check if we can access Claude 3 Sonnet."""
    
    print(f"\n{'='*70}")
    print(f"  CHECKING CLAUDE 3 SONNET ACCESS")
    print(f"{'='*70}\n")
    
    bedrock = boto3.client('bedrock', region_name=AWS_REGION)
    
    # The model we're using
    target_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    try:
        # Get foundation model details
        response = bedrock.get_foundation_model(modelIdentifier=target_model)
        
        model_details = response['modelDetails']
        
        print(f"✅ Model Found: {model_details['modelName']}")
        print(f"   Model ID: {model_details['modelId']}")
        print(f"   Provider: {model_details['providerName']}")
        print(f"   Status: Available")
        
        # Try to invoke the model to verify access
        print(f"\n🔍 Testing model invocation...")
        
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        
        try:
            # Simple test invocation
            test_response = bedrock_runtime.invoke_model(
                modelId=target_model,
                body='{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
            )
            
            print(f"✅ Model invocation successful!")
            print(f"\n{'='*70}")
            print(f"🎉 CLAUDE 3 SONNET ACCESS IS GRANTED!")
            print(f"{'='*70}\n")
            print(f"✨ You can now run the chat test:")
            print(f"   ./venv/Scripts/python test_chat_questions.py")
            print(f"\n{'='*70}\n")
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            if "use case details" in error_msg.lower() or "404" in error_msg:
                print(f"❌ Model access NOT yet granted")
                print(f"\n⏳ Status: Pending approval")
                print(f"\n💡 What to do:")
                print(f"   1. Wait 5-15 minutes for AWS to process your request")
                print(f"   2. Check your email for approval notification")
                print(f"   3. Run this script again to verify")
                print(f"\n   If it's been more than 15 minutes:")
                print(f"   - Go to AWS Bedrock Console")
                print(f"   - Check 'Model access' page")
                print(f"   - Verify the request was submitted")
                print(f"\n{'='*70}\n")
                return False
            else:
                print(f"❌ Error invoking model: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return False

if __name__ == "__main__":
    check_model_access()
