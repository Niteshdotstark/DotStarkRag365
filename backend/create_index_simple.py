"""
Create OpenSearch index for Bedrock using opensearchpy
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def create_index():
    """Create the Bedrock index in OpenSearch"""
    
    collection_endpoint = 'https://l2gyy0eln3h84ay5st85.ap-south-1.aoss.amazonaws.com'
    index_name = 'bedrock-knowledge-base-default-index'
    
    print(f"\n{'='*70}")
    print(f"  CREATING OPENSEARCH INDEX")
    print(f"{'='*70}\n")
    
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
        
        # Get AWS credentials
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
        
        # Connect to OpenSearch
        host = collection_endpoint.replace('https://', '').replace('/', '')
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        
        print(f"Collection: {host}")
        print(f"Index: {index_name}\n")
        
        # Check if index exists
        if client.indices.exists(index=index_name):
            print(f"✅ Index already exists\n")
            return True
        
        print(f"📝 Creating index...")
        
        # Create index
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
        print(f"✅ Index created successfully\n")
        
        print(f"{'='*70}\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        print(f"{'='*70}\n")
        return False

if __name__ == "__main__":
    create_index()
