"""
Fix data access policy for the new collection to include current user
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def fix_access():
    """Update data access policy to include current user"""
    
    collection_id = 'r0fqf4rli0n632ypd4la'
    policy_name = 'kb-policy-3421'
    
    print(f"\n{'='*70}")
    print(f"  FIXING DATA ACCESS POLICY")
    print(f"{'='*70}\n")
    
    # Get current user
    sts = boto3.client('sts', region_name=AWS_REGION)
    user_arn = sts.get_caller_identity()['Arn']
    print(f"Current User: {user_arn}")
    print(f"Collection ID: {collection_id}\n")
    
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    # Get existing policy
    try:
        response = aoss.get_access_policy(name=policy_name, type='data')
        policy_version = response['accessPolicyDetail']['policyVersion']
        print(f"Found existing policy: {policy_name}")
        print(f"Version: {policy_version}\n")
    except Exception as e:
        print(f"❌ Error getting policy: {e}\n")
        return False
    
    # Update policy
    policy = [{
        "Rules": [
            {
                "Resource": [f"collection/{collection_id}"],
                "Permission": ["aoss:*"],
                "ResourceType": "collection"
            },
            {
                "Resource": [f"index/{collection_id}/*"],
                "Permission": ["aoss:*"],
                "ResourceType": "index"
            }
        ],
        "Principal": [
            BEDROCK_ROLE_ARN,
            f"arn:aws:iam::{AWS_ACCOUNT_ID}:root",
            user_arn
        ],
        "Description": "Data access policy with current user"
    }]
    
    try:
        print("🔧 Updating policy...")
        aoss.update_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(policy),
            policyVersion=policy_version
        )
        print("✅ Policy updated!\n")
        
        print("⏳ Waiting 30 seconds for changes to propagate...")
        import time
        time.sleep(30)
        
        print(f"\n{'='*70}")
        print("✅ ACCESS FIXED!")
        print(f"{'='*70}")
        print(f"\nYou should now be able to:")
        print(f"1. Access OpenSearch Dashboards")
        print(f"2. Create the index via Dev Tools")
        print(f"3. Start crawling websites\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating policy: {e}\n")
        return False

if __name__ == "__main__":
    fix_access()
