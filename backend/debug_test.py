"""
Debug script to capture detailed error information
"""
import requests
import json
import traceback
import sys

BASE_URL = "http://localhost:8000"
TENANT_ID = 1
WEBSITE_URL = "https://dotstark.com"
MAX_PAGES = 2

def test_server_connection():
    """Test if server is running"""
    print("\n" + "="*70)
    print("CHECKING SERVER CONNECTION")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("   Make sure FastAPI is running: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_crawl_initiation():
    """Test crawl initiation with detailed error capture"""
    print("\n" + "="*70)
    print("TESTING CRAWL INITIATION")
    print("="*70)
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl"
    payload = {
        "url": WEBSITE_URL,
        "max_pages": MAX_PAGES,
        "crawl_scope": "HOST"
    }
    
    print(f"\n📤 Request:")
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print(f"   Payload: {json.dumps(payload, indent=6)}")
    
    try:
        print("\n⏳ Sending request...")
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"\n   Body:")
            print(json.dumps(response_data, indent=6, default=str))
        except:
            print(f"\n   Body (raw): {response.text}")
        
        if response.status_code == 202:
            print("\n✅ SUCCESS: Crawl initiated")
            return {'success': True, 'data': response_data}
        else:
            print(f"\n❌ FAILED: Status code {response.status_code}")
            return {'success': False, 'status_code': response.status_code, 'response': response.text}
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: Request took longer than 120 seconds")
        print("   This might mean:")
        print("   1. Server is processing but slow")
        print("   2. AWS operations are taking too long")
        print("   3. Network issues")
        return {'success': False, 'error': 'timeout'}
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("   Server might not be running")
        return {'success': False, 'error': 'connection_error'}
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print(f"\n   Full traceback:")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def test_status_check(website_id):
    """Test status check with detailed error capture"""
    print("\n" + "="*70)
    print("TESTING STATUS CHECK")
    print("="*70)
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl/{website_id}/status"
    
    print(f"\n📤 Request:")
    print(f"   URL: {url}")
    print(f"   Method: GET")
    
    try:
        print("\n⏳ Sending request...")
        response = requests.get(url, timeout=30)
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"\n   Body:")
            print(json.dumps(response_data, indent=6, default=str))
        except:
            print(f"\n   Body (raw): {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Status retrieved")
            return {'success': True, 'data': response_data}
        else:
            print(f"\n❌ FAILED: Status code {response.status_code}")
            return {'success': False, 'status_code': response.status_code}
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def test_chat(question):
    """Test chat with detailed error capture"""
    print("\n" + "="*70)
    print("TESTING CHAT")
    print("="*70)
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/chat"
    payload = {
        "website_url": WEBSITE_URL,
        "question": question
    }
    
    print(f"\n📤 Request:")
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print(f"   Payload: {json.dumps(payload, indent=6)}")
    
    try:
        print("\n⏳ Sending request...")
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"\n   Body:")
            print(json.dumps(response_data, indent=6, default=str))
        except:
            print(f"\n   Body (raw): {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Answer received")
            return {'success': True, 'data': response_data}
        else:
            print(f"\n❌ FAILED: Status code {response.status_code}")
            return {'success': False, 'status_code': response.status_code}
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def main():
    """Run debug tests"""
    print("\n" + "="*70)
    print("DEBUG TEST FOR DOTSTARK.COM CRAWLING")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Tenant ID: {TENANT_ID}")
    print(f"   Website: {WEBSITE_URL}")
    print(f"   Max Pages: {MAX_PAGES}")
    
    # Step 1: Check server
    if not test_server_connection():
        print("\n❌ Cannot proceed - server is not accessible")
        sys.exit(1)
    
    # Step 2: Test crawl initiation
    crawl_result = test_crawl_initiation()
    
    if not crawl_result['success']:
        print("\n" + "="*70)
        print("❌ TEST FAILED AT CRAWL INITIATION")
        print("="*70)
        print("\nError details saved above. Please share this output.")
        sys.exit(1)
    
    website_id = crawl_result['data']['website_id']
    print(f"\n📝 Website ID: {website_id}")
    
    # Step 3: Test status check
    status_result = test_status_check(website_id)
    
    if not status_result['success']:
        print("\n" + "="*70)
        print("❌ TEST FAILED AT STATUS CHECK")
        print("="*70)
        sys.exit(1)
    
    # Step 4: If complete, test chat
    if status_result['data']['status'] == 'COMPLETE':
        chat_result = test_chat("What is DotStark?")
        
        if not chat_result['success']:
            print("\n" + "="*70)
            print("❌ TEST FAILED AT CHAT")
            print("="*70)
            sys.exit(1)
    else:
        print(f"\n⏳ Crawl status is {status_result['data']['status']}")
        print("   Wait for it to complete before testing chat")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(1)
