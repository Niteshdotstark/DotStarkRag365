"""
Script to create IAM role for Bedrock Knowledge Base
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv('env')

# Initialize IAM client
iam = boto3.client('iam', region_name=os.getenv('AWS_REGION'))

print('='*60)
print('STEP 1: Creating IAM Role for Bedrock Knowledge Base')
print('='*60)

# Trust policy for Bedrock to assume the role
trust_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Principal': {
                'Service': 'bedrock.amazonaws.com'
            },
            'Action': 'sts:AssumeRole',
            'Condition': {
                'StringEquals': {
                    'aws:SourceAccount': os.getenv('AWS_ACCOUNT_ID')
                },
                'ArnLike': {
                    'aws:SourceArn': f'arn:aws:bedrock:{os.getenv("AWS_REGION")}:{os.getenv("AWS_ACCOUNT_ID")}:knowledge-base/*'
                }
            }
        }
    ]
}

try:
    # Create the role
    response = iam.create_role(
        RoleName='BedrockKnowledgeBaseRole',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role for Bedrock Knowledge Bases to access OpenSearch Serverless'
    )
    print(f'✅ Role created successfully!')
    print(f'   ARN: {response["Role"]["Arn"]}')
    role_created = True
except iam.exceptions.EntityAlreadyExistsException:
    print('ℹ️  Role already exists, updating trust policy...')
    iam.update_assume_role_policy(
        RoleName='BedrockKnowledgeBaseRole',
        PolicyDocument=json.dumps(trust_policy)
    )
    print('✅ Trust policy updated!')
    role_created = False
except Exception as e:
    print(f'❌ Error creating role: {e}')
    exit(1)

print('\n' + '='*60)
print('STEP 2: Attaching AWS Managed Policy - AmazonBedrockFullAccess')
print('='*60)

# Attach AWS managed policy for Bedrock
bedrock_policy_arn = 'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'

try:
    iam.attach_role_policy(
        RoleName='BedrockKnowledgeBaseRole',
        PolicyArn=bedrock_policy_arn
    )
    print('✅ AmazonBedrockFullAccess policy attached successfully!')
except Exception as e:
    if 'already attached' in str(e).lower() or 'attached' in str(e).lower():
        print('ℹ️  AmazonBedrockFullAccess policy already attached')
    else:
        print(f'❌ Error attaching Bedrock policy: {e}')
        exit(1)

print('\n' + '='*60)
print('STEP 3: Creating Custom IAM Policy for OpenSearch Serverless')
print('='*60)

# Permissions policy for OpenSearch Serverless
permissions_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Sid': 'OpenSearchServerlessAccess',
            'Effect': 'Allow',
            'Action': [
                'aoss:APIAccessAll'
            ],
            'Resource': f'arn:aws:aoss:{os.getenv("AWS_REGION")}:{os.getenv("AWS_ACCOUNT_ID")}:collection/*'
        }
    ]
}

custom_policy_arn = f'arn:aws:iam::{os.getenv("AWS_ACCOUNT_ID")}:policy/BedrockOpenSearchPolicy'

try:
    # Create the custom policy
    response = iam.create_policy(
        PolicyName='BedrockOpenSearchPolicy',
        PolicyDocument=json.dumps(permissions_policy),
        Description='Permissions for Bedrock Knowledge Base to access OpenSearch Serverless'
    )
    print(f'✅ Custom policy created successfully!')
    print(f'   ARN: {response["Policy"]["Arn"]}')
    custom_policy_arn = response["Policy"]["Arn"]
except iam.exceptions.EntityAlreadyExistsException:
    print(f'ℹ️  Custom policy already exists')
    print(f'   ARN: {custom_policy_arn}')
except Exception as e:
    print(f'❌ Error creating custom policy: {e}')
    exit(1)

print('\n' + '='*60)
print('STEP 4: Attaching Custom Policy to Role')
print('='*60)

try:
    # Attach custom policy to role
    iam.attach_role_policy(
        RoleName='BedrockKnowledgeBaseRole',
        PolicyArn=custom_policy_arn
    )
    print('✅ Custom policy attached to role successfully!')
except Exception as e:
    if 'already attached' in str(e).lower():
        print('ℹ️  Custom policy already attached to role')
    else:
        print(f'❌ Error attaching custom policy: {e}')
        exit(1)

print('\n' + '='*60)
print('STEP 5: Verifying Role Configuration')
print('='*60)

try:
    # Get role details
    response = iam.get_role(RoleName='BedrockKnowledgeBaseRole')
    print(f'✅ Role verified!')
    print(f'   Role Name: {response["Role"]["RoleName"]}')
    print(f'   Role ARN: {response["Role"]["Arn"]}')
    print(f'   Created: {response["Role"]["CreateDate"]}')
    
    # List attached policies
    policies = iam.list_attached_role_policies(RoleName='BedrockKnowledgeBaseRole')
    print(f'\n   Attached Policies:')
    for policy in policies['AttachedPolicies']:
        print(f'     - {policy["PolicyName"]}')
    
except Exception as e:
    print(f'❌ Error verifying role: {e}')
    exit(1)

print('\n' + '='*60)
print('✅ IAM ROLE SETUP COMPLETE!')
print('='*60)
print('\nThe role is ready to use. You can now:')
print('1. Restart your FastAPI server')
print('2. Run the website crawling tests')
print('\nRole ARN in env file:')
print(f'BEDROCK_ROLE_ARN={response["Role"]["Arn"]}')
