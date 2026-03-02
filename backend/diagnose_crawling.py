"""
Diagnostic script to identify issues with website crawling setup.

This script checks:
1. AWS credentials and permissions
2. Database connectivity
3. Environment variables
4. Bedrock service availability
5. OpenSearch Serverless permissions
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(".").resolve() / "env"
load_dotenv(dotenv_path=env_path)

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("\n" + "="*60)
    print("1. CHECKING ENVIRONMENT VARIABLES")
    print("="*60)
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'AWS_ACCOUNT_ID',
        'BEDROCK_ROLE_ARN'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'KEY' in var:
                display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All environment variables are set")
        return True


def check_aws_credentials():
    """Check if AWS credentials are valid"""
    print("\n" + "="*60)
    print("2. CHECKING AWS CREDENTIALS")
    print("="*60)
    
    try:
        sts_client = boto3.client('sts', region_name=os.getenv('AWS_REGION'))
        identity = sts_client.get_caller_identity()
        
        print(f"   ✅ AWS credentials are valid")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        return True
    except ClientError as e:
        print(f"   ❌ AWS credentials are invalid: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error checking credentials: {e}")
        return False


def check_bedrock_access():
    """Check if Bedrock service is accessible"""
    print("\n" + "="*60)
    print("3. CHECKING BEDROCK ACCESS")
    print("="*60)
    
    try:
        bedrock_client = boto3.client('bedrock', region_name=os.getenv('AWS_REGION'))
        
        # Try to list foundation models
        response = bedrock_client.list_foundation_models()
        model_count = len(response.get('modelSummaries', []))
        
        print(f"   ✅ Bedrock service is accessible")
        print(f"   Available foundation models: {model_count}")
        
        # Check for specific models we use
        models_needed = [
            'amazon.titan-embed-text-v2:0',
            'anthropic.claude-3-sonnet-20240229-v1:0'
        ]
        
        available_models = [m['modelId'] for m in response.get('modelSummaries', [])]
        
        for model in models_needed:
            if any(model in am for am in available_models):
                print(f"   ✅ Model available: {model}")
            else:
                print(f"   ⚠️  Model not found: {model}")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Cannot access Bedrock: {error_code} - {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n   💡 SOLUTION: Your AWS user needs Bedrock permissions")
            print("      Add the 'AmazonBedrockFullAccess' policy to your IAM user")
        
        return False
    except Exception as e:
        print(f"   ❌ Error checking Bedrock: {e}")
        return False


def check_bedrock_agent_access():
    """Check if Bedrock Agent service is accessible"""
    print("\n" + "="*60)
    print("4. CHECKING BEDROCK AGENT ACCESS")
    print("="*60)
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION'))
        
        # Try to list knowledge bases
        response = bedrock_agent.list_knowledge_bases(maxResults=1)
        
        print(f"   ✅ Bedrock Agent service is accessible")
        print(f"   Existing knowledge bases: {len(response.get('knowledgeBaseSummaries', []))}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Cannot access Bedrock Agent: {error_code} - {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n   💡 SOLUTION: Your AWS user needs Bedrock Agent permissions")
            print("      Add these policies to your IAM user:")
            print("      - AmazonBedrockFullAccess")
            print("      - Custom policy for bedrock-agent:* actions")
        
        return False
    except Exception as e:
        print(f"   ❌ Error checking Bedrock Agent: {e}")
        return False


def check_opensearch_serverless_access():
    """Check if OpenSearch Serverless is accessible"""
    print("\n" + "="*60)
    print("5. CHECKING OPENSEARCH SERVERLESS ACCESS")
    print("="*60)
    
    try:
        aoss_client = boto3.client('opensearchserverless', region_name=os.getenv('AWS_REGION'))
        
        # Try to list collections
        response = aoss_client.list_collections()
        
        print(f"   ✅ OpenSearch Serverless is accessible")
        print(f"   Existing collections: {len(response.get('collectionSummaries', []))}")
        
        # List collections
        for collection in response.get('collectionSummaries', []):
            print(f"      - {collection['name']} ({collection['status']})")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Cannot access OpenSearch Serverless: {error_code} - {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n   💡 SOLUTION: Your AWS user needs OpenSearch Serverless permissions")
            print("      Add the 'AmazonOpenSearchServiceFullAccess' policy to your IAM user")
        
        return False
    except Exception as e:
        print(f"   ❌ Error checking OpenSearch Serverless: {e}")
        return False


def check_iam_role():
    """Check if the Bedrock IAM role exists and has correct permissions"""
    print("\n" + "="*60)
    print("6. CHECKING BEDROCK IAM ROLE")
    print("="*60)
    
    role_arn = os.getenv('BEDROCK_ROLE_ARN')
    if not role_arn:
        print("   ❌ BEDROCK_ROLE_ARN not set")
        return False
    
    try:
        # Extract role name from ARN
        role_name = role_arn.split('/')[-1]
        
        iam_client = boto3.client('iam', region_name=os.getenv('AWS_REGION'))
        
        # Get role details
        role = iam_client.get_role(RoleName=role_name)
        
        print(f"   ✅ IAM role exists: {role_name}")
        print(f"   ARN: {role['Role']['Arn']}")
        print(f"   Created: {role['Role']['CreateDate']}")
        
        # Check attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        
        print(f"\n   Attached policies:")
        for policy in attached_policies['AttachedPolicies']:
            print(f"      - {policy['PolicyName']}")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Cannot access IAM role: {error_code} - {error_message}")
        
        if error_code == 'NoSuchEntity':
            print("\n   💡 SOLUTION: The Bedrock IAM role doesn't exist")
            print("      Run: python create_iam_role.py")
        
        return False
    except Exception as e:
        print(f"   ❌ Error checking IAM role: {e}")
        return False


def check_database_connection():
    """Check if database is accessible"""
    print("\n" + "="*60)
    print("7. CHECKING DATABASE CONNECTION")
    print("="*60)
    
    try:
        from database import SessionLocal, engine
        from sqlalchemy import text
        
        # Try to connect
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        
        print(f"   ✅ Database connection successful")
        print(f"   Database URI: {os.getenv('DATABASE_URI', 'Not set')}")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print("\n   💡 SOLUTION: Check your database configuration in env file")
        return False


def main():
    """Run all diagnostic checks"""
    print("\n" + "="*60)
    print("WEBSITE CRAWLING DIAGNOSTIC TOOL")
    print("="*60)
    print("\nThis tool will check your setup for common issues\n")
    
    results = {
        'Environment Variables': check_environment_variables(),
        'AWS Credentials': check_aws_credentials(),
        'Bedrock Access': check_bedrock_access(),
        'Bedrock Agent Access': check_bedrock_agent_access(),
        'OpenSearch Serverless': check_opensearch_serverless_access(),
        'IAM Role': check_iam_role(),
        'Database Connection': check_database_connection()
    }
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {check}")
    
    print(f"\n   Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All checks passed! Your setup is ready for website crawling.")
        print("\nYou can now:")
        print("   1. Start the FastAPI server: uvicorn main:app --reload")
        print("   2. Run the test script: python test_website_crawling.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues above before proceeding.")
        print("\nCommon solutions:")
        print("   1. Run 'python create_iam_role.py' to create the Bedrock IAM role")
        print("   2. Add required AWS policies to your IAM user")
        print("   3. Check your env file for correct AWS credentials")
        print("   4. Ensure your database is running")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
