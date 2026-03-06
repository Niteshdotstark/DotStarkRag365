"""
Create index by assuming the Bedrock role
This should work because the Bedrock role has the necessary permissions
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
print(f"  CREATING INDEX AS BEDROCK ROLE")
print(f"{'='*70}\n")

print(f"Collection ID: {collection_id}")
print(f"Index Name: {index_name}")
print(f"Bedrock Role: {BEDROCK_ROLE_ARN}\n")

try:
    print("1️⃣  Assuming Bedrock role...")
    
    # Assume the Bedrock role
    sts = boto3.client('sts', region_name=AWS_REGION)
    
    assumed_role = sts.assume_role(
        RoleArn=BEDROCK_ROLE_ARN,
        RoleSessionName='CreateIndexSession',
        DurationSeconds=900  # 15 minutes
    )
    
    credentials = assumed_role['Credentials']
    print(f"   ✅ Assumed role successfully\n")
    
    print("2️⃣  Connecting to OpenSearch with Bedrock role credentials...")
    
    # Create auth with assumed role credentials
    from botocore.credentials import Credentials
    temp_creds = Credentials(
        access_key=credentials['AccessKeyId'],
        secret_key=credentials['SecretAccessKey'],
        token=credentials['SessionToken']
    )
    
    auth = AWSV4SignerAuth(temp_creds, AWS_REGION, 'aoss')
    
    host = f'{collection_id}.{AWS_REGION}.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    print(f"   ✅ Connected to OpenSearch\n")
    
    print("3️⃣  Checking if index exists...")
    if client.indices.exists(index=index_name):
        print(f"   ✅ Index already exists: {index_name}\n")
    else:
        print(f"   ℹ️  Index does not exist, creating...\n")
        
        print("4️⃣  Creating index...")
        
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
    
    print("5️⃣  Verifying index...")
    if client.indices.exists(index=index_name):
        mappings = client.indices.get_mapping(index=index_name)
        print(f"   ✅ Index verified!\n")
    else:
        print(f"   ❌ Index verification failed\n")
        exit(1)
    
    print(f"{'='*70}")
    print(f"  ✅ SUCCESS!")
    print(f"{'='*70}\n")
    print(f"Index '{index_name}' is ready!")
    print(f"\nNow test the crawl:")
    print(f"  sudo docker exec -it fastapi-backend python test_new_crawl.py\n")
    
except Exception as e:
    print(f"\n{'='*70}")
    print(f"  ❌ ERROR")
    print(f"{'='*70}\n")
    print(f"Error: {e}")
    
    import traceback
    traceback.print_exc()
    
    print(f"\n💡 The Bedrock role might not have permission to be assumed.")
    print(f"   Check the role's trust policy allows your IAM user to assume it.")

print(f"\n{'='*70}\n")
