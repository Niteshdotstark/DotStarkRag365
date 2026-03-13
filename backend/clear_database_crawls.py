#!/usr/bin/env python3
"""
Clear all website crawl records from the database.
Run this after cleaning up AWS resources.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URI') or os.getenv('DATABASE_URL')

def clear_crawl_records():
    """Clear all website crawl records"""
    from models import WebsiteCrawl
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🔍 Counting website crawl records...")
        count = db.query(WebsiteCrawl).count()
        print(f"   Found {count} record(s)")
        
        if count == 0:
            print("✅ Database is already clean")
            return
        
        print()
        confirm = input(f"Delete all {count} crawl record(s)? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        print("\n🗑️  Deleting records...")
        deleted = db.query(WebsiteCrawl).delete()
        db.commit()
        
        print(f"✅ Deleted {deleted} record(s)")
        print("💡 Database is now clean and ready for fresh crawls")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️  CLEAR DATABASE CRAWL RECORDS")
    print("=" * 60)
    print()
    clear_crawl_records()
