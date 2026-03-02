"""
Comprehensive permission checker and fixer for AWS Bedrock + OpenSearch Serverless.
This script will:
1. Check all current permissions
2. Grant missing permissions via CLI
3. Verify the setup is correct
"""
import boto3
import json
import os
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')
BEDROCK_ROLE_NAME = BEDROCK_ROLE_ARN.split('/')[-1] if BEDROCK_ROLE_ARN else None

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_status(status, message):
    symbols = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    print(f"{symbols.get(status, '•')} {message}")

def check_iam_role():
    """Check if IAM role exists and has correct trust policy."""
    print_section("1. CHECKING IAM ROLE")
    
    iam = boto3.client('iam', region_name=AWS_REGION)
    
    try:
        role = iam.get_role(RoleName=BEDROCK_ROLE_NAME)
        print_status("success", f"Role exists: {BEDROCK_ROLE_NAME}")
        
        # Check trust policy
        trust_policy = role['Role']['AssumeRolePolicyDocument']
        print_status("info", "Current trust policy:")
        print(json.dumps(trust_policy, indent=2))
        
        # Check if Bedrock service is in trust policy
        has_bedrock = False
        for statement in trust_policy.get('Statement', []):
            principal = statement.get('Principal', {})
            service = principal.get('Service', '')
            if 'bedrock.amazonaws.com' in str(service):
                has_bedrock = True
                break
        
        if has_bedrock:
            print_status("success", "Bedrock service can assume this role")
        else:
            print_status("error", "Bedrock service NOT in trust policy - FIXING...")
            fix_trust_policy(iam)
        
        return True
        
    except iam.exceptions.NoSuchEntityException:
        print_status("error", f"Role does not exist: {BEDROCK_ROLE_NAME}")
        print_status("info", "Creating role...")
        create_iam_role(iam)
        return True
    except Exception as e:
        print_status("error", f"Error checking role: {e}")
        return False

def fix_trust_policy(iam):
    """Fix the trust policy to allow Bedrock to assume the role."""
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
        iam.update_assume_role_policy(
            RoleName=BEDROCK_ROLE_NAME,
            PolicyDocument=json.dumps(trust_policy)
        )
        print_status("success", "Trust policy updated")
    except Exception as e:
        print_status("error", f"Failed to update trust policy: {e}")

def create_iam_role(iam):
    """Create the IAM role if it doesn't exist."""
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
        iam.create_role(
            RoleName=BEDROCK_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock Knowledge Base to access OpenSearch and S3"
        )
        print_status("success", f"Created role: {BEDROCK_ROLE_NAME}")
    except Exception as e:
        print_status("error", f"Failed to create role: {e}")

def check_and_attach_policies():
    """Check and attach all required policies to the IAM role."""
    print_section("2. CHECKING IAM POLICIES")
    
    iam = boto3.client('iam', region_name=AWS_REGION)
    
    # Define all required policies
    policies = {
        "BedrockFullAccess": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:*"
                    ],
                    "Resource": "*"
                }
            ]
        },
        "OpenSearchServerlessFullAccess": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:*"
                    ],
                    "Resource": "*"
                }
            ]
        },
        "S3FullAccessForBedrock": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
    }
    
    for policy_name, policy_doc in policies.items():
        policy_arn = f"arn:aws:iam::{AWS_ACCOUNT_ID}:policy/{policy_name}"
        
        # Check if policy exists
        try:
            iam.get_policy(PolicyArn=policy_arn)
            print_status("info", f"Policy exists: {policy_name}")
        except iam.exceptions.NoSuchEntityException:
            # Create policy
            try:
                response = iam.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_doc),
                    Description=f"Full access policy for {policy_name}"
                )
                policy_arn = response['Policy']['Arn']
                print_status("success", f"Created policy: {policy_name}")
            except Exception as e:
                print_status("error", f"Failed to create policy {policy_name}: {e}")
                continue
        
        # Attach policy to role
        try:
            iam.attach_role_policy(
                RoleName=BEDROCK_ROLE_NAME,
                PolicyArn=policy_arn
            )
            print_status("success", f"Attached {policy_name} to role")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print_status("info", f"Policy already attached: {policy_name}")
            else:
                print_status("error", f"Failed to attach {policy_name}: {e}")

def check_opensearch_collection():
    """Check OpenSearch Serverless collection and policies."""
    print_section("3. CHECKING OPENSEARCH SERVERLESS")
    
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    sts = boto3.client('sts', region_name=AWS_REGION)
    
    tenant_id = 1
    collection_name = f"kb-collection-{tenant_id}"
    
    # Check if collection exists
    try:
        response = aoss.batch_get_collection(names=[collection_name])
        if response['collectionDetails']:
            collection = response['collectionDetails'][0]
            print_status("success", f"Collection exists: {collection_name}")
            print_status("info", f"Collection ARN: {collection['arn']}")
            print_status("info", f"Collection endpoint: {collection.get('collectionEndpoint', 'N/A')}")
        else:
            print_status("warning", f"Collection does not exist: {collection_name}")
            return False
    except Exception as e:
        print_status("error", f"Error checking collection: {e}")
        return False
    
    # Check data access policy
    policy_name = f"kb-policy-{tenant_id}"
    current_user_arn = sts.get_caller_identity()['Arn']
    
    try:
        response = aoss.get_access_policy(name=policy_name, type='data')
        print_status("success", f"Data access policy exists: {policy_name}")
        
        # Parse policy - it might be a string or already parsed
        policy_data = response['accessPolicyDetail']['policy']
        if isinstance(policy_data, str):
            policy_doc = json.loads(policy_data)
        else:
            policy_doc = policy_data
            
        principals = policy_doc[0].get('Principal', [])
        
        print_status("info", "Current principals in policy:")
        for principal in principals:
            print(f"    - {principal}")
        
        # Check if Bedrock role is in principals
        if BEDROCK_ROLE_ARN in principals:
            print_status("success", "Bedrock role is in data access policy")
        else:
            print_status("error", "Bedrock role NOT in data access policy - FIXING...")
            fix_data_access_policy(aoss, sts, collection_name, policy_name)
            
    except aoss.exceptions.ResourceNotFoundException:
        print_status("error", f"Data access policy does not exist: {policy_name}")
        print_status("info", "Creating data access policy...")
        fix_data_access_policy(aoss, sts, collection_name, policy_name)
    except Exception as e:
        print_status("error", f"Error checking data access policy: {e}")
    
    return True

