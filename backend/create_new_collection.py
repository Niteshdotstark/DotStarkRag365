"""
Create a new OpenSearch collection with proper index for Bedrock
"""
import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')

def create_collection_with_index():
    """Create OpenSearch collection and index"""
    
    agent_id = 3421
    collection_name = f"kb-collection-{agent_id}"
    
    print(f"\n{'='*70}")
    print(f"  CREATING OPENSEARCH COLLECTION WITH INDEX")
    print(f"{'='*70}\n")
    
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    # Step 1: Create encryption policy
    print("1️⃣  Creating encryption policy...")
    encryption_policy_name = f"kb-encryption-{agent_id}"
    try:
        aoss_client.create_security_policy(
            name=encryption_policy_name,
            type='encryption',
            policy=f'''{{"Rules":[{{"ResourceType":"collection","Resource":["collection/{collection_name}"]}}],"AWSOwnedKey":true}}'''
        )
        print(f"   ✅ Created: {encryption_policy_name}\n")
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"   ℹ️  Already exists: {encryption_policy_name}\n")
        else:
            print(f"   ❌ Error: {e}\n")
            return False
    
    # Step 2: Create network policy
    print("2️⃣  Creating network policy...")
    network_policy_name = f"kb-network-{agent_id}"
    try:
        aoss_client.create_security_policy(
            name=network_policy_name,
            type='network',
            policy=f'''[{{"Rules":[{{"ResourceType":"collection","Resource":["collection/{collection_name}"]}}],"AllowFromPublic":true}}]'''
        )
        print(f"   ✅ Created: {network_policy_name}\n")
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"   ℹ️  Already exists: {network_policy_name}\n")
        else:
            print(f"   ❌ Error: {e}\n")
            return False
    
    # Step 3: Create data access policy
    print("3️⃣  Creating data access policy...")
    policy_name = f"kb-policy-{agent_id}"
    
    # Get current user ARN
    sts_client = boto3.client('sts', region_name=AWS_REGION)
    current_user_arn = sts_client.get_caller_identity()['Arn']
    
    try:
        aoss_client.create_access_policy(
            name=policy_name,
            type='data',
            policy=f'''[{{
                "Rules": [
                    {{
                        "ResourceType": "collection",
                        "Resource": ["collection/{collection_name}"],
                        "Permission": ["aoss:*"]
                    }},
                    {{
                        "ResourceType": "index",
                        "Resource": ["index/{collection_name}/*"],
                        "Permission": ["aoss:*"]
                    }}
                ],
                "Principal": ["{BEDROCK_ROLE_ARN}", "{current_user_arn}", "arn:aws:iam::{AWS_ACCOUNT_ID}:root"]
            }}]'''
        )
        print(f"   ✅ Created: {policy_name}\n")
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"   ℹ️  Already exists: {policy_name}\n")
        else:
            print(f"   ❌ Error: {e}\n")
            return False
    
    # Step 4: Create collection
    print("4️⃣  Creating collection...")
    try:
        response = aoss_client.create_collection(
            name=collection_name,
            type='VECTORSEARCH',
            description=f'Knowledge base collection for agent {agent_id}'
        )
        
        collection_id = response['createCollectionDetail']['id']
        print(f"   ✅ Collection created: {collection_id}")
        print(f"   ⏳ Waiting for collection to become ACTIVE (this takes 3-5 minutes)...\n")
        
    except Exception as e:
        if 'ConflictException' in str(e):
            print(f"   ℹ️  Collection already exists, fetching details...")
            list_response = aoss_client.list_collections(
                collectionFilters={'name': collection_name}
            )
            if list_response.get('collectionSummaries'):
                collection_id = list_response['collectionSummaries'][0]['id']
                print(f"   ✅ Found: {collection_id}\n")
            else:
                print(f"   ❌ Could not find collection\n")
                return False
        else:
            print(f"   ❌ Error: {e}\n")
            return False
    
    # Step 5: Wait for collection to become ACTIVE
    max_wait = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        collection_response = aoss_client.batch_get_collection(ids=[collection_id])
        if collection_response['collectionDetails']:
            collection_status = collection_response['collectionDetails'][0]['status']
            elapsed = int(time.time() - start_time)
            
            if collection_status == 'ACTIVE':
                collection_endpoint = collection_response['collectionDetails'][0].get('collectionEndpoint')
                print(f"5️⃣  Collection is ACTIVE (took {elapsed} seconds)")
                print(f"   📍 Endpoint: {collection_endpoint}\n")
                break
            elif collection_status == 'FAILED':
                print(f"   ❌ Collection creation failed\n")
                return False
            else:
                print(f"   ⏳ Status: {collection_status} ({elapsed}s elapsed)")
        
        time.sleep(10)
    else:
        print(f"   ⚠️  Timeout waiting for collection\n")
        return False
    
    # Step 6: Wait for permissions to propagate
    print("6️⃣  Waiting for permissions to propagate (120 seconds)...")
    time.sleep(120)
    print(f"   ✅ Permissions should be ready\n")
    
    # Step 6.5: Update data access policy with actual collection ID
    print("6.5️⃣  Updating data access policy with collection ID...")
    try:
        # Get current policy version
        policy_response = aoss_client.get_access_policy(name=policy_name, type='data')
        policy_version = policy_response['accessPolicyDetail']['policyVersion']
        
        # Update with actual collection ID
        aoss_client.update_access_policy(
            name=policy_name,
            type='data',
            policyVersion=policy_version,
            policy=f'''[{{
                "Rules": [
                    {{
                        "ResourceType": "collection",
                        "Resource": ["collection/{collection_id}"],
                        "Permission": ["aoss:*"]
                    }},
                    {{
                        "ResourceType": "index",
                        "Resource": ["index/{collection_id}/*"],
                        "Permission": ["aoss:*"]
                    }}
                ],
                "Principal": ["{BEDROCK_ROLE_ARN}", "{current_user_arn}", "arn:aws:iam::{AWS_ACCOUNT_ID}:root"]
            }}]'''
        )
        print(f"   ✅ Policy updated with collection ID\n")
        
        # Wait again for policy update to propagate
        print("   ⏳ Waiting 30 more seconds for policy update...")
        time.sleep(30)
        print(f"   ✅ Ready\n")
        
    except Exception as e:
        print(f"   ⚠️  Could not update policy: {e}\n")
        print(f"   ℹ️  Continuing anyway...\n")
    
    # Step 7: Create the vector index
    print("7️⃣  Creating vector index in OpenSearch...")
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
        
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
        
        host = collection_endpoint.replace('https://', '').replace('/', '')
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        
        index_name = 'bedrock-knowledge-base-default-index'
        
        if client.indices.exists(index=index_name):
            print(f"   ℹ️  Index already exists: {index_name}\n")
        else:
            index_body = {
                "settings": {
                    "index.knn": True
                },
                "mappings": {
                    "properties": {
                        "bedrock-knowledge-base-default-vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "engine": "faiss",
                                "name": "hnsw"
                            }
                        },
                        "AMAZON_BEDROCK_TEXT_CHUNK": {
                            "type": "text"
                        },
                        "AMAZON_BEDROCK_METADATA": {
                            "type": "text"
                        }
                    }
                }
            }
            
            client.indices.create(index=index_name, body=index_body)
            print(f"   ✅ Index created: {index_name}\n")
    
    except Exception as e:
        print(f"   ❌ Error creating index: {e}\n")
        return False
    
    print(f"{'='*70}")
    print("✅ COLLECTION AND INDEX CREATED SUCCESSFULLY!")
    print(f"{'='*70}")
    print(f"\nCollection ID: {collection_id}")
    print(f"Collection Endpoint: {collection_endpoint}")
    print(f"Index Name: {index_name}")
    print(f"\n💡 You can now create knowledge bases and start crawling!\n")
    
    return True

if __name__ == "__main__":
    create_collection_with_index()
