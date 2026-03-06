"""
Create OpenSearch index using AWS credentials directly
This should work now that permissions have propagated
"""
import boto3
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import json

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
collection_id = 'r0fqf4rli0n632ypd4la'
index_name = 'bedrock-knowledge-base-default-index'

print(f"\n{'='*70}")
print(f"  CREATING OPENSEARCH INDEX VIA AWS")
print(f"{'='*70}\n")

print(f"Collection ID: {collection_id}")
print(f"Index Name: {index_name}")
print(f"Region: {AWS_REGION}\n")

try:
    # Get AWS credentials
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    
    # Connect to OpenSearch
    host = f'{collection_id}.{AWS_REGION}.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    print("1️⃣  Checking if index already exists...")
    if client.indices.exists(index=index_name):
        print(f"   ✅ Index already exists: {index_name}")
        
        # Get index info
        info = client.indices.get(index=index_name)
        print(f"\n   Index details:")
        print(f"   {json.dumps(info, indent=2)}\n")
        
    else:
        print(f"   ℹ️  Index does not exist, creating...\n")
        
        print("2️⃣  Creating index with vector configuration...")
        
        # Create index with exact Bedrock requirements
        index_body = {
            "settings": {
                "index.knn": True,
                "index.knn.algo_param.ef_search": 512
            },
            "mappings": {
                "properties": {
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "engine": "faiss",
                            "name": "hnsw",
                            "space_type": "l2",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    "AMAZON_BEDROCK_TEXT_CHUNK": {
                        "type": "text",
                        "index": True
                    },
                    "AMAZON_BEDROCK_METADATA": {
                        "type": "text",
                        "index": False
                    }
                }
            }
        }
        
        result = client.indices.create(index=index_name, body=index_body)
        print(f"   ✅ Index created successfully!")
        print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    print("3️⃣  Verifying index...")
    
    # Verify the index exists and has correct mappings
    if client.indices.exists(index=index_name):
        mappings = client.indices.get_mapping(index=index_name)
        print(f"   ✅ Index verified!")
        print(f"\n   Mappings:")
        print(f"   {json.dumps(mappings, indent=2)}\n")
    else:
        print(f"   ❌ Index verification failed\n")
        exit(1)
    
    print(f"{'='*70}")
    print(f"  ✅ SUCCESS!")
    print(f"{'='*70}\n")
    print(f"Index '{index_name}' is ready for Bedrock Knowledge Bases!")
    print(f"\nYou can now create knowledge bases and start crawls.")
    
except Exception as e:
    print(f"\n{'='*70}")
    print(f"  ❌ ERROR")
    print(f"{'='*70}\n")
    print(f"Error: {e}")
    
    import traceback
    traceback.print_exc()
    
    print(f"\n💡 Troubleshooting:")
    print(f"   1. Check if permissions have propagated (may take hours)")
    print(f"   2. Verify data access policy includes your IAM user")
    print(f"   3. Check collection is ACTIVE")
    print(f"   4. Try again in 10-15 minutes")

print(f"\n{'='*70}\n")
