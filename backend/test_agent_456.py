"""
Test script for agent_id 456 - planethomelending.com crawl
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"
AGENT_ID = 456
WEBSITE_URL = "https://planethomelending.com/"
MAX_PAGES = 1

def test_crawl():
    """Test crawling planethomelending.com with agent_id 456"""
    
    print("=" * 70)
    print("🚀 AGENT 456 - PLANETHOMELENDING.COM CRAWL TEST")
    print("=" * 70)
    print(f"Agent ID: {AGENT_ID}")
    print(f"Website: {WEBSITE_URL}")
    print(f"Max Pages: {MAX_PAGES}")
    print()
    
    # Step 1: Initiate crawl
    print("STEP 1: INITIATE CRAWL")
    print("-" * 70)
    
    crawl_payload = {
        "url": WEBSITE_URL,
        "max_pages": MAX_PAGES,
        "crawl_scope": "HOST_ONLY"
    }
    
    print(f"📤 POST {BASE_URL}/tenants/{AGENT_ID}/websites/crawl")
    print(f"📋 Payload: {json.dumps(crawl_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/tenants/{AGENT_ID}/websites/crawl",
            json=crawl_payload,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code in [200, 202]:
            result = response.json()
            print("✅ Crawl initiated successfully!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            website_id = result.get('website_id')
            if not website_id:
                print("❌ No website_id in response")
                return
            
            print()
            print("STEP 2: MONITOR CRAWL STATUS")
            print("-" * 70)
            
            # Poll status
            max_wait = 600  # 10 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(
                    f"{BASE_URL}/tenants/{AGENT_ID}/websites/{website_id}/status"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    crawl_status = status_data.get('status')
                    pages_crawled = status_data.get('pages_crawled', 0)
                    
                    print(f"⏳ Status: {crawl_status} | Pages: {pages_crawled}")
                    
                    if crawl_status == 'completed':
                        print()
                        print("✅ CRAWL COMPLETED!")
                        print(f"📊 Total pages crawled: {pages_crawled}")
                        print()
                        
                        # Test chat
                        print("STEP 3: TEST CHAT")
                        print("-" * 70)
                        
                        test_question = "What is Planet Home Lending?"
                        print(f"❓ Question: {test_question}")
                        
                        chat_response = requests.post(
                            f"{BASE_URL}/tenants/{AGENT_ID}/websites/{website_id}/chat",
                            json={"question": test_question}
                        )
                        
                        if chat_response.status_code == 200:
                            chat_data = chat_response.json()
                            print(f"💬 Answer: {chat_data.get('answer')}")
                            print()
                            print("=" * 70)
                            print("✅ TEST PASSED - Agent 456 working correctly!")
                            print("=" * 70)
                        else:
                            print(f"❌ Chat failed: {chat_response.status_code}")
                            print(chat_response.text)
                        
                        return
                    
                    elif crawl_status == 'failed':
                        print()
                        print(f"❌ CRAWL FAILED")
                        print(f"Error: {status_data.get('error_message')}")
                        return
                    
                    time.sleep(10)
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    print(status_response.text)
                    return
            
            print()
            print(f"⏰ Timeout after {max_wait} seconds")
            
        else:
            print(f"❌ Crawl failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print()
    print("⚠️  PREREQUISITES:")
    print("1. FastAPI server must be running: uvicorn main:app --reload")
    print("2. Virtual environment must be activated")
    print()
    input("Press Enter to start the test or Ctrl+C to cancel...")
    print()
    
    test_crawl()
