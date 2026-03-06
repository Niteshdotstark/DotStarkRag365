"""
Comprehensive permission test - shows exactly what works and what doesn't
"""
import boto3
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import json

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')
collection_id = 'r0fqf4rli0n632ypd4la'
index_name = 'bedrock-knowledge-base-default-index'

print(f"\n{'='*70}")
print(f"  COMPREHENSIVE PERMISSION TEST")
print(f"{'='*70}\n")

results = {
    'aws_credentials': False,
    'list_collections': False,
    'get_collection': False,
    'get_policy': False,
    'opensearch_connect': False,
    'opensearch_list_indices': False,
    'opensearch_index_exists': False,
    'opensearch_create_index': False,
    'bedrock_list_kbs': False,
    'bedrock_create_kb': False
}

# Test 1: AWS Credentials
print("1️⃣  Testing AWS Credentials...")
try:
    sts = boto3.client('sts', region_name=AWS_REGION)
    identity = sts.get_caller_identity()
    print(f"   ✅ PASS - Credentials valid")
    print(f"   User: {identity['Arn']}")
    print(f"   Account: {identity['Account']}\n")
    results['aws_credentials'] = True
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 2: List Collections
print("2️⃣  Testing List Collections...")
try:
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    response = aoss.list_collections()
    print(f"   ✅ PASS - Can list collections")
    print(f"   Found {len(response['collectionSummaries'])} collections\n")
    results['list_collections'] = True
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 3: Get Specific Collection
print("3️⃣  Testing Get Collection Details...")
try:
    response = aoss.batch_get_collection(ids=[collection_id])
    if response['collectionDetails']:
        coll = response['collectionDetails'][0]
        print(f"   ✅ PASS - Can get collection details")
        print(f"   Name: {coll['name']}")
        print(f"   Status: {coll['status']}")
        print(f"   Endpoint: {coll.get('collectionEndpoint')}\n")
        results['get_collection'] = True
    else:
        print(f"   ❌ FAIL - Collection not found\n")
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 4: Get Data Access Policy
print("4️⃣  Testing Get Data Access Policy...")
try:
    response = aoss.get_access_policy(name='kb-policy-3421', type='data')
    policy = response['accessPolicyDetail']
    print(f"   ✅ PASS - Can get data access policy")
    print(f"   Policy: {policy['name']}")
    print(f"   Version: {policy['policyVersion']}\n")
    results['get_policy'] = True
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 5: Connect to OpenSearch
print("5️⃣  Testing OpenSearch Connection...")
try:
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    
    host = f'{collection_id}.{AWS_REGION}.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    # Try to get cluster info
    info = client.info()
    print(f"   ✅ PASS - Can connect to OpenSearch")
    print(f"   Cluster: {info.get('cluster_name', 'N/A')}\n")
    results['opensearch_connect'] = True
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 6: List Indices
if results['opensearch_connect']:
    print("6️⃣  Testing List Indices...")
    try:
        indices = client.cat.indices(format='json')
        print(f"   ✅ PASS - Can list indices")
        print(f"   Found {len(indices)} indices")
        for idx in indices:
            print(f"   - {idx['index']}")
        print()
        results['opensearch_list_indices'] = True
    except Exception as e:
        print(f"   ❌ FAIL - {e}\n")
else:
    print("6️⃣  Skipping List Indices (connection failed)\n")

# Test 7: Check if Index Exists
if results['opensearch_connect']:
    print("7️⃣  Testing Check Index Exists...")
    try:
        exists = client.indices.exists(index=index_name)
        if exists:
            print(f"   ✅ PASS - Index exists: {index_name}\n")
            results['opensearch_index_exists'] = True
        else:
            print(f"   ℹ️  INFO - Index does not exist yet\n")
    except Exception as e:
        print(f"   ❌ FAIL - {e}\n")
else:
    print("7️⃣  Skipping Check Index (connection failed)\n")

