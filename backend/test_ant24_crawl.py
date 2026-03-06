"""
Test website crawling with a fresh agent ID for https://ant24.ai/
"""
import requests
import time

BASE_URL = "http://localhost:8000"
AGENT_ID = 3213  # Fresh agent ID
WEBSITE_URL = "https://ant24.ai/"

print("\n" + "="*70)
print("TESTING ANT24.AI WEBSITE CRAWL")
print("="*70 + "\n")

# Step 1: Initiate crawl
print("1️⃣  Initiating crawl...")
crawl_response = requests.post(
    f"{BASE_URL}/tenants/{AGENT_ID}/websites/crawl",
    json={"url": WEBSITE_URL}
)

print(f"Status Code: {crawl_response.status_code}")

if crawl_response.status_code == 200:
    print("✅ Crawl initiated!")
    data = crawl_response.json()
    print(f"Message: {data.get('message')}")
    print(f"Website ID: {data.get('website_id')}")
else:
    print(f"❌ Error: {crawl_response.text}")
    exit(1)

# Step 2: Check status
print("\n2️⃣  Checking crawl status...")
print("(Waiting 10 seconds for background task to start...)")
time.sleep(10)

status_response = requests.get(f"{BASE_URL}/tenants/{AGENT_ID}/websites/status")

if status_response.status_code == 200:
    print("✅ Status retrieved!")
    status_data = status_response.json()
    
    print(f"Agent ID: {status_data.get('agent_id')}")
    print(f"Total Crawls: {len(status_data.get('websites', []))}")
    
    for website in status_data.get('websites', []):
        print(f"\n📊 Crawl:")
        print(f"   URL: {website.get('url')}")
        print(f"   Status: {website.get('status')}")
        print(f"   KB ID: {website.get('knowledge_base_id')}")
        
        if website.get('error_message'):
            print(f"   ❌ Error: {website.get('error_message')}")
        
        if website.get('status') == 'ACTIVE':
            print(f"   ✅ Crawl is ACTIVE and ready!")
            print(f"   📝 You can now query this knowledge base")
else:
    print(f"❌ Error: {status_response.text}")

print("\n✅ Test completed! Check the status above for results.")
print("💡 The crawl runs in background. It may take a few minutes.")
print("   Check status again in 2-3 minutes to see progress.\n")
