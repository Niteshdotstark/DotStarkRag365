"""
List available Bedrock models in the region.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def main():
    bedrock = boto3.client('bedrock', region_name=AWS_REGION)
    
    print(f"\n{'='*70}")
    print(f"  AVAILABLE BEDROCK MODELS IN {AWS_REGION}")
    print(f"{'='*70}\n")
    
    try:
        response = bedrock.list_foundation_models()
        
        # Filter for text generation models
        text_models = [m for m in response['modelSummaries'] 
                      if 'TEXT' in m.get('outputModalities', [])]
        
        print(f"Found {len(text_models)} text generation models:\n")
        
        for model in text_models:
            model_id = model['modelId']
            model_name = model['modelName']
            provider = model['providerName']
            
            print(f"✓ {model_name}")
            print(f"  ID: {model_id}")
            print(f"  Provider: {provider}")
            print(f"  ARN: arn:aws:bedrock:{AWS_REGION}::foundation-model/{model_id}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
