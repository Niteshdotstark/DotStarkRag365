#!/usr/bin/env python3
"""
Update database with new collection ID on server.
Run this on the server to update the database.
"""

import os
import sys

# New collection details
COLLECTION_ID = '3wwawnad009sxxxdsnni'
COLLECTION_NAME = 'kb-collection-321'
COLLECTION_ENDPOINT = 'https://3wwawnad009sxxxdsnni.ap-south-1.aoss.amazonaws.com'
SHARED_AGENT_ID = 132
AWS_REGION = 'ap-south-1'
AWS_ACCOUNT_ID = '705406524080'

print("=" * 70)
print("  💾 UPDATE DATABASE WITH NEW COLLECTION")
print("=" * 70)
print()
print(f"Collection ID: {COLLECTION_ID}")
print(f"Collection Name: {COLLECTION_NAME}")
print(f"Agent ID: {SHARED_AGENT_ID}")
print()

try:
    # Import database modules
    from database import SessionLocal
    from models import Agent, AgentCollection
    
    db = SessionLocal()
    
    # Step 1: Ensure agent exists
    print("1️⃣  Checking agent...")
    agent = db.query(Agent).filter_by(id=SHARED_AGENT_ID).first()
    
    if not agent:
        print(f"   📝 Creating agent {SHARED_AGENT_ID}...")
        agent = Agent(
            id=SHARED_AGENT_ID,
            agent_name="Shared Demo Agent (Cost Optimization)"
        )
        db.add(agent)
        db.commit()
        print(f"   ✅ Agent created")
    else:
        print(f"   ✅ Agent {SHARED_AGENT_ID} exists")
    
    print()
    
    # Step 2: Update or create collection record
    print("2️⃣  Updating collection...")
    collection_record = db.query(AgentCollection).filter_by(agent_id=SHARED_AGENT_ID).first()
    
    collection_arn = f"arn:aws:aoss:{AWS_REGION}:{AWS_ACCOUNT_ID}:collection/{COLLECTION_ID}"
    
    if collection_record:
        print(f"   📝 Updating existing record...")
        print(f"      Old Collection ID: {collection_record.collection_id}")
        print(f"      New Collection ID: {COLLECTION_ID}")
        
        collection_record.collection_id = COLLECTION_ID
        collection_record.collection_arn = collection_arn
        collection_record.collection_name = COLLECTION_NAME
        collection_record.collection_endpoint = COLLECTION_ENDPOINT
        
        print(f"   ✅ Record updated")
    else:
        print(f"   📝 Creating new record...")
        collection_record = AgentCollection(
            agent_id=SHARED_AGENT_ID,
            collection_id=COLLECTION_ID,
            collection_arn=collection_arn,
            collection_name=COLLECTION_NAME,
            collection_endpoint=COLLECTION_ENDPOINT
        )
        db.add(collection_record)
        print(f"   ✅ Record created")
    
    db.commit()
    
    print()
    
    # Step 3: Verify
    print("3️⃣  Verifying...")
    verify_record = db.query(AgentCollection).filter_by(agent_id=SHARED_AGENT_ID).first()
    
    if verify_record and verify_record.collection_id == COLLECTION_ID:
        print(f"   ✅ Verification successful!")
        print(f"      Agent ID: {verify_record.agent_id}")
        print(f"      Collection ID: {verify_record.collection_id}")
        print(f"      Collection Name: {verify_record.collection_name}")
    else:
        print(f"   ❌ Verification failed!")
        sys.exit(1)
    
    db.close()
    
    print()
    print("=" * 70)
    print("  ✅ DATABASE UPDATE COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Restart the Docker container:")
    print("     sudo docker-compose restart")
    print()
    print("  2. Test a crawl:")
    print('     curl -X POST "http://localhost:8000/api/crawl/start" \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"agent_id": 532, "website_url": "https://vyauma.com/", "max_pages": 1}\'')
    print()
    print("  3. Check logs:")
    print("     sudo docker logs -f fastapi-backend")
    print()
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print()
    print("Make sure you're running this from the backend directory:")
    print("  cd ~/DotStarkRag365/backend")
    print("  python update_db_collection.py")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
