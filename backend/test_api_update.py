"""
Test script to simulate the API update request
This helps debug what data is being sent vs what's being stored
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
TENANT_ID = 7
TEST_TOKEN = "chatbottoken@3420"

def test_update_tenant():
    """Test updating tenant through the API"""
    
    print("=" * 60)
    print("Testing Tenant Update via API")
    print("=" * 60)
    
    # First, you need to login to get a token
    print("\nStep 1: Login (you need to provide credentials)")
    print("Please login manually and provide the access token")
    access_token = input("Enter your access token: ").strip()
    
    if not access_token:
        print("❌ No access token provided. Exiting.")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get current tenant data
    print(f"\nStep 2: Getting current data for tenant {TENANT_ID}")
    try:
        response = requests.get(f"{BASE_URL}/tenants/", headers=headers)
        response.raise_for_status()
        tenants = response.json()
        
        tenant_7 = None
        for t in tenants:
            if t['id'] == TENANT_ID:
                tenant_7 = t
                break
        
        if tenant_7:
            print(f"Current fb_verify_token: '{tenant_7.get('fb_verify_token')}'")
            print(f"Token length: {len(tenant_7.get('fb_verify_token', ''))}")
        else:
            print(f"❌ Tenant {TENANT_ID} not found")
            return
            
    except Exception as e:
        print(f"❌ Error getting tenant: {e}")
        return
    
    # Step 3: Update the tenant
    print(f"\nStep 3: Updating tenant with new token")
    print(f"New token: '{TEST_TOKEN}'")
    print(f"Token length: {len(TEST_TOKEN)}")
    
    update_data = {
        "fb_verify_token": TEST_TOKEN
    }
    
    print(f"\nSending PUT request to: {BASE_URL}/tenants/{TENANT_ID}/")
    print(f"Request body: {json.dumps(update_data, indent=2)}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/tenants/{TENANT_ID}/",
            headers=headers,
            json=update_data
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body: {json.dumps(result, indent=2)}")
        
        returned_token = result.get('fb_verify_token')
        print(f"\nReturned fb_verify_token: '{returned_token}'")
        print(f"Returned token length: {len(returned_token) if returned_token else 0}")
        
        if returned_token == TEST_TOKEN:
            print("✅ Token matches! Update successful.")
        else:
            print("❌ Token doesn't match!")
            print(f"Expected: '{TEST_TOKEN}'")
            print(f"Got: '{returned_token}'")
            print("\nThis indicates the database is truncating the value.")
            
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error updating tenant: {e}")
    
    # Step 4: Verify by reading again
    print(f"\nStep 4: Verifying by reading tenant data again")
    try:
        response = requests.get(f"{BASE_URL}/tenants/", headers=headers)
        response.raise_for_status()
        tenants = response.json()
        
        tenant_7 = None
        for t in tenants:
            if t['id'] == TENANT_ID:
                tenant_7 = t
                break
        
        if tenant_7:
            stored_token = tenant_7.get('fb_verify_token')
            print(f"Stored fb_verify_token: '{stored_token}'")
            print(f"Stored token length: {len(stored_token) if stored_token else 0}")
            
            if stored_token == TEST_TOKEN:
                print("✅ Verification successful! Token stored correctly.")
            else:
                print("❌ Verification failed! Token was truncated.")
                print(f"Expected: '{TEST_TOKEN}'")
                print(f"Got: '{stored_token}'")
                
    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    print("This script will test updating tenant 7's fb_verify_token")
    print(f"Target URL: {BASE_URL}")
    print(f"Tenant ID: {TENANT_ID}")
    print(f"Test Token: {TEST_TOKEN}")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() == 'yes':
        test_update_tenant()
    else:
        print("Operation cancelled.")
