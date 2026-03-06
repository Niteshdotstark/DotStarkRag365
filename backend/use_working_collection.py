"""
Find and use the collection that actually has working permissions
"""
import boto3
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

print(f"\n{'='*70}")
print(f"  FINDING WORKING COLLECTION")
print(f"{'='*70}\n")

# Check both collections
OLD_COLLECTION_ID = 'l2gyy0eln3h84ay5st85'
NEW_COLLECTION_ID = 'r0fqf4rli0n632ypd4la'

aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)

def check_collection(collection_id, name):
    """Check if a collection exists and has working permissions"""
    print(f"Checking {name} collection: {collection_id}")
    
    try:
        # Check if collection exists
        response = aoss.batch_get_collection(ids=[collection_id])
        if not response['collectionDetails']:
            print(f"   ❌ Collection not found\n")
            return None
        
        coll = response['collectionDetails'][0]
        status = coll['status']
        endpoint = coll.get('collectionEndpoint', '')
        
        print(f"   Status: {status}")
        print(f"   Endpoint: {endpoint}")
        
        if status != 'ACTIVE':
            print(f"   ❌ Collection not ACTIVE\n")
            return None
        
        # Try to access OpenSearch
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
        
        host = endpoint.replace('https://', '').replace('/', '')
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        # Try to list indices
        indices = client.cat.indices(format='json')
        print(f"   ✅ Can access OpenSearch! ({len(indices)} indices)")
        
        # Check if index exists
        index_name = 'bedrock-knowledge-base-default-index'
        if client.indices.exists(index=index_name):
            print(f"   ✅ Index exists: {index_name}\n")
            return {
                'collection_id': collection_id,
                'collection_arn': coll['arn'],
                'collection_name': coll['name'],
                'collection_endpoint': endpoint,
                'has_index': True
            }
        else:
            print(f"   ⚠️  Index does not exist (but we can create it)\n")
            return {
                'collection_id': collection_id,
                'collection_arn': coll['arn'],
                'collection_name': coll['name'],
                'collection_endpoint': endpoint,
                'has_index': False
            }
            
    except Exception as e:
        print(f"   ❌ Cannot access: {e}\n")
        return None

# Check both collections
print("1️⃣  Checking OLD collection...")
old_result = check_collection(OLD_COLLECTION_ID, "OLD")

print("2️⃣  Checking NEW collection...")
new_result = check_collection(NEW_COLLECTION_ID, "NEW")

# Decide which to use
working_collection = None

if old_result and old_result['has_index']:
    print("✅ OLD collection has working permissions AND index!")
    working_collection = old_result
    collection_name = "OLD"
elif new_result and new_result['has_index']:
    print("✅ NEW collection has working permissions AND index!")
    working_collection = new_result
    collection_name = "NEW"
elif old_result:
    print("✅ OLD collection has working permissions (no index yet)")
    working_collection = old_result
    collection_name = "OLD"
elif new_result:
    print("✅ NEW collection has working permissions (no index yet)")
    working_collection = new_result
    collection_name = "NEW"
else:
    print("❌ Neither collection has working permissions!")
    print("\n💡 You need to wait for AWS permissions to propagate.")
    print("   This can take several hours or up to 24 hours.")
    exit(1)

print(f"\n3️⃣  Using {collection_name} collection: {working_collection['collection_id']}")

# Update database
print(f"\n4️⃣  Updating database...")
DATABASE_URL = os.getenv('DATABASE_URI', 'postgresql://postgres:123@postgres_db:5432/multi_tenant_admin')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Update agent_collections
    update_query = text("""
        INSERT INTO agent_collections (agent_id, collection_id, collection_arn, collection_name, collection_endpoint)
        VALUES (3421, :cid, :carn, :cname, :cendpoint)
        ON CONFLICT (agent_id) 
        DO UPDATE SET 
            collection_id = :cid,
            collection_arn = :carn,
            collection_name = :cname,
            collection_endpoint = :cendpoint
    """)
    
    db.execute(update_query, {
        'cid': working_collection['collection_id'],
        'carn': working_collection['collection_arn'],
        'cname': working_collection['collection_name'],
        'cendpoint': working_collection['collection_endpoint']
    })
    db.commit()
    print(f"   ✅ Database updated!\n")
    
except Exception as e:
    print(f"   ❌ Database error: {e}\n")
    db.rollback()
finally:
    db.close()

# Create index if needed
if not working_collection['has_index']:
    print(f"5️⃣  Creating index...")
    try:
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
        
        host = working_collection['collection_endpoint'].replace('https://', '').replace('/', '')
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        
        index_name = 'bedrock-knowledge-base-default-index'
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
        
        client.indices.create(index=index_name, body=index_body)
        print(f"   ✅ Index created!\n")
        
    except Exception as e:
        print(f"   ❌ Index creation failed: {e}\n")
        print(f"   ℹ️  Bedrock will create it automatically\n")

print(f"{'='*70}")
print(f"  ✅ READY TO TEST!")
print(f"{'='*70}\n")
print(f"Collection: {working_collection['collection_name']}")
print(f"ID: {working_collection['collection_id']}")
print(f"Endpoint: {working_collection['collection_endpoint']}")
print(f"\nRun: sudo docker exec -it fastapi-backend python test_new_crawl.py")
print(f"\n{'='*70}\n")
