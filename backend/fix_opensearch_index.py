"""
Fix OpenSearch index for existing collections
"""
import boto3
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from database import get_db
from models import AgentCollection

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def create_index_for_collection(collection_endpoint: str, collection_name: str):
    """Create the bedrock index in an OpenSearch collection"""
    
    print(f"\n📊 Creating index for collection: {collection_name}")
    print(f"   Endpoint: {collection_endpoint}")
    
    try:
        # Get AWS credentials for signing requests
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
        
        # Connect to OpenSearch Serverless
        host = collection_endpoint.replace('https://', '').replace('/', '')
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        
        # Create the vector index that Bedrock will use
        index_name = 'bedrock-knowledge-base-default-index'
        
        # Check if index exists
        if client.indices.exists(index=index_name):
            print(f"   ✅ Index already exists: {index_name}")
            return True
        
        # Create index with vector search configuration
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
        print(f"   ✅ Created vector index: {index_name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating index: {e}")
        return False

def fix_all_collections():
    """Fix indexes for all collections in database"""
    
    db = next(get_db())
    
    try:
        # Get all agent collections
        collections = db.query(AgentCollection).all()
        
        if not collections:
            print("❌ No collections found in database")
            return
        
        print(f"\n{'='*60}")
        print(f"Found {len(collections)} collection(s)")
        print(f"{'='*60}")
        
        success_count = 0
        for collection in collections:
            if create_index_for_collection(collection.collection_endpoint, collection.collection_name):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully fixed {success_count}/{len(collections)} collections")
        print(f"{'='*60}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_collections()
