"""
Fix permissions for the shared OpenSearch collection (agent 3421)
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def fix_collection_permissions():
    """Fix data access policy for the shared collection"""
    
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    collection_id = 'l2gyy0eln3h84ay5st85'
    policy_name = 'kb-policy-3421'
    
    print(f"\n{'='*70}")
    print(f"  FIXING COLLECTION PERMISSIONS")
    print(f"{'='*70}\n")
    
    print(f"Collection ID: {collection_id}")
    print(f"Policy Name: {policy_name}")
    print(f"Bedrock Role: {BEDROCK_ROLE_ARN}\n")
    
    # Create/update data access policy
    policy_document = [
        {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_id}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ],
                    "ResourceType": "collection"
                },
                {
                    "Resource": [f"index/{collection_id}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ],
                    "ResourceType": "index"
                }
            ],
            "Principal": [
                BEDROCK_ROLE_ARN,
                f"arn:aws:iam::{AWS_ACCOUNT_ID}:root"
            ],
            "Description": "Data access policy for shared collection"
        }
    ]
    
    try:
        print("🔧 Getting existing policy...")
        
        # Get existing policy to get its version
        existing_policy = aoss_client.get_access_policy(
            name=policy_name,
            type='data'
        )
        
        policy_version = existing_policy['accessPolicyDetail']['policyVersion']
        
        print(f"   Current version: {policy_version}")
        print("🔧 Updating data access policy...")
        
        aoss_client.update_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(policy_document),
            policyVersion=policy_version,
            description='Data access policy for shared collection'
        )
        
        print("✅ Data access policy updated successfully\n")
        
    except aoss_client.exceptions.ResourceNotFoundException:
        print("📝 Policy doesn't exist, creating new one...")
        
        try:
            aoss_client.create_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(policy_document),
                description='Data access policy for shared collection'
            )
            
            print("✅ Data access policy created successfully\n")
            
        except Exception as e:
            print(f"❌ Error creating policy: {e}\n")
            return False
    
    except Exception as e:
        print(f"❌ Error updating policy: {e}\n")
        return False
    
    print(f"{'='*70}")
    print("✅ Collection permissions fixed!")
    print(f"{'='*70}\n")
    
    return True

if __name__ == "__main__":
    fix_collection_permissions()
