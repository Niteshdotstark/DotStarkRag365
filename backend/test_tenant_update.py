"""
Test script to debug tenant update issue with fb_verify_token
Run this on your server to see what's happening
"""
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Tenant, Base
import json

def test_tenant_token():
    """Test reading and writing fb_verify_token for tenant 7"""
    db = SessionLocal()
    
    try:
        # 1. Check current value in database
        print("=" * 60)
        print("STEP 1: Reading current tenant 7 data from database")
        print("=" * 60)
        tenant = db.query(Tenant).filter(Tenant.id == 7).first()
        
        if not tenant:
            print("❌ Tenant 7 not found!")
            return
        
        print(f"Tenant ID: {tenant.id}")
        print(f"Tenant Name: {tenant.name}")
        print(f"fb_verify_token value: '{tenant.fb_verify_token}'")
        print(f"fb_verify_token length: {len(tenant.fb_verify_token) if tenant.fb_verify_token else 0}")
        print(f"fb_verify_token repr: {repr(tenant.fb_verify_token)}")
        
        # 2. Check column definition
        print("\n" + "=" * 60)
        print("STEP 2: Checking column definition in database")
        print("=" * 60)
        
        # Get column info from database
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns('tenants')
        
        for col in columns:
            if col['name'] == 'fb_verify_token':
                print(f"Column name: {col['name']}")
                print(f"Column type: {col['type']}")
                print(f"Column nullable: {col['nullable']}")
                print(f"Column default: {col.get('default', 'None')}")
        
        # 3. Test update with new value
        print("\n" + "=" * 60)
        print("STEP 3: Testing update with test token")
        print("=" * 60)
        
        test_token = "chatbottoken@3420"
        print(f"Attempting to set token to: '{test_token}'")
        print(f"Token length: {len(test_token)}")
        
        tenant.fb_verify_token = test_token
        db.commit()
        db.refresh(tenant)
        
        print(f"\nAfter update:")
        print(f"fb_verify_token value: '{tenant.fb_verify_token}'")
        print(f"fb_verify_token length: {len(tenant.fb_verify_token) if tenant.fb_verify_token else 0}")
        print(f"fb_verify_token repr: {repr(tenant.fb_verify_token)}")
        
        # 4. Check if value was truncated
        if tenant.fb_verify_token != test_token:
            print(f"\n❌ VALUE WAS TRUNCATED!")
            print(f"Expected: '{test_token}'")
            print(f"Got: '{tenant.fb_verify_token}'")
            print(f"\nThis indicates the database column is too short.")
            print(f"You need to alter the column to allow longer strings.")
        else:
            print(f"\n✅ Value stored correctly!")
        
        # 5. Show all tenants and their tokens
        print("\n" + "=" * 60)
        print("STEP 4: All tenants and their verify tokens")
        print("=" * 60)
        
        all_tenants = db.query(Tenant).all()
        for t in all_tenants:
            token_display = repr(t.fb_verify_token) if t.fb_verify_token else "None"
            print(f"Tenant {t.id} ({t.name}): {token_display}")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing Tenant fb_verify_token Issue")
    print("=" * 60)
    test_tenant_token()
