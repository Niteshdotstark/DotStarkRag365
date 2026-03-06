"""
Fix database with proper timestamp and test crawl
"""
import sys
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('env')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

print(f"\n{'='*70}")
print(f"  FIXING DATABASE AND TESTING")
print(f"{'='*70}\n")

DATABASE_URL = os.getenv('DATABASE_URI', 'postgresql://postgres:123@postgres_db:5432/multi_tenant_admin')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

COLLECTION_ID = 'r0fqf4rli0n632ypd4la'
COLLECTION_ARN = 'arn:aws:aoss:ap-south-1:705406524080:collection/r0fqf4rli0n632ypd4la'
COLLECTION_NAME = 'kb-collection-3421'
COLLECTION_ENDPOINT = 'https://r0fqf4rli0n632ypd4la.ap-south-1.aoss.amazonaws.com'

try:
    print("1️⃣  Fixing database with proper timestamp...")
    
    # Delete existing entry if any
    db.execute(text("DELETE FROM agent_collections WHERE agent_id = 3421"))
    db.commit()
    
    # Insert with timestamp
    insert_query = text("""
        INSERT INTO agent_collections 
        (agent_id, collection_id, collection_arn, collection_name, collection_endpoint, created_at)
        VALUES (3421, :cid, :carn, :cname, :cendpoint, :created_at)
    """)
    
    db.execute(insert_query, {
        'cid': COLLECTION_ID,
        'carn': COLLECTION_ARN,
        'cname': COLLECTION_NAME,
        'cendpoint': COLLECTION_ENDPOINT,
        'created_at': datetime.utcnow()
    })
    db.commit()
    
    print(f"   ✅ Database updated successfully!\n")
    
    # Verify
    result = db.execute(text("SELECT * FROM agent_collections WHERE agent_id = 3421"))
    row = result.fetchone()
    
    if row:
        print(f"   Verified:")
        print(f"   - Agent ID: {row.agent_id}")
        print(f"   - Collection ID: {row.collection_id}")
        print(f"   - Collection Name: {row.collection_name}")
        print(f"   - Created At: {row.created_at}\n")
    
    print(f"{'='*70}")
    print(f"  ✅ DATABASE FIXED!")
    print(f"{'='*70}\n")
    
    print("The system is now configured to use the new collection.")
    print("Bedrock will create the index automatically when needed.\n")
    
    print("Next step: Test the crawl")
    print("Run: sudo docker exec -it fastapi-backend python test_new_crawl.py\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    
finally:
    db.close()

print(f"{'='*70}\n")
