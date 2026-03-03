"""
Fix OpenSearch collection permissions to allow index creation
"""
import boto3
import os
import json
from dotenv import load_dotenv
from database import get_db
from models import AgentCollection

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def fix_collection_policy(collection_name: str, tenant_id: int):
    """Update data access policy to include current user"""
    
    print(f"\n🔧 Fixing permissions for: {collection_name}")
    
    try:
        aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
        sts_client = boto3.client('sts', region_name=AWS_REGION)
        
        # Get current user ARN
        current_user_arn = sts_client.get_caller_identity()['Arn']
        print(f"   Current user: {current_user_arn}")
        print(f"   Bedrock role: {BEDROCK_ROLE_ARN}")
        
        policy_name = f"kb-policy-{tenant_id}"
        
        # Create or update the policy
        policy_document = [
            {
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
            }
        ]
        
        try:
            # Get existing policy to get its version
            existing_policy = aoss_client.get_access_policy(
                name=policy_name,
                type='data'
            )
            policy_version = existing_policy['accessPolicyDetail']['policyVersion']
            
            # Update existing policy
            aoss_client.update_access_policy(
                name=policy_name,
                type='data',
                policyVersion=policy_version,
                policy=json.dumps(policy_document)
            )
            print(f"   ✅ Updated policy: {policy_name}")
        except Exception as e:
            if 'ResourceNotFoundException' in str(e):
                # Policy doesn't exist, create it
                aoss_client.create_access_policy(
                    name=policy_name,
                    type='data',
                    policy=json.dumps(policy_document)
                )
                print(f"   ✅ Created policy: {policy_name}")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def fix_all_policies():
    """Fix policies for all collections"""
    
    db = next(get_db())
    
    try:
        collections = db.query(AgentCollection).all()
        
        if not collections:
            print("❌ No collections found")
            return
        
        print(f"\n{'='*60}")
        print(f"Found {len(collections)} collection(s)")
        print(f"{'='*60}")
        
        success_count = 0
        for collection in collections:
            # Extract tenant_id from collection name (kb-collection-{tenant_id})
            tenant_id = collection.collection_name.split('-')[-1]
            if fix_collection_policy(collection.collection_name, tenant_id):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Fixed {success_count}/{len(collections)} policies")
        print(f"⏳ Wait 30 seconds for permissions to propagate...")
        print(f"{'='*60}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_policies()