def fix_data_access_policy(aoss, sts, collection_name, policy_name):
    """Create or update the data access policy."""
    current_user_arn = sts.get_caller_identity()['Arn']
    
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
        "Principal": [
            BEDROCK_ROLE_ARN,
            current_user_arn,
            f"arn:aws:iam::{AWS_ACCOUNT_ID}:root"  # Add root for full access
        ]
    }]
    
    try:
        # Try to delete existing policy first
        try:
            aoss.delete_access_policy(name=policy_name, type='data')
            print_status("info", "Deleted old policy")
            time.sleep(2)  # Wait for deletion to propagate
        except:
            pass
        
        # Create new policy
        aoss.create_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(policy_document)
        )
        print_status("success", "Created/updated data access policy")
        print_status("info", "Policy document:")
        print(json.dumps(policy_document, indent=2))
        
    except Exception as e:
        print_status("error", f"Failed to fix data access policy: {e}")

def check_network_policy():
    """Check and fix network policy for OpenSearch."""
    print_section("4. CHECKING NETWORK POLICY")
    
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    tenant_id = 1
    collection_name = f"kb-collection-{tenant_id}"
    network_policy_name = f"kb-network-{tenant_id}"
    
    try:
        response = aoss.get_security_policy(name=network_policy_name, type='network')
        print_status("success", f"Network policy exists: {network_policy_name}")
        
        policy_doc = json.loads(response['securityPolicyDetail']['policy'])
        print_status("info", "Network policy:")
        print(json.dumps(policy_doc, indent=2))
        
    except aoss.exceptions.ResourceNotFoundException:
        print_status("warning", f"Network policy does not exist: {network_policy_name}")
        print_status("info", "Creating network policy...")
        
        network_policy = [{
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AllowFromPublic": True
        }]
        
        try:
            aoss.create_security_policy(
                name=network_policy_name,
                type='network',
                policy=json.dumps(network_policy)
            )
            print_status("success", "Created network policy")
        except Exception as e:
            print_status("error", f"Failed to create network policy: {e}")
    except Exception as e:
        print_status("error", f"Error checking network policy: {e}")

def check_encryption_policy():
    """Check encryption policy for OpenSearch."""
    print_section("5. CHECKING ENCRYPTION POLICY")
    
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    tenant_id = 1
    collection_name = f"kb-collection-{tenant_id}"
    encryption_policy_name = f"kb-encryption-{tenant_id}"
    
    try:
        response = aoss.get_security_policy(name=encryption_policy_name, type='encryption')
        print_status("success", f"Encryption policy exists: {encryption_policy_name}")
    except aoss.exceptions.ResourceNotFoundException:
        print_status("info", f"Encryption policy does not exist (this is OK)")
    except Exception as e:
        print_status("error", f"Error checking encryption policy: {e}")

def verify_bedrock_access():
    """Verify Bedrock can access required services."""
    print_section("6. VERIFYING BEDROCK ACCESS")
    
    bedrock = boto3.client('bedrock', region_name=AWS_REGION)
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    try:
        # List foundation models
        response = bedrock.list_foundation_models()
        print_status("success", f"Can access Bedrock - found {len(response['modelSummaries'])} models")
    except Exception as e:
        print_status("error", f"Cannot access Bedrock: {e}")
    
    try:
        # List knowledge bases
        response = bedrock_agent.list_knowledge_bases(maxResults=10)
        print_status("success", f"Can access Bedrock Agent - found {len(response.get('knowledgeBaseSummaries', []))} knowledge bases")
    except Exception as e:
        print_status("error", f"Cannot access Bedrock Agent: {e}")

def main():
    """Run all checks and fixes."""
    print_section("AWS PERMISSION CHECKER AND FIXER")
    
    print(f"AWS Region: {AWS_REGION}")
    print(f"AWS Account: {AWS_ACCOUNT_ID}")
    print(f"Bedrock Role: {BEDROCK_ROLE_ARN}")
    
    if not all([AWS_REGION, AWS_ACCOUNT_ID, BEDROCK_ROLE_ARN]):
        print_status("error", "Missing required environment variables!")
        print("Please set: AWS_REGION, AWS_ACCOUNT_ID, BEDROCK_ROLE_ARN in your env file")
        return
    
    # Run all checks
    check_iam_role()
    check_and_attach_policies()
    check_opensearch_collection()
    check_network_policy()
    check_encryption_policy()
    verify_bedrock_access()
    
    print_section("SUMMARY")
    print_status("success", "All permission checks complete!")
    print_status("warning", "Wait 2-3 minutes for AWS policies to propagate")
    print_status("info", "Then run: ./venv/Scripts/python test_dotstark_e2e.py")
    print()

if __name__ == "__main__":
    main()
