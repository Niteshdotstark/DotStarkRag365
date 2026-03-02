"""
Check if access tokens are being truncated in the database
"""
from database import SessionLocal, engine
from models import Tenant
from sqlalchemy import text

def check_access_tokens():
    """Check all tenants' access tokens"""
    
    print("=" * 70)
    print("ACCESS TOKEN CHECK")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Check column definition
        print("\nStep 1: Checking column definitions...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'tenants' 
                AND column_name IN ('fb_access_token', 'insta_access_token')
                ORDER BY column_name
            """))
            
            print(f"\n{'Column Name':<25} {'Type':<15} {'Max Length':<12}")
            print("-" * 55)
            
            for row in result:
                col_name = row[0]
                data_type = row[1]
                max_length = row[2] if row[2] else "unlimited"
                print(f"{col_name:<25} {data_type:<15} {str(max_length):<12}")
                
                if row[2] and row[2] < 200:
                    print(f"  ⚠️  WARNING: {col_name} is too short for access tokens!")
        
        # Check actual data
        print("\n" + "=" * 70)
        print("Step 2: Checking stored tokens")
        print("=" * 70)
        
        tenants = db.query(Tenant).all()
        
        print(f"\n{'ID':<5} {'Name':<20} {'FB Token Len':<15} {'Insta Token Len':<15}")
        print("-" * 70)
        
        for tenant in tenants:
            fb_len = len(tenant.fb_access_token) if tenant.fb_access_token else 0
            insta_len = len(tenant.insta_access_token) if tenant.insta_access_token else 0
            
            print(f"{tenant.id:<5} {tenant.name:<20} {fb_len:<15} {insta_len:<15}")
            
            # Check if tokens look suspicious
            if tenant.id == 7:
                print(f"\n  Tenant 7 Details:")
                if tenant.fb_access_token:
                    print(f"  FB Token: {tenant.fb_access_token[:50]}...")
                    print(f"  FB Token Length: {fb_len}")
                    if fb_len < 100:
                        print(f"  ❌ FB token is too short! Facebook tokens are usually 200+ chars")
                else:
                    print(f"  ❌ FB token is NULL/empty")
                
                if tenant.insta_access_token:
                    print(f"  Insta Token: {tenant.insta_access_token[:50]}...")
                    print(f"  Insta Token Length: {insta_len}")
                    if insta_len < 100:
                        print(f"  ❌ Insta token is too short!")
                else:
                    print(f"  ⚠️  Insta token is NULL/empty")
        
        print("\n" + "=" * 70)
        print("DIAGNOSIS")
        print("=" * 70)
        
        print("\nFacebook access tokens are typically 200-300 characters long.")
        print("If your tokens are shorter, they're being truncated by the database.")
        print("\nTo fix:")
        print("1. Run: python diagnose_and_fix.py")
        print("2. Or manually alter the columns to VARCHAR(500)")
        print("3. Then update the tokens in your admin UI")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_access_tokens()
