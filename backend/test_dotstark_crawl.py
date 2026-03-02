"""
Quick test for website crawling with example.com
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
TENANT_ID = 2
TEST_WEBSITE_URL = "https://example.com"
MAX_PAGES = 5

print("\n" + "="*60)
print("TESTING WEBSITE CRAWLING FEATURE")
print("="*60)
print(f"Tenant ID: {TENANT_ID}")
print(f"Website: {TEST_WEBSITE_URL}")
print(f"Max Pages: {MAX_PAGES}")

# Test 1: Initiate crawl
print("\n" + "="*60)
print("TEST 1: Initiate Website Crawl")
print("="*60)

url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl"
payload = {
    "url": TEST_WEBSITE_URL,
    "max_pages": MAX_PAGES,
    "crawl_scope": "HOST"
}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=120)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 202:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, default=str)}")
        print("\n✅ Crawl initiated successfully!")
        
        website_id = result['website_id']
        knowledge_base_id = result['knowledge_base_id']
        
        print(f"\nWebsite ID: {website_id}")
        print(f"Knowledge Base ID: {knowledge_base_id}")
        print(f"Status: {result['status']}")
        
        # Test 2: Check status
        print("\n" + "="*60)
        print("TEST 2: Check Crawl Status (waiting 30 seconds)")
        print("="*60)
        
        time.sleep(30)
        
        status_url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl/{website_id}/status"
        print(f"GET {status_url}")
        
        status_response = requests.get(status_url, timeout=30)
        print(f"\nStatus Code: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Response: {json.dumps(status_data, indent=2, default=str)}")
            print(f"\n📊 Status: {status_data['status']}")
            print(f"📄 Pages Crawled: {status_data['pages_crawled']}/{status_data['max_pages']}")
            
            if status_data['status'] == 'COMPLETE':
                print("\n✅ Crawling completed! Ready for chat.")
            elif status_data['status'] in ['STARTING', 'IN_PROGRESS']:
                print("\n⏳ Crawling still in progress. Check status again later.")
            elif status_data['status'] == 'FAILED':
                print(f"\n❌ Crawling failed: {status_data.get('error_message')}")
        else:
            print(f"❌ Failed to get status: {status_response.text}")
            
    else:
        print(f"Response: {response.text}")
        print("\n❌ Failed to initiate crawl")
        
except requests.exceptions.Timeout:
    print("\n⏳ Request timed out - this is normal for large crawls")
    print("The crawl is running in the background. Check status later.")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nNext steps:")
print(f"1. Check status: GET /tenants/{TENANT_ID}/websites/crawl/{{website_id}}/status")
print(f"2. Once COMPLETE, ask questions: POST /tenants/{TENANT_ID}/websites/chat")
