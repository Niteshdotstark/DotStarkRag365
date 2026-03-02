"""
PostgreSQL-specific script to check and fix the fb_verify_token column
"""
from database import engine
from sqlalchemy import text
import sys

def check_postgres_column():
    """Check the actual column definition in PostgreSQL"""
    
    print("=" * 60)
    print("PostgreSQL Column Check for fb_verify_token")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Get column information
            print("\nStep 1: Checking column definition...")
            result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'tenants' 
                AND column_name IN ('fb_verify_token', 'fb_access_token', 'insta_access_token', 'telegram_bot_token')
                ORDER BY column_name
            """))
            
            print(f"\n{'Column Name':<25} {'Data Type':<15} {'Max Length':<12} {'Nullable':<10}")
            print("-" * 70)
            
            columns_info = {}
            for row in result:
                col_name = row[0]
                data_type = row[1]
                max_length = row[2] if row[2] else "unlimited"
                nullable = row[3]
                columns_info[col_name] = {
                    'type': data_type,
                    'length': row[2],
                    'nullable': nullable
                }
                print(f"{col_name:<25} {data_type:<15} {str(max_length):<12} {nullable:<10}")
            
            # Check if column is too short
            print("\n" + "=" * 60)
            print("Analysis")
            print("=" * 60)
            
            fb_token_col = columns_info.get('fb_verify_token')
            if fb_token_col:
                if fb_token_col['length'] and fb_token_col['length'] < 50:
                    print(f"\n❌ PROBLEM FOUND!")
                    print(f"fb_verify_token column max length is {fb_token_col['length']}")
                    print(f"This is too short for tokens like 'chatbottoken@3420' (18 chars)")
                    print(f"\nRecommended fix: Increase to VARCHAR(255)")
                elif fb_token_col['length'] is None:
                    print(f"\n⚠️  Column has unlimited length (TEXT type)")
                    print(f"This should work, but let's check the actual data...")
                else:
                    print(f"\n✅ Column length ({fb_token_col['length']}) should be sufficient")
            
            # Check actual data
            print("\n" + "=" * 60)
            print("Step 2: Checking actual data in database")
            print("=" * 60)
            
            result = conn.execute(text("""
                SELECT 
                    id, 
                    name, 
                    fb_verify_token,
                    LENGTH(fb_verify_token) as token_length
                FROM tenants 
                ORDER BY id
            """))
            
            print(f"\n{'ID':<5} {'Name':<20} {'Token':<35} {'Length':<10}")
            print("-" * 75)
            
            tenant_7_found = False
            for row in result:
                tenant_id = row[0]
                name = row[1]
                token = row[2] if row[2] else "NULL"
                token_len = row[3] if row[3] else 0
                
                # Truncate display if too long
                token_display = (token[:32] + "...") if len(token) > 35 else token
                print(f"{tenant_id:<5} {name:<20} {token_display:<35} {token_len:<10}")
                
                if tenant_id == 7:
                    tenant_7_found = True
                    if token == "d":
                        print(f"\n❌ CONFIRMED: Tenant 7 has truncated token 'd'")
                    elif token_len < 10:
                        print(f"\n⚠️  Tenant 7 token seems too short: '{token}'")
            
            if not tenant_7_found:
                print(f"\n⚠️  Tenant 7 not found in database")
            
            # Offer to fix
            print("\n" + "=" * 60)
            print("Step 3: Fix Options")
            print("=" * 60)
            
            if fb_token_col and fb_token_col['length'] and fb_token_col['length'] < 50:
                print("\nWould you like to fix the column length now?")
                print("This will run: ALTER TABLE tenants ALTER COLUMN fb_verify_token TYPE VARCHAR(255)")
                response = input("\nProceed with fix? (yes/no): ")
                
                if response.lower() == 'yes':
                    print("\nApplying fix...")
                    conn.execute(text("""
                        ALTER TABLE tenants ALTER COLUMN fb_verify_token TYPE VARCHAR(255)
                    """))
                    conn.execute(text("""
                        ALTER TABLE tenants ALTER COLUMN fb_access_token TYPE VARCHAR(500)
                    """))
                    conn.execute(text("""
                        ALTER TABLE tenants ALTER COLUMN insta_access_token TYPE VARCHAR(500)
                    """))
                    conn.execute(text("""
                        ALTER TABLE tenants ALTER COLUMN telegram_bot_token TYPE VARCHAR(255)
                    """))
                    conn.commit()
                    
                    print("✅ Columns updated successfully!")
                    print("\nNext steps:")
                    print("1. Restart your FastAPI application")
                    print("2. Update tenant 7's fb_verify_token through your admin UI")
                    print("3. Test webhook verification again")
                else:
                    print("Fix cancelled.")
            else:
                print("\nColumn length appears OK. The issue might be elsewhere.")
                print("\nPossible causes:")
                print("1. Application code is truncating the value")
                print("2. Frontend is sending truncated data")
                print("3. There's a validator limiting the length")
                print("\nRun test_api_update.py to test the full API flow")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_postgres_column()
