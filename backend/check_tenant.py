"""
Quick script to check existing tenants and create a test tenant if needed.
"""
from database import get_db
from models import Tenant, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def main():
    db = next(get_db())
    
    # Check existing tenants
    tenants = db.query(Tenant).all()
    print(f"\n📊 Found {len(tenants)} tenant(s) in database:")
    
    if tenants:
        for tenant in tenants:
            print(f"\n  Tenant ID: {tenant.id}")
            print(f"  Name: {tenant.name}")
            print(f"  Creator ID: {tenant.creator_id}")
            print(f"  Created: {tenant.created_at}")
    else:
        print("\n⚠️  No tenants found!")
        
        # Check if we have any users
        users = db.query(User).all()
        print(f"\n📊 Found {len(users)} user(s) in database:")
        
        if users:
            for user in users:
                print(f"\n  User ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Username: {user.username}")
        else:
            print("\n⚠️  No users found! Creating test user...")
            
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=pwd_context.hash("testpass123"),
                phone_number="1234567890",
                address="Test Address",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"\n✅ Created test user with ID: {test_user.id}")
            users = [test_user]
        
        # Create a test tenant
        print("\n🔧 Creating test tenant...")
        test_tenant = Tenant(
            name="Test Tenant",
            fb_url=None,
            insta_url=None,
            fb_verify_token=None,
            fb_access_token=None,
            insta_access_token=None,
            telegram_bot_token=None,
            telegram_chat_id=None,
            creator_id=users[0].id
        )
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)
        print(f"\n✅ Created test tenant with ID: {test_tenant.id}")
        print(f"   Name: {test_tenant.name}")
        print(f"   Creator ID: {test_tenant.creator_id}")
    
    db.close()
    
    print("\n" + "="*70)
    print("💡 Use one of the tenant IDs above in your API calls")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
