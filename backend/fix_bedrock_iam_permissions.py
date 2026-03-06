"""
Fix Bedrock IAM role to include required OpenSearch Serverless permissions.

According to AWS docs, having a data access policy is NOT enough.
The IAM role MUST also have aoss:APIAccessAll permission.

Reference: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-data-access.html
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')

def fix_bedrock_role_permissions():
    """Add required OpenSearch Serverless IAM permissions to Bedrock role"""
    
    print(f"\n{'='*70}")
    print(f"  FIXING BEDROCK ROLE IAM PERMISSIONS")
    print(f"{'='*70}\n")
    
    if not BEDROCK_ROLE_ARN:
        print("❌ BEDROCK_ROLE_ARN not set in environment")
        return False
    
    # Extract role name from ARN
    role_name = BEDROCK_ROLE_ARN.split('/')[-1]
    print(f"Role ARN: {BEDROCK_ROLE_ARN}")
    print(f"Role Name: {role_name}\n")
    
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    
    # Define the required policy
    policy_name = "OpenSearchServerlessAPIAccess"
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll",
                    "aoss:DashboardsAccessAll"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Check if policy already exists on the role
        print(f"🔍 Checking existing inline policies...")
        existing_policies = iam_client.list_role_policies(RoleName=role_name)
        
        if policy_name in existing_policies['PolicyNames']:
            print(f"   ℹ️  Policy '{policy_name}' already exists, updating...")
        else:
            print(f"   📝 Creating new inline policy '{policy_name}'...")
        
        # Put (create or update) the inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"   ✅ Successfully added/updated policy!\n")
        
        # Verify the policy
        print(f"🔍 Verifying policy...")
        policy_response = iam_client.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        
        print(f"   ✅ Policy verified:")
        print(json.dumps(json.loads(policy_response['PolicyDocument']), indent=2))
        
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS!")
        print(f"{'='*70}")
        print(f"\nThe Bedrock role now has the required permissions:")
        print(f"  • aoss:APIAccessAll - Required for OpenSearch API access")
        print(f"  • aoss:DashboardsAccessAll - Required for Dashboards access")
        print(f"\nYou can now create indexes and access OpenSearch collections.")
        print(f"{'='*70}\n")
        
        return True
        
    except iam_client.exceptions.NoSuchEntityException:
        print(f"❌ Role '{role_name}' not found!")
        print(f"   Make sure BEDROCK_ROLE_ARN is correct in your .env file")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_bedrock_role_permissions()
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Wait 10-30 seconds for IAM changes to propagate")
        print("   2. Run your crawl test again: python test_new_crawl.py")
        print("   3. The 403 errors should be resolved\n")
    else:
        print("\n❌ Failed to fix permissions. Check the error above.\n")
