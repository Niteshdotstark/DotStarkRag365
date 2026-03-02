"""
Manual test script for website crawling feature.

This script tests the complete flow:
1. Start the FastAPI server
2. Initiate a website crawl
3. Check crawl status
4. Query the website once crawling is complete

Run this after starting the FastAPI server with: uvicorn main:app --reload
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
TENANT_ID = 1  # Use an existing tenant ID from your database
TEST_WEBSITE_URL = "https://docs.python.org/3/tutorial/"  # Small website for testing
MAX_PAGES = 10  # Small number for quick testing

def test_crawl_initiation():
    """Test POST /tenants/{tenant_id}/websites/crawl"""
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
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 202:
        print("\n✅ Crawl initiated successfully!")
        return response.json()
    else:
        print("\n❌ Failed to initiate crawl")
        return None


def test_crawl_status(website_id):
    """Test GET /tenants/{tenant_id}/websites/crawl/{website_id}/status"""
    print("\n" + "="*60)
    print("TEST 2: Check Crawl Status")
    print("="*60)
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl/{website_id}/status"
    
    print(f"GET {url}")
    
    response = requests.get(url)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"\n📊 Status: {status_data['status']}")
        print(f"📄 Pages Crawled: {status_data['pages_crawled']}/{status_data['max_pages']}")
        return status_data
    else:
        print("\n❌ Failed to get status")
        return None


def test_website_chat(website_url, question):
    """Test POST /tenants/{tenant_id}/websites/chat"""
    print("\n" + "="*60)
    print("TEST 3: Chat with Website")
    print("="*60)
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/chat"
    payload = {
        "website_url": website_url,
        "question": question
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        chat_data = response.json()
        print(f"\n💬 Answer: {chat_data['answer'][:200]}...")
        print(f"\n📚 Sources ({len(chat_data['source_citations'])}):")
        for i, citation in enumerate(chat_data['source_citations'][:3], 1):
            print(f"   {i}. {citation['url']}")
        print(f"\n✅ Chat successful!")
        return chat_data
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("\n❌ Chat failed")
        return None


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("WEBSITE CRAWLING FEATURE - MANUAL TEST")
    print("="*60)
    print(f"\nTenant ID: {TENANT_ID}")
    print(f"Test Website: {TEST_WEBSITE_URL}")
    print(f"Max Pages: {MAX_PAGES}")
    
    # Test 1: Initiate crawl
    crawl_result = test_crawl_initiation()
    if not crawl_result:
        print("\n❌ Test failed at crawl initiation")
        return
    
    website_id = crawl_result['website_id']
    
    # Test 2: Poll status until complete
    print("\n⏳ Waiting for crawl to complete...")
    print("   (This may take a few minutes depending on the website size)")
    
    max_wait_time = 600  # 10 minutes
    poll_interval = 10  # 10 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        time.sleep(poll_interval)
        elapsed_time += poll_interval
        
        status_data = test_crawl_status(website_id)
        if not status_data:
            print("\n❌ Test failed at status check")
            return
        
        status = status_data['status']
        
        if status == "COMPLETE":
            print("\n✅ Crawling completed!")
            break
        elif status == "FAILED":
            print(f"\n❌ Crawling failed: {status_data.get('error_message')}")
            return
        else:
            print(f"   Status: {status} - {status_data['pages_crawled']}/{status_data['max_pages']} pages")
    else:
        print(f"\n⚠️  Crawl did not complete within {max_wait_time} seconds")
        print("   You can check status later and run the chat test manually")
        return
    
    # Test 3: Chat with website
    test_question = "What is Python?"
    chat_result = test_website_chat(TEST_WEBSITE_URL, test_question)
    
    if chat_result:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe website crawling feature is working correctly!")
        print(f"\nYou can now:")
        print(f"1. Crawl more websites using POST /tenants/{TENANT_ID}/websites/crawl")
        print(f"2. Check status using GET /tenants/{TENANT_ID}/websites/crawl/{{website_id}}/status")
        print(f"3. Ask questions using POST /tenants/{TENANT_ID}/websites/chat")
    else:
        print("\n❌ Test failed at chat")


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("1. FastAPI server must be running: uvicorn main:app --reload")
    print("2. Database must be set up with at least one tenant")
    print("3. AWS credentials must be configured in env file")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    main()
