"""
Test crawling with the new collection
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
AGENT_ID = 999  # Test agent

def test_crawl():
    """Test website crawl"""
    
    print(f"\n{'='*70}")
    print(f"  TESTING WEBSITE CRAWL")
    print(f"{'='*70}\n")
    
    # Step 1: Initiate crawl
    print("1️⃣  Initiating crawl...")
    crawl_data = {
        "url": "https://example.com",
        "max_pages": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tenants/{AGENT_ID}/websites/crawl",
            json=crawl_data,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Crawl initiated!")
            print(f"   Message: {result.get('message')}")
            print(f"   Website ID: {result.get('website_id')}\n")
        else:
            print(f"   ❌ Error: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    # Step 2: Check status
    print("2️⃣  Checking crawl status...")
    print("   (Waiting 10 seconds for background task to start...)")
    time.sleep(10)
    
    try:
        response = requests.get(
            f"{BASE_URL}/tenants/{AGENT_ID}/websites/status",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status retrieved!")
            print(f"   Agent ID: {result.get('agent_id')}")
            print(f"   Total Crawls: {result.get('total_crawls')}\n")
            
            if result.get('crawls'):
                for crawl in result['crawls']:
                    print(f"   📊 Crawl:")
                    print(f"      URL: {crawl.get('website_url')}")
                    print(f"      Status: {crawl.get('status')}")
                    print(f"      KB ID: {crawl.get('knowledge_base_id')}")
                    if crawl.get('error_message'):
                        print(f"      ❌ Error: {crawl.get('error_message')}")
                    print()
            
            return True
        else:
            print(f"   ❌ Error: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    success = test_crawl()
    
    if success:
        print("✅ Test completed! Check the status above for results.")
        print("\n💡 The crawl runs in background. It may take a few minutes.")
        print("   Check status again in 2-3 minutes to see progress.")
    else:
        print("❌ Test failed!")
