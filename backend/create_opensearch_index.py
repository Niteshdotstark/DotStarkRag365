"""
Manually create the OpenSearch vector index for Bedrock.
"""
import boto3
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def create_index():
    """Create the vector index in OpenSearch."""
    
    tenant_id = 1
    collection_name = f"kb-collection-{tenant_id}"
    
    print(f"\n📊 Creating OpenSearch Vector Index")
    print(f"   Collection: {collection_name}\n")
    
    # Get collection endpoint
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    try:
        response = aoss_client.batch_get_collection(names=[collection_name])
        if not response['collectionDetails']:
            print(f"❌ Collection not found: {collection_name}")
            return False
            
        collection_endpoint = response['collectionDetails'][0]['collectionEndpoint']
        print(f"   Collection endpoint: {collection_endpoint}")
        
    except Exception as e:
        print(f"❌ Error getting collection: {e}")
        return False
    
    # Get AWS credentials for signing requests
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    
    # Create OpenSearch client
    host = collection_endpoint.replace('https://', '')
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    # Create the vector index that Bedrock will use
    index_name = 'bedrock-knowledge-base-default-index'
    
    try:
        if client.indices.exists(index=index_name):
            print(f"   ℹ️  Index already exists: {index_name}")
            print(f"   Deleting and recreating...")
            client.indices.delete(index=index_name)
        
        # Create index with vector search configuration
        index_body = {
            "settings": {
                "index.knn": True,
                "number_of_shards": 2,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "engine": "faiss",  # Changed from nmslib to faiss
                            "space_type": "l2",  # Changed from cosinesimil to l2
                            "name": "hnsw"
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
        
        client.indices.create(index=index_name, body=index_body)
        print(f"   ✅ Created vector index: {index_name}")
        
        # Verify index was created
        if client.indices.exists(index=index_name):
            print(f"   ✅ Verified index exists")
            
            # Get index info
            info = client.indices.get(index=index_name)
            print(f"\n   Index Configuration:")
            print(f"   - Shards: {info[index_name]['settings']['index']['number_of_shards']}")
            print(f"   - Replicas: {info[index_name]['settings']['index']['number_of_replicas']}")
            print(f"   - KNN enabled: {info[index_name]['settings']['index'].get('knn', False)}")
        
        print(f"\n{'='*60}")
        print("✅ OpenSearch index created successfully!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating index: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_index()
