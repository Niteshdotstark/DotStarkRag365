"""
Check what IAM permissions the Bedrock role currently has
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def check_bedrock_role():
    """Check current IAM permissions on Bedrock role"""
    
    print(f"\n{'='*70}")
    print(f"  CHECKING BEDROCK ROLE IAM PERMISSIONS")
    print(f"{'='*70}\n")
    
    if not BEDROCK_ROLE_ARN:
        print("❌ BEDROCK_ROLE_ARN not set in environment")
        return
    
    role_name = BEDROCK_ROLE_ARN.split('/')[-1]
    print(f"Role ARN: {BEDROCK_ROLE_ARN}")
    print(f"Role Name: {role_name}\n")
    
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    
    try:
        # Get role details
        role = iam_client.get_role(RoleName=role_name)
        print(f"✅ Role exists")
        print(f"   Created: {role['Role']['CreateDate']}")
        print(f"   Trust Policy: {json.dumps(json.loads(role['Role']['AssumeRolePolicyDocument']), indent=2)}\n")
        
        # Check inline policies
        print(f"📋 Inline Policies:")
        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        
        if not inline_policies['PolicyNames']:
            print(f"   ⚠️  No inline policies found\n")
        else:
            for policy_name in inline_policies['PolicyNames']:
                policy = iam_client.get_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
                print(f"\n   Policy: {policy_name}")
                print(json.dumps(json.loads(policy['PolicyDocument']), indent=2))
        
        # Check attached managed policies
        print(f"\n📋 Attached Managed Policies:")
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        
        if not attached_policies['AttachedPolicies']:
            print(f"   ⚠️  No managed policies attached\n")
        else:
            for policy in attached_policies['AttachedPolicies']:
                print(f"   • {policy['PolicyName']} ({policy['PolicyArn']})")
        
        # Check for required permissions
        print(f"\n{'='*70}")
        print(f"PERMISSION CHECK:")
        print(f"{'='*70}\n")
        
        has_aoss_api = False
        has_aoss_dashboards = False
        
        # Check inline policies
        for policy_name in inline_policies['PolicyNames']:
            policy = iam_client.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            policy_doc = json.loads(policy['PolicyDocument'])
            
            for statement in policy_doc.get('Statement', []):
                actions = statement.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]
                
                if 'aoss:APIAccessAll' in actions or 'aoss:*' in actions:
                    has_aoss_api = True
                if 'aoss:DashboardsAccessAll' in actions or 'aoss:*' in actions:
                    has_aoss_dashboards = True
        
        print(f"Required Permissions:")
        print(f"  aoss:APIAccessAll        : {'✅ YES' if has_aoss_api else '❌ MISSING'}")
        print(f"  aoss:DashboardsAccessAll : {'✅ YES' if has_aoss_dashboards else '❌ MISSING'}")
        
        if not has_aoss_api or not has_aoss_dashboards:
            print(f"\n❌ PROBLEM FOUND!")
            print(f"\nAccording to AWS documentation:")
            print(f"  'Being granted permissions within a data access policy is not")
            print(f"   sufficient to access data in your OpenSearch Serverless collection.")
            print(f"   An associated principal must also be granted access to the IAM")
            print(f"   permissions aoss:APIAccessAll and aoss:DashboardsAccessAll.'")
            print(f"\n💡 This is why you're getting 403 Forbidden errors!")
            print(f"\n🔧 Run this to fix:")
            print(f"   python fix_bedrock_iam_permissions.py")
        else:
            print(f"\n✅ All required permissions are present!")
        
        print(f"\n{'='*70}\n")
        
    except iam_client.exceptions.NoSuchEntityException:
        print(f"❌ Role '{role_name}' not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_bedrock_role()
