"""
Quick script to check database configuration and location
"""
from database import engine, DATABASE_URL
from sqlalchemy import inspect, text
import os

def check_database():
    """Check database type and configuration"""
    
    print("=" * 60)
    print("Database Configuration Check")
    print("=" * 60)
    
    print(f"\nDatabase URL: {DATABASE_URL}")
    print(f"Engine: {engine}")
    print(f"Dialect: {engine.dialect.name}")
    
    # Check if database file exists (for SQLite)
    if 'sqlite' in str(DATABASE_URL).lower():
        db_path = str(DATABASE_URL).replace('sqlite:///', '')
        print(f"\nSQLite database path: {db_path}")
        print(f"Database file exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"Database file size: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    # Check tables
    print("\n" + "=" * 60)
    print("Database Tables")
    print("=" * 60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Check tenants table structure
    if 'tenants' in tables:
        print("\n" + "=" * 60)
        print("Tenants Table Structure")
        print("=" * 60)
        
        columns = inspector.get_columns('tenants')
        print(f"\n{'Column Name':<25} {'Type':<20} {'Nullable':<10}")
        print("-" * 60)
        for col in columns:
            col_type = str(col['type'])
            nullable = "Yes" if col['nullable'] else "No"
            print(f"{col['name']:<25} {col_type:<20} {nullable:<10}")
        
        # Check data
        print("\n" + "=" * 60)
        print("Tenant Data (fb_verify_token column)")
        print("=" * 60)
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, name, fb_verify_token 
                    FROM tenants 
                    ORDER BY id
                """))
                
                print(f"\n{'ID':<5} {'Name':<20} {'Token':<30} {'Length':<10}")
                print("-" * 70)
                
                for row in result:
                    token = row[2] if row[2] else "NULL"
                    token_len = len(row[2]) if row[2] else 0
                    # Truncate display if too long
                    token_display = token[:27] + "..." if len(token) > 30 else token
                    print(f"{row[0]:<5} {row[1]:<20} {token_display:<30} {token_len:<10}")
                    
        except Exception as e:
            print(f"Error reading data: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_database()
