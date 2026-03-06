"""
Direct test of knowledge base creation without API server
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv('env')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Agent
from rag_model.rag_website import create_or_get_opensearch_collection, create_or_get_knowledge_base

print(f"\n{'='*70}")
print(f"  DIRECT KNOWLEDGE BASE CREATION TEST")
print(f"{'='*70}\n")

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/chatbot_db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Test agent ID
    test_agent_id = 999
    
    # Ensure test agent exists
    agent = db.query(Agent).filter_by(id=test_agent_id).first()
    if not agent:
        print(f"Creating test agent {test_agent_id}...")
        agent = Agent(id=test_agent_id, agent_name="Test Agent 999")
        db.add(agent)
        db.commit()
        print(f"✅ Test agent created\n")
    else:
        print(f"✅ Test agent exists\n")
    
    # Step 1: Get or create OpenSearch collection
    print("📦 Step 1: Creating/getting OpenSearch collection...")
    collection = create_or_get_opensearch_collection(test_agent_id, db)
    print(f"✅ Collection ready: {collection['collection_id']}")
    print(f"   Endpoint: {collection['collection_endpoint']}\n")
    
    # Step 2: Create or get knowledge base
    print("🧠 Step 2: Creating/getting Knowledge Base...")
    kb = create_or_get_knowledge_base(test_agent_id, collection['collection_arn'], db)
    print(f"✅ Knowledge Base ready: {kb['knowledge_base_id']}")
    print(f"   Name: {kb['name']}\n")
    
    print(f"{'='*70}")
    print(f"  ✅ SUCCESS!")
    print(f"{'='*70}\n")
    print(f"Knowledge Base ID: {kb['knowledge_base_id']}")
    print(f"Collection ID: {collection['collection_id']}")
    print(f"\nYou can now use this KB to crawl websites!")
    
except Exception as e:
    print(f"\n{'='*70}")
    print(f"  ❌ ERROR")
    print(f"{'='*70}\n")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    db.close()

print(f"\n{'='*70}\n")
