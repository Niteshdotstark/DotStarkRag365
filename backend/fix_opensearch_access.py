"""
Fix OpenSearch data access policy for tenant 1.
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def fix_opensearch_access():
    """Update the OpenSearch data access policy to include Bedrock role."""
    
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    sts_client = boto3.client('sts', region_name=AWS_REGION)
    
    tenant_id = 1
    collection_name = f"kb-collection-{tenant_id}"
    policy_name = f"kb-policy-{tenant_id}"
    
    # Get current user ARN
    current_user_arn = sts_client.get_caller_identity()['Arn']
    
    print(f"\n🔧 Fixing OpenSearch Access Policy")
    print(f"   Collection: {collection_name}")
    print(f"   Policy: {policy_name}")
    print(f"   Bedrock Role: {BEDROCK_ROLE_ARN}")
    print(f"   Current User: {current_user_arn}\n")
    
    # Delete existing policy if it exists
    try:
        aoss_client.delete_access_policy(
            name=policy_name,
            type='data'
        )
        print(f"✅ Deleted old policy: {policy_name}")
    except Exception as e:
        print(f"   ℹ️  No existing policy to delete: {e}")
    
    # Create new policy with correct principals
    policy_document = [{
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": [f"collection/{collection_name}"],
                "Permission": ["aoss:*"]
            },
            {
                "ResourceType": "index",
                "Resource": [f"index/{collection_name}/*"],
                "Permission": ["aoss:*"]
            }
        ],
        "Principal": [BEDROCK_ROLE_ARN, current_user_arn]
    }]
    
    try:
        aoss_client.create_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(policy_document)
        )
        print(f"✅ Created new data access policy: {policy_name}")
        print(f"\n   Policy Document:")
        print(f"   {json.dumps(policy_document, indent=2)}")
    except Exception as e:
        print(f"❌ Error creating policy: {e}")
        return False
    
    print(f"\n{'='*60}")
    print("✅ OpenSearch access policy updated!")
    print("   Wait 60 seconds for changes to propagate...")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    fix_opensearch_access()
