"""
Diagnose and fix collection permissions issues
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def diagnose_and_fix():
    """Diagnose and fix collection permissions"""
    
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    collection_id = 'l2gyy0eln3h84ay5st85'
    policy_name = 'kb-policy-3421'
    
    print(f"\n{'='*70}")
    print(f"  DIAGNOSING COLLECTION PERMISSIONS")
    print(f"{'='*70}\n")
    
    print(f"Collection ID: {collection_id}")
    print(f"Bedrock Role: {BEDROCK_ROLE_ARN}\n")
    
    # Check existing policy
    try:
        print("🔍 Checking existing data access policy...")
        response = aoss_client.get_access_policy(
            name=policy_name,
            type='data'
        )
        
        policy = response['accessPolicyDetail']
        print(f"   Policy Name: {policy['name']}")
        print(f"   Policy Version: {policy['policyVersion']}")
        print(f"   Created: {policy['createdDate']}")
        
        # Policy is already a list, not a JSON string
        if isinstance(policy['policy'], str):
            current_policy = json.loads(policy['policy'])
        else:
            current_policy = policy['policy']
        
        print(f"\n   Current Policy:")
        print(json.dumps(current_policy, indent=2))
        
    except aoss_client.exceptions.ResourceNotFoundException:
        print("   ❌ Policy not found!")
        current_policy = None
        policy_version = None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Create correct policy
    print(f"\n🔧 Creating/updating policy with correct permissions...")
    
    correct_policy = [
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
        if current_policy:
            # Update existing policy
            policy_version = response['accessPolicyDetail']['policyVersion']
            
            aoss_client.update_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(correct_policy),
                policyVersion=policy_version,
                description='Data access policy for shared collection'
            )
            print("   ✅ Policy updated")
        else:
            # Create new policy
            aoss_client.create_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(correct_policy),
                description='Data access policy for shared collection'
            )
            print("   ✅ Policy created")
        
        print(f"\n   New Policy:")
        print(json.dumps(correct_policy, indent=2))
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Check network policy
    print(f"\n🔍 Checking network policy...")
    try:
        network_response = aoss_client.get_access_policy(
            name='kb-network-3421',
            type='network'
        )
        print("   ✅ Network policy exists")
    except aoss_client.exceptions.ResourceNotFoundException:
        print("   ⚠️  Network policy not found, creating...")
        
        network_policy = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{collection_id}"],
                        "ResourceType": "collection"
                    }
                ],
                "AllowFromPublic": True,
                "Description": "Network policy for shared collection"
            }
        ]
        
        try:
            aoss_client.create_access_policy(
                name='kb-network-3421',
                type='network',
                policy=json.dumps(network_policy),
                description='Network policy for shared collection'
            )
            print("   ✅ Network policy created")
        except Exception as e:
            print(f"   ❌ Error creating network policy: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Diagnosis complete!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    diagnose_and_fix()
