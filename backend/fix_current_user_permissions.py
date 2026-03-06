"""
Add OpenSearch Serverless permissions to the current IAM user/role.

The current EC2 instance role also needs aoss:APIAccessAll permissions
to create indexes and access OpenSearch collections.
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def fix_current_user_permissions():
    """Add OpenSearch Serverless permissions to current user/role"""
    
    print(f"\n{'='*70}")
    print(f"  FIXING CURRENT USER/ROLE PERMISSIONS")
    print(f"{'='*70}\n")
    
    sts_client = boto3.client('sts', region_name=AWS_REGION)
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    
    # Get current identity
    identity = sts_client.get_caller_identity()
    current_arn = identity['Arn']
    
    print(f"Current Identity: {current_arn}")
    print(f"Account: {identity['Account']}\n")
    
    # Check if it's a role or user
    if ':role/' in current_arn:
        entity_type = 'role'
        entity_name = current_arn.split('/')[-1]
    elif ':user/' in current_arn:
        entity_type = 'user'
        entity_name = current_arn.split('/')[-1]
    else:
        print(f"❌ Unknown identity type: {current_arn}")
        return False
    
    print(f"Entity Type: {entity_type}")
    print(f"Entity Name: {entity_name}\n")
    
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
        if entity_type == 'role':
            # Check existing policies
            print(f"🔍 Checking existing inline policies on role...")
            existing_policies = iam_client.list_role_policies(RoleName=entity_name)
            
            if policy_name in existing_policies['PolicyNames']:
                print(f"   ℹ️  Policy '{policy_name}' already exists, updating...")
            else:
                print(f"   📝 Creating new inline policy '{policy_name}'...")
            
            # Put the inline policy
            iam_client.put_role_policy(
                RoleName=entity_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            print(f"   ✅ Successfully added/updated policy!\n")
            
            # Verify
            print(f"🔍 Verifying policy...")
            policy_response = iam_client.get_role_policy(
                RoleName=entity_name,
                PolicyName=policy_name
            )
            
        elif entity_type == 'user':
            # Check existing policies
            print(f"🔍 Checking existing inline policies on user...")
            existing_policies = iam_client.list_user_policies(UserName=entity_name)
            
            if policy_name in existing_policies['PolicyNames']:
                print(f"   ℹ️  Policy '{policy_name}' already exists, updating...")
            else:
                print(f"   📝 Creating new inline policy '{policy_name}'...")
            
            # Put the inline policy
            iam_client.put_user_policy(
                UserName=entity_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            print(f"   ✅ Successfully added/updated policy!\n")
            
            # Verify
            print(f"🔍 Verifying policy...")
            policy_response = iam_client.get_user_policy(
                UserName=entity_name,
                PolicyName=policy_name
            )
        
        # Policy document might be dict or string
        verified_policy = policy_response['PolicyDocument']
        if isinstance(verified_policy, str):
            verified_policy = json.loads(verified_policy)
        
        print(f"   ✅ Policy verified:")
        print(json.dumps(verified_policy, indent=2))
        
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS!")
        print(f"{'='*70}")
        print(f"\nThe current {entity_type} now has the required permissions:")
        print(f"  • aoss:APIAccessAll - Required for OpenSearch API access")
        print(f"  • aoss:DashboardsAccessAll - Required for Dashboards access")
        print(f"\nYou can now create indexes and access OpenSearch collections.")
        print(f"{'='*70}\n")
        
        return True
        
    except iam_client.exceptions.NoSuchEntityException:
        print(f"❌ {entity_type.capitalize()} '{entity_name}' not found!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_current_user_permissions()
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Wait 10-30 seconds for IAM changes to propagate")
        print("   2. Run your crawl test again: python test_new_crawl.py")
        print("   3. The 403 errors should be resolved\n")
    else:
        print("\n❌ Failed to fix permissions. Check the error above.\n")
