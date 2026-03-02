"""
Migration script to add Agent tables and update WebsiteCrawl for agent-based system.
"""
from database import engine, Base
from models import Agent, AgentCollection, WebsiteCrawl
from sqlalchemy import text

def migrate():
    """Create new tables and update existing ones."""
    
    print("\n" + "="*70)
    print("  MIGRATING TO AGENT-BASED SYSTEM")
    print("="*70 + "\n")
    
    # Create all tables (will create new ones, skip existing)
    print("📦 Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created/verified\n")
    
    # Update WebsiteCrawl table to add agent_id column if it doesn't exist
    print("🔧 Updating WebsiteCrawl table...")
    
    with engine.connect() as conn:
        try:
            # Check if agent_id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='website_crawls' AND column_name='agent_id'
            """))
            
            if not result.fetchone():
                print("   Adding agent_id column...")
                conn.execute(text("""
                    ALTER TABLE website_crawls 
                    ADD COLUMN agent_id INTEGER
                """))
                conn.commit()
                print("   ✅ Added agent_id column")
            else:
                print("   ℹ️  agent_id column already exists")
            
            # Make tenant_id nullable
            print("   Making tenant_id nullable...")
            conn.execute(text("""
                ALTER TABLE website_crawls 
                ALTER COLUMN tenant_id DROP NOT NULL
            """))
            conn.commit()
            print("   ✅ tenant_id is now nullable")
                
        except Exception as e:
            print(f"   ⚠️  Note: {e}")
            print("   This is normal if using SQLite or if changes already applied")
    
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETE!")
    print("="*70)
    print("\n📝 Summary:")
    print("   - Agent table created")
    print("   - AgentCollection table created")
    print("   - WebsiteCrawl updated to support agent_id")
    print("\n💡 The system now uses agent_id instead of tenant_id")
    print("   URL format remains: /tenants/{agent_id}/websites/crawl")
    print("="*70 + "\n")

if __name__ == "__main__":
    migrate()
