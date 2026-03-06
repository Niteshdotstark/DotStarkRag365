"""
Check current permission status for the collection
"""
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
collection_id = 'r0fqf4rli0n632ypd4la'

print(f"\n{'='*70}")
print(f"  CHECKING CURRENT PERMISSIONS")
print(f"{'='*70}\n")

# Check who I am
sts = boto3.client('sts', region_name=AWS_REGION)
identity = sts.get_caller_identity()
print(f"Current User: {identity['Arn']}")
print(f"Account: {identity['Account']}\n")

# Check data access policy
aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)

try:
    response = aoss.get_access_policy(name='kb-policy-3421', type='data')
    policy = response['accessPolicyDetail']
    
    print(f"Data Access Policy:")
    print(f"  Name: {policy['name']}")
    print(f"  Version: {policy['policyVersion']}")
    
    if isinstance(policy['policy'], str):
        policy_doc = json.loads(policy['policy'])
    else:
        policy_doc = policy['policy']
    
    print(f"\n  Principals with access:")
    for rule in policy_doc:
        for principal in rule.get('Principal', []):
            print(f"    - {principal}")
    
    print(f"\n  Resources:")
    for rule in policy_doc:
        for res_rule in rule.get('Rules', []):
            print(f"    - {res_rule.get('ResourceType')}: {res_rule.get('Resource')}")
            print(f"      Permissions: {', '.join(res_rule.get('Permission', []))}")
    
except Exception as e:
    print(f"❌ Error getting policy: {e}")

# Check collection status
print(f"\n{'='*70}")
print(f"Collection Status:")
try:
    coll_response = aoss.batch_get_collection(ids=[collection_id])
    if coll_response['collectionDetails']:
        coll = coll_response['collectionDetails'][0]
        print(f"  Name: {coll['name']}")
        print(f"  Status: {coll['status']}")
        print(f"  Endpoint: {coll.get('collectionEndpoint')}")
except Exception as e:
    print(f"❌ Error: {e}")

print(f"{'='*70}\n")

# Try to create index
print("Attempting to create index...")
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
    
    index_name = 'bedrock-knowledge-base-default-index'
    
    # Check if exists
    if client.indices.exists(index=index_name):
        print(f"✅ Index already exists!")
    else:
        print(f"📝 Creating index...")
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
        print(f"✅ Index created successfully!")
        print(f"   Result: {result}")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\n💡 This means permissions haven't propagated yet.")
    print(f"   Wait another 10-15 minutes and try again.")

print(f"\n{'='*70}\n")
