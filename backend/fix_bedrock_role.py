"""
Fix the Bedrock IAM role to have correct trust policy and permissions.
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def fix_bedrock_role():
    """Ensure the Bedrock role has correct trust policy and permissions."""
    
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    
    role_name = BEDROCK_ROLE_ARN.split('/')[-1]
    
    print(f"\n🔧 Fixing Bedrock IAM Role: {role_name}")
    print(f"   ARN: {BEDROCK_ROLE_ARN}\n")
    
    # 1. Update trust policy to allow Bedrock to assume the role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": AWS_ACCOUNT_ID
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock:{AWS_REGION}:{AWS_ACCOUNT_ID}:knowledge-base/*"
                    }
                }
            }
        ]
    }
    
    try:
        iam_client.update_assume_role_policy(
            RoleName=role_name,
            PolicyDocument=json.dumps(trust_policy)
        )
        print("✅ Updated trust policy")
    except Exception as e:
        print(f"❌ Error updating trust policy: {e}")
        return False
    
    # 2. Attach required policies
    policies_to_attach = [
        {
            'name': 'BedrockKnowledgeBasePolicy',
            'policy': {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        "Resource": f"arn:aws:bedrock:{AWS_REGION}::foundation-model/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "aoss:APIAccessAll"
                        ],
                        "Resource": f"arn:aws:aoss:{AWS_REGION}:{AWS_ACCOUNT_ID}:collection/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            "arn:aws:s3:::*/*",
                            "arn:aws:s3:::*"
                        ]
                    }
                ]
            }
        }
    ]
    
    for policy_config in policies_to_attach:
        policy_name = policy_config['name']
        
        try:
            # Check if policy exists
            try:
                policy_arn = f"arn:aws:iam::{AWS_ACCOUNT_ID}:policy/{policy_name}"
                iam_client.get_policy(PolicyArn=policy_arn)
                print(f"   ℹ️  Policy already exists: {policy_name}")
            except iam_client.exceptions.NoSuchEntityException:
                # Create the policy
                response = iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_config['policy']),
                    Description=f"Policy for Bedrock Knowledge Base - {policy_name}"
                )
                policy_arn = response['Policy']['Arn']
                print(f"   ✅ Created policy: {policy_name}")
            
            # Attach policy to role
            try:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                print(f"   ✅ Attached policy to role: {policy_name}")
            except iam_client.exceptions.NoSuchEntityException:
                print(f"   ℹ️  Policy already attached: {policy_name}")
                
        except Exception as e:
            print(f"   ❌ Error with policy {policy_name}: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Bedrock role configuration complete!")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    fix_bedrock_role()
