"""
Check Bedrock role permissions
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv('env')

iam = boto3.client('iam')
role_name = 'BedrockKnowledgeBaseRole'

print(f"\n{'='*70}")
print(f"  CHECKING BEDROCK ROLE")
print(f"{'='*70}\n")

try:
    role = iam.get_role(RoleName=role_name)
    print(f"Role ARN: {role['Role']['Arn']}")
    print(f"Created: {role['Role']['CreateDate']}")
    
    print(f"\nTrust Policy:")
    print(json.dumps(role['Role']['AssumeRolePolicyDocument'], indent=2))
    
    print(f"\nAttached Policies:")
    policies = iam.list_attached_role_policies(RoleName=role_name)
    for p in policies['AttachedPolicies']:
        print(f"  - {p['PolicyName']}: {p['PolicyArn']}")
    
    print(f"\nInline Policies:")
    inline = iam.list_role_policies(RoleName=role_name)
    for p in inline['PolicyNames']:
        print(f"  - {p}")
        policy_doc = iam.get_role_policy(RoleName=role_name, PolicyName=p)
        print(f"    {json.dumps(policy_doc['PolicyDocument'], indent=4)}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n{'='*70}\n")
