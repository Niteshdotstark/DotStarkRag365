"""
Verify that the OpenSearch permission fix is ready to test
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')
collection_id = 'r0fqf4rli0n632ypd4la'

print(f"\n{'='*70}")
print(f"  VERIFYING FIX IS READY")
print(f"{'='*70}\n")

all_good = True

# 1. Check AWS credentials
print("1️⃣  Checking AWS credentials...")
try:
    sts = boto3.client('sts', region_name=AWS_REGION)
    identity = sts.get_caller_identity()
    print(f"   ✅ AWS credentials valid")
    print(f"   User: {identity['Arn']}")
    print(f"   Account: {identity['Account']}\n")
except Exception as e:
    print(f"   ❌ AWS credentials invalid: {e}\n")
    all_good = False

# 2. Check collection exists and is ACTIVE
print("2️⃣  Checking OpenSearch collection...")
try:
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    response = aoss.batch_get_collection(ids=[collection_id])
    
    if response['collectionDetails']:
        coll = response['collectionDetails'][0]
        status = coll['status']
        
        if status == 'ACTIVE':
            print(f"   ✅ Collection is ACTIVE")
            print(f"   Name: {coll['name']}")
            print(f"   Endpoint: {coll.get('collectionEndpoint')}\n")
        else:
            print(f"   ⚠️  Collection status: {status}")
            print(f"   Wait for it to become ACTIVE\n")
            all_good = False
    else:
        print(f"   ❌ Collection not found: {collection_id}\n")
        all_good = False
        
except Exception as e:
    print(f"   ❌ Error checking collection: {e}\n")
    all_good = False

# 3. Check data access policy
print("3️⃣  Checking data access policy...")
try:
    policy_name = 'kb-policy-3421'
    response = aoss.get_access_policy(name=policy_name, type='data')
    
    import json
    policy = response['accessPolicyDetail']
    policy_doc = json.loads(policy['policy']) if isinstance(policy['policy'], str) else policy['policy']
    
    principals = []
    for rule in policy_doc:
        principals.extend(rule.get('Principal', []))
    
    has_bedrock = any('BedrockKnowledgeBaseRole' in p for p in principals)
    
    if has_bedrock:
        print(f"   ✅ Data access policy exists")
        print(f"   Policy: {policy_name}")
        print(f"   Bedrock role included: Yes\n")
    else:
        print(f"   ⚠️  Bedrock role not in policy")
        print(f"   Principals: {principals}\n")
        all_good = False
        
except Exception as e:
    print(f"   ❌ Error checking policy: {e}\n")
    all_good = False

# 4. Check Bedrock role exists
print("4️⃣  Checking Bedrock role...")
try:
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='BedrockKnowledgeBaseRole')
    
    print(f"   ✅ Bedrock role exists")
    print(f"   ARN: {role['Role']['Arn']}\n")
    
    # Check attached policies
    policies = iam.list_attached_role_policies(RoleName='BedrockKnowledgeBaseRole')
    policy_names = [p['PolicyName'] for p in policies['AttachedPolicies']]
    
    required_policies = ['BedrockFullAccess', 'OpenSearchServerlessFullAccess']
    missing = [p for p in required_policies if p not in policy_names]
    
    if missing:
        print(f"   ⚠️  Missing policies: {missing}\n")
        all_good = False
    else:
        print(f"   ✅ All required policies attached\n")
        
except Exception as e:
    print(f"   ❌ Error checking role: {e}\n")
    all_good = False

# 5. Check OpenSearch access (optional - may still be propagating)
print("5️⃣  Checking OpenSearch access (optional)...")
try:
    from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
    
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    
    host = f'{collection_id}.{AWS_REGION}.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    # Try to list indices
    indices = client.cat.indices(format='json')
    print(f"   ✅ Can access OpenSearch")
    print(f"   Found {len(indices)} indices")
    
    # Check if our index exists
    index_name = 'bedrock-knowledge-base-default-index'
    if client.indices.exists(index=index_name):
        print(f"   ✅ Index '{index_name}' exists\n")
    else:
        print(f"   ℹ️  Index doesn't exist yet (Bedrock will create it)\n")
        
except Exception as e:
    print(f"   ⚠️  Cannot access OpenSearch yet: {e}")
    print(f"   ℹ️  This is OK - Bedrock will create the index automatically\n")

# Final verdict
print(f"{'='*70}")
if all_good:
    print(f"  ✅ ALL CHECKS PASSED - READY TO TEST!")
    print(f"{'='*70}\n")
    print(f"You can now test the crawl:")
    print(f"  sudo docker exec -it fastapi-backend python test_new_crawl.py")
    print(f"\nOr test directly:")
    print(f"  sudo docker exec -it fastapi-backend python test_kb_creation_direct.py")
else:
    print(f"  ⚠️  SOME CHECKS FAILED")
    print(f"{'='*70}\n")
    print(f"Review the errors above and fix them before testing.")

print(f"\n{'='*70}\n")
