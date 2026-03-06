"""
Fix: Update database to use the new collection ID
The database still has the old collection ID stored
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv('env')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

print(f"\n{'='*70}")
print(f"  FIXING DATABASE COLLECTION ID")
print(f"{'='*70}\n")

# Database setup
DATABASE_URL = os.getenv('DATABASE_URI', 'postgresql://postgres:123@postgres_db:5432/multi_tenant_admin')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

OLD_COLLECTION_ID = 'l2gyy0eln3h84ay5st85'
NEW_COLLECTION_ID = 'r0fqf4rli0n632ypd4la'
NEW_COLLECTION_NAME = 'kb-collection-3421'
NEW_COLLECTION_ARN = f'arn:aws:aoss:ap-south-1:705406524080:collection/{NEW_COLLECTION_ID}'
NEW_COLLECTION_ENDPOINT = f'https://{NEW_COLLECTION_ID}.ap-south-1.aoss.amazonaws.com'

try:
    print("1️⃣  Checking current collection in database...")
    
    # Check agent_collections table
    result = db.execute(text("SELECT * FROM agent_collections WHERE agent_id = 3421"))
    row = result.fetchone()
    
    if row:
        print(f"   Found collection for agent 3421:")
        print(f"   Collection ID: {row.collection_id}")
        print(f"   Collection Name: {row.collection_name}")
        print(f"   Collection Endpoint: {row.collection_endpoint}\n")
        
        if row.collection_id == OLD_COLLECTION_ID:
            print("   ⚠️  Using OLD collection ID - needs update!\n")
            
            print("2️⃣  Updating to new collection...")
            
            update_query = text("""
                UPDATE agent_collections 
                SET 
                    collection_id = :new_id,
                    collection_arn = :new_arn,
                    collection_name = :new_name,
                    collection_endpoint = :new_endpoint
                WHERE agent_id = 3421
            """)
            
            db.execute(update_query, {
                'new_id': NEW_COLLECTION_ID,
                'new_arn': NEW_COLLECTION_ARN,
                'new_name': NEW_COLLECTION_NAME,
                'new_endpoint': NEW_COLLECTION_ENDPOINT
            })
            db.commit()
            
            print(f"   ✅ Updated to new collection!")
            print(f"   New Collection ID: {NEW_COLLECTION_ID}")
            print(f"   New Endpoint: {NEW_COLLECTION_ENDPOINT}\n")
            
        elif row.collection_id == NEW_COLLECTION_ID:
            print("   ✅ Already using new collection ID!\n")
        else:
            print(f"   ⚠️  Unknown collection ID: {row.collection_id}\n")
    else:
        print("   ℹ️  No collection found for agent 3421")
        print("   Will be created on next crawl\n")
    
    # Also check tenant_collections for backward compatibility
    print("3️⃣  Checking tenant_collections table...")
    result = db.execute(text("SELECT * FROM tenant_collections"))
    rows = result.fetchall()
    
    if rows:
        print(f"   Found {len(rows)} tenant collections:")
        for row in rows:
            print(f"   - Tenant {row.tenant_id}: {row.collection_id}")
            
            if row.collection_id == OLD_COLLECTION_ID:
                print(f"     ⚠️  Updating tenant {row.tenant_id} to new collection...")
                
                update_query = text("""
                    UPDATE tenant_collections 
                    SET 
                        collection_id = :new_id,
                        collection_arn = :new_arn,
                        collection_name = :new_name,
                        collection_endpoint = :new_endpoint
                    WHERE tenant_id = :tenant_id
                """)
                
                db.execute(update_query, {
                    'new_id': NEW_COLLECTION_ID,
                    'new_arn': NEW_COLLECTION_ARN,
                    'new_name': NEW_COLLECTION_NAME,
                    'new_endpoint': NEW_COLLECTION_ENDPOINT,
                    'tenant_id': row.tenant_id
                })
                db.commit()
                print(f"     ✅ Updated!\n")
    else:
        print("   ℹ️  No tenant collections found\n")
    
    print(f"{'='*70}")
    print(f"  ✅ DATABASE UPDATED!")
    print(f"{'='*70}\n")
    print(f"Old Collection: {OLD_COLLECTION_ID}")
    print(f"New Collection: {NEW_COLLECTION_ID}")
    print(f"\nThe system will now use the new collection for all crawls.")
    
except Exception as e:
    print(f"\n{'='*70}")
    print(f"  ❌ ERROR")
    print(f"{'='*70}\n")
    print(f"Error: {e}")
    
    import traceback
    traceback.print_exc()
    
    db.rollback()
    
finally:
    db.close()

print(f"\n{'='*70}\n")
