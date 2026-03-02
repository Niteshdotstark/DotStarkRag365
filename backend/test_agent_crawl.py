"""
Test website crawling with agent_id 21.
"""
import requests
import json

BASE_URL = "http://localhost:8000"
AGENT_ID = 21  # Using agent_id 21 as requested
WEBSITE_URL = "https://example.com"
MAX_PAGES = 5

def test_crawl():
    """Test initiating a crawl with agent_id 21."""
    
    print(f"\n{'='*70}")
    print(f"  TESTING AGENT-BASED CRAWLING")
    print(f"{'='*70}\n")
    
    print(f"📋 Configuration:")
    print(f"   Agent ID: {AGENT_ID}")
    print(f"   Website: {WEBSITE_URL}")
    print(f"   Max Pages: {MAX_PAGES}\n")
    
    url = f"{BASE_URL}/tenants/{AGENT_ID}/websites/crawl"
    payload = {
        "url": WEBSITE_URL,
        "max_pages": MAX_PAGES,
        "crawl_scope": "HOST_ONLY"
    }
    
    print(f"📤 POST {url}")
    print(f"📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 202:
            data = response.json()
            print(f"\n✅ Crawl initiated successfully!")
            print(f"\n📊 Response Data:")
            print(json.dumps(data, indent=2, default=str))
            
            print(f"\n{'='*70}")
            print(f"🎉 SUCCESS! Agent {AGENT_ID} can now crawl websites!")
            print(f"{'='*70}\n")
            print(f"💡 Key Points:")
            print(f"   - Agent {AGENT_ID} was auto-created")
            print(f"   - No tenant validation required")
            print(f"   - Each agent has independent crawls")
            print(f"   - URL format: /tenants/{{agent_id}}/websites/crawl")
            print(f"\n{'='*70}\n")
            
            return True
        else:
            print(f"\n❌ Failed to initiate crawl")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("   1. FastAPI server must be running: uvicorn main:app --reload")
    print("   2. Migration completed: python migrate_to_agent_system.py")
    print("\n   Press Enter to start the test or Ctrl+C to cancel...")
    
    try:
        input()
        test_crawl()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
