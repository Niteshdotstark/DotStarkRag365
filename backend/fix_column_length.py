"""
Script to fix the fb_verify_token column length issue
This will alter the database column to support longer strings
"""
from database import engine
from sqlalchemy import text
import sys

def fix_column_length():
    """Fix the fb_verify_token column to support longer strings"""
    
    print("=" * 60)
    print("Fixing fb_verify_token column length")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Check database type
            db_url = str(engine.url)
            print(f"Database URL: {db_url}")
            
            if 'sqlite' in db_url.lower():
                print("\nDetected SQLite database")
                print("SQLite doesn't support ALTER COLUMN directly.")
                print("We need to recreate the table...")
                
                # For SQLite, we need to recreate the table
                print("\nStep 1: Creating backup of tenants table...")
                conn.execute(text("""
                    CREATE TABLE tenants_backup AS SELECT * FROM tenants
                """))
                conn.commit()
                
                print("Step 2: Dropping original table...")
                conn.execute(text("DROP TABLE tenants"))
                conn.commit()
                
                print("Step 3: Creating new table with correct column sizes...")
                conn.execute(text("""
                    CREATE TABLE tenants (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        fb_url VARCHAR(500),
                        insta_url VARCHAR(500),
                        fb_verify_token VARCHAR(255),
                        fb_access_token VARCHAR(500),
                        insta_access_token VARCHAR(500),
                        telegram_bot_token VARCHAR(255),
                        telegram_chat_id VARCHAR(255),
                        created_at TIMESTAMP,
                        creator_id INTEGER NOT NULL,
                        FOREIGN KEY (creator_id) REFERENCES users(id)
                    )
                """))
                conn.commit()
                
                print("Step 4: Restoring data from backup...")
                conn.execute(text("""
                    INSERT INTO tenants 
                    SELECT * FROM tenants_backup
                """))
                conn.commit()
                
                print("Step 5: Dropping backup table...")
                conn.execute(text("DROP TABLE tenants_backup"))
                conn.commit()
                
            elif 'postgresql' in db_url.lower():
                print("\nDetected PostgreSQL database")
                print("Altering column type...")
                
                conn.execute(text("""
                    ALTER TABLE tenants 
                    ALTER COLUMN fb_verify_token TYPE VARCHAR(255)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    ALTER COLUMN fb_access_token TYPE VARCHAR(500)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    ALTER COLUMN insta_access_token TYPE VARCHAR(500)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    ALTER COLUMN telegram_bot_token TYPE VARCHAR(255)
                """))
                conn.commit()
                
            elif 'mysql' in db_url.lower():
                print("\nDetected MySQL database")
                print("Altering column type...")
                
                conn.execute(text("""
                    ALTER TABLE tenants 
                    MODIFY COLUMN fb_verify_token VARCHAR(255)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    MODIFY COLUMN fb_access_token VARCHAR(500)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    MODIFY COLUMN insta_access_token VARCHAR(500)
                """))
                conn.execute(text("""
                    ALTER TABLE tenants 
                    MODIFY COLUMN telegram_bot_token VARCHAR(255)
                """))
                conn.commit()
            
            print("\n✅ Column length fixed successfully!")
            print("\nNow you need to:")
            print("1. Update tenant 7's fb_verify_token through your API")
            print("2. Test the webhook verification again")
            
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  If this fails, you may need to:")
        print("1. Backup your data")
        print("2. Drop and recreate the database")
        print("3. Restore your data")

if __name__ == "__main__":
    response = input("This will modify your database structure. Continue? (yes/no): ")
    if response.lower() == 'yes':
        fix_column_length()
    else:
        print("Operation cancelled.")
