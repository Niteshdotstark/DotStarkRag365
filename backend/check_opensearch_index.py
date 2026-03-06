"""
Check if OpenSearch index exists and create if needed
"""
import boto3
import os
import requests
from requests.auth import AWS4Auth
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def check_and_create_index():
    """Check if the default Bedrock index exists"""
    
    collection_endpoint = 'https://l2gyy0eln3h84ay5st85.ap-south-1.aoss.amazonaws.com'
    index_name = 'bedrock-knowledge-base-default-index'
    
    print(f"\n{'='*70}")
    print(f"  CHECKING OPENSEARCH INDEX")
    print(f"{'='*70}\n")
    
    print(f"Collection Endpoint: {collection_endpoint}")
    print(f"Index Name: {index_name}\n")
    
    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        AWS_REGION,
        'aoss',
        session_token=credentials.token
    )
    
    # Check if index exists
    print("🔍 Checking if index exists...")
    try:
        response = requests.head(
            f'{collection_endpoint}/{index_name}',
            auth=awsauth,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ Index exists\n")
            return True
        elif response.status_code == 404:
            print(f"   ❌ Index does not exist")
            print(f"   📝 Creating index...\n")
            
            # Create index with Bedrock schema
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        "bedrock-knowledge-base-default-vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "name": "hnsw",
                                "engine": "faiss",
                                "parameters": {
                                    "ef_construction": 512,
                                    "m": 16
                                }
                            }
                        },
                        "AMAZON_BEDROCK_TEXT_CHUNK": {
                            "type": "text"
                        },
                        "AMAZON_BEDROCK_METADATA": {
                            "type": "text",
                            "index": False
                        }
                    }
                }
            }
            
            create_response = requests.put(
                f'{collection_endpoint}/{index_name}',
                auth=awsauth,
                json=index_body,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if create_response.status_code in [200, 201]:
                print(f"   ✅ Index created successfully\n")
                return True
            else:
                print(f"   ❌ Failed to create index")
                print(f"   Status: {create_response.status_code}")
                print(f"   Response: {create_response.text}\n")
                return False
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    check_and_create_index()
