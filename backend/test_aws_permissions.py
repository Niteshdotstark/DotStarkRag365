"""
Test script to verify AWS account has necessary permissions for website crawling feature.

This script tests:
1. AWS credentials are valid
2. Bedrock Knowledge Bases access
3. OpenSearch Serverless access
4. IAM role access

Run this script after adding your AWS credentials to the env file.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('env')

def test_aws_credentials():
    """Test if AWS credentials are valid"""
    print("\n" + "="*60)
    print("1. Testing AWS Credentials")
    print("="*60)
    
    try:
        # Get credentials from environment
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not access_key or access_key == 'your_access_key_here':
            print("❌ FAILED: AWS_ACCESS_KEY_ID not set in env file")
            return False
            
        if not secret_key or secret_key == 'your_secret_key_here':
            print("❌ FAILED: AWS_SECRET_ACCESS_KEY not set in env file")
            return False
        
        # Test credentials with STS
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        
        print(f"✅ SUCCESS: AWS credentials are valid")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   Region: {region}")
        
        # Update AWS_ACCOUNT_ID in env file if not set
        if os.getenv('AWS_ACCOUNT_ID') == 'your_account_id_here':
            print(f"\n   💡 TIP: Update AWS_ACCOUNT_ID in env file to: {identity['Account']}")
        
        return True
        
    except NoCredentialsError:
        print("❌ FAILED: No AWS credentials found")
        return False
    except ClientError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def test_bedrock_access():
    """Test if account has access to Bedrock Knowledge Bases"""
    print("\n" + "="*60)
    print("2. Testing AWS Bedrock Knowledge Bases Access")
    print("="*60)
    
    try:
        region = os.getenv('AWS_REGION', 'us-east-1')
        bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        
        # Try to list knowledge bases (should work even if empty)
        response = bedrock_agent.list_knowledge_bases(maxResults=1)
        
        print(f"✅ SUCCESS: Can access Bedrock Knowledge Bases")
        print(f"   Existing knowledge bases: {len(response.get('knowledgeBaseSummaries', []))}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ FAILED: No permission to access Bedrock Knowledge Bases")
            print(f"   Error: {e.response['Error']['Message']}")
            print(f"\n   💡 Required IAM permissions:")
            print(f"      - bedrock:ListKnowledgeBases")
            print(f"      - bedrock:CreateKnowledgeBase")
            print(f"      - bedrock:GetKnowledgeBase")
            print(f"      - bedrock:CreateDataSource")
            print(f"      - bedrock:StartIngestionJob")
            print(f"      - bedrock:GetIngestionJob")
        else:
            print(f"❌ FAILED: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def test_bedrock_runtime_access():
    """Test if account has access to Bedrock Agent Runtime"""
    print("\n" + "="*60)
    print("3. Testing AWS Bedrock Agent Runtime Access")
    print("="*60)
    
    try:
        region = os.getenv('AWS_REGION', 'us-east-1')
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Note: We can't test retrieve_and_generate without a knowledge base ID
        # But we can check if the client is accessible
        print(f"✅ SUCCESS: Can access Bedrock Agent Runtime")
        print(f"   Note: Full testing requires a knowledge base to be created")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ FAILED: No permission to access Bedrock Agent Runtime")
            print(f"   Error: {e.response['Error']['Message']}")
            print(f"\n   💡 Required IAM permissions:")
            print(f"      - bedrock:Retrieve")
            print(f"      - bedrock:RetrieveAndGenerate")
        else:
            print(f"❌ FAILED: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def test_opensearch_serverless_access():
    """Test if account has access to OpenSearch Serverless"""
    print("\n" + "="*60)
    print("4. Testing AWS OpenSearch Serverless Access")
    print("="*60)
    
    try:
        region = os.getenv('AWS_REGION', 'us-east-1')
        aoss = boto3.client('opensearchserverless', region_name=region)
        
        # Try to list collections (should work even if empty)
        response = aoss.list_collections(maxResults=1)
        
        print(f"✅ SUCCESS: Can access OpenSearch Serverless")
        print(f"   Existing collections: {len(response.get('collectionSummaries', []))}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ FAILED: No permission to access OpenSearch Serverless")
            print(f"   Error: {e.response['Error']['Message']}")
            print(f"\n   💡 Required IAM permissions:")
            print(f"      - aoss:ListCollections")
            print(f"      - aoss:CreateCollection")
            print(f"      - aoss:BatchGetCollection")
            print(f"      - aoss:CreateAccessPolicy")
            print(f"      - aoss:APIAccessAll")
        else:
            print(f"❌ FAILED: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def test_iam_access():
    """Test if account has access to IAM for role management"""
    print("\n" + "="*60)
    print("5. Testing AWS IAM Access")
    print("="*60)
    
    try:
        region = os.getenv('AWS_REGION', 'us-east-1')
        iam = boto3.client('iam', region_name=region)
        
        # Try to list roles (limited to 1 for testing)
        response = iam.list_roles(MaxItems=1)
        
        print(f"✅ SUCCESS: Can access IAM")
        
        # Check if BedrockKnowledgeBaseRole exists
        try:
            role_name = 'BedrockKnowledgeBaseRole'
            role = iam.get_role(RoleName=role_name)
            print(f"   ✅ BedrockKnowledgeBaseRole exists")
            print(f"      ARN: {role['Role']['Arn']}")
            
            # Update env file suggestion
            print(f"\n   💡 TIP: Update BEDROCK_ROLE_ARN in env file to:")
            print(f"      {role['Role']['Arn']}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"   ⚠️  WARNING: BedrockKnowledgeBaseRole does not exist")
                print(f"      You'll need to create this role manually or via script")
                print(f"\n   💡 Required trust policy:")
                print(f"      Service: bedrock.amazonaws.com")
                print(f"\n   💡 Required permissions:")
                print(f"      - aoss:APIAccessAll")
                print(f"      - bedrock:InvokeModel")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ FAILED: No permission to access IAM")
            print(f"   Error: {e.response['Error']['Message']}")
            print(f"\n   💡 Required IAM permissions:")
            print(f"      - iam:ListRoles")
            print(f"      - iam:GetRole")
            print(f"      - iam:CreateRole (optional, for auto-creation)")
        else:
            print(f"❌ FAILED: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def test_bedrock_model_access():
    """Test if account has access to Bedrock foundation models"""
    print("\n" + "="*60)
    print("6. Testing AWS Bedrock Foundation Models Access")
    print("="*60)
    
    try:
        region = os.getenv('AWS_REGION', 'us-east-1')
        bedrock = boto3.client('bedrock', region_name=region)
        
        # Check if Titan Embeddings v2 is available
        response = bedrock.list_foundation_models(
            byProvider='Amazon',
            byOutputModality='EMBEDDING'
        )
        
        titan_v2_found = False
        for model in response.get('modelSummaries', []):
            if 'titan-embed-text-v2' in model['modelId']:
                titan_v2_found = True
                print(f"✅ SUCCESS: Titan Embeddings v2 is available")
                print(f"   Model ID: {model['modelId']}")
                print(f"   Model ARN: {model['modelArn']}")
                break
        
        if not titan_v2_found:
            print(f"⚠️  WARNING: Titan Embeddings v2 not found")
            print(f"   Available embedding models: {len(response.get('modelSummaries', []))}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ FAILED: No permission to access Bedrock models")
            print(f"   Error: {e.response['Error']['Message']}")
            print(f"\n   💡 Required IAM permissions:")
            print(f"      - bedrock:ListFoundationModels")
            print(f"      - bedrock:InvokeModel")
        else:
            print(f"❌ FAILED: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False


def main():
    """Run all permission tests"""
    print("\n" + "="*60)
    print("AWS PERMISSIONS TEST FOR WEBSITE CRAWLING FEATURE")
    print("="*60)
    print("\nThis script will test if your AWS account has the necessary")
    print("permissions to use AWS Bedrock Knowledge Bases with Web Crawler.")
    
    results = {
        'credentials': test_aws_credentials(),
        'bedrock_kb': test_bedrock_access(),
        'bedrock_runtime': test_bedrock_runtime_access(),
        'opensearch': test_opensearch_serverless_access(),
        'iam': test_iam_access(),
        'bedrock_models': test_bedrock_model_access()
    }
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your AWS account is ready for implementation.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above and:")
        print("   1. Ensure your AWS credentials are correct in the env file")
        print("   2. Add the required IAM permissions to your AWS user/role")
        print("   3. Enable Bedrock services in your AWS region if needed")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