# Test 8: Try to Create Index
if results['opensearch_connect'] and not results['opensearch_index_exists']:
    print("8️⃣  Testing Create Index...")
    try:
        index_body = {
            "settings": {"index.knn": True},
            "mappings": {
                "properties": {
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {"engine": "faiss", "name": "hnsw"}
                    },
                    "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                    "AMAZON_BEDROCK_METADATA": {"type": "text"}
                }
            }
        }
        
        result = client.indices.create(index=index_name, body=index_body)
        print(f"   ✅ PASS - Can create index!")
        print(f"   Index created: {index_name}\n")
        results['opensearch_create_index'] = True
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        print(f"   This is the BLOCKING issue!\n")
else:
    if results['opensearch_index_exists']:
        print("8️⃣  Skipping Create Index (already exists)\n")
        results['opensearch_create_index'] = True
    else:
        print("8️⃣  Skipping Create Index (connection failed)\n")

# Test 9: List Bedrock Knowledge Bases
print("9️⃣  Testing List Bedrock Knowledge Bases...")
try:
    bedrock = boto3.client('bedrock-agent', region_name=AWS_REGION)
    response = bedrock.list_knowledge_bases(maxResults=10)
    print(f"   ✅ PASS - Can list knowledge bases")
    print(f"   Found {len(response.get('knowledgeBaseSummaries', []))} KBs\n")
    results['bedrock_list_kbs'] = True
except Exception as e:
    print(f"   ❌ FAIL - {e}\n")

# Test 10: Try to Create Knowledge Base (only if index exists)
if results['opensearch_index_exists'] or results['opensearch_create_index']:
    print("🔟  Testing Create Bedrock Knowledge Base...")
    try:
        kb_name = f"test-kb-{int(boto3.Session().get_credentials().access_key[-4:], 16)}"
        
        response = bedrock.create_knowledge_base(
            name=kb_name,
            description="Test KB for permission testing",
            roleArn=BEDROCK_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f'arn:aws:aoss:{AWS_REGION}:705406524080:collection/{collection_id}',
                    'vectorIndexName': index_name,
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"   ✅ PASS - Can create knowledge base!")
        print(f"   KB ID: {kb_id}")
        print(f"   Name: {kb_name}\n")
        results['bedrock_create_kb'] = True
        
        # Clean up test KB
        print(f"   🧹 Cleaning up test KB...")
        bedrock.delete_knowledge_base(knowledgeBaseId=kb_id)
        print(f"   ✅ Test KB deleted\n")
        
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
        print(f"   This is the MAIN issue preventing crawls!\n")
else:
    print("🔟  Skipping Create KB (index doesn't exist)\n")

# Summary
print(f"{'='*70}")
print(f"  PERMISSION TEST SUMMARY")
print(f"{'='*70}\n")

passed = sum(results.values())
total = len(results)

for test, result in results.items():
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} - {test.replace('_', ' ').title()}")

print(f"\n{'='*70}")
print(f"  SCORE: {passed}/{total} tests passed")
print(f"{'='*70}\n")

# Diagnosis
if results['opensearch_create_index']:
    print("🎉 GREAT NEWS! You can create the index now!")
    print("   Run: sudo docker exec -it fastapi-backend python test_new_crawl.py\n")
elif results['opensearch_index_exists']:
    print("🎉 GREAT NEWS! The index already exists!")
    print("   Run: sudo docker exec -it fastapi-backend python test_new_crawl.py\n")
elif results['opensearch_connect']:
    print("⏳ PARTIAL PERMISSIONS:")
    print("   - Can connect to OpenSearch")
    print("   - Cannot create index yet (403 error)")
    print("   - Permissions are still propagating")
    print("   - Wait 1-2 hours and run this test again\n")
else:
    print("❌ PERMISSIONS NOT READY:")
    print("   - Cannot access OpenSearch at all")
    print("   - Permissions haven't propagated yet")
    print("   - Wait 2-4 hours and run this test again\n")

print(f"{'='*70}\n")
