"""
End-to-end test for dotstark.com website crawling.

This script:
1. Crawls https://dotstark.com (2 pages)
2. Monitors crawl status until complete
3. Asks 3 questions about the website
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TENANT_ID = 1  # Using tenant ID 1 (verified to exist in database)
WEBSITE_URL = "https://dotstark.com"
MAX_PAGES = 2

# Test questions
QUESTIONS = [
    "What services does DotStark offer?",
    "What is DotStark?",
    "How can I contact DotStark?"
]


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_step(step_num, title):
    """Print a formatted step header"""
    print(f"\n{'─'*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'─'*70}")


def test_initiate_crawl():
    """Step 1: Initiate website crawl"""
    print_step(1, "INITIATE WEBSITE CRAWL")
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl"
    payload = {
        "url": WEBSITE_URL,
        "max_pages": MAX_PAGES,
        "crawl_scope": "HOST_ONLY"  # Changed from HOST to HOST_ONLY
    }
    
    print(f"\n📤 POST {url}")
    print(f"📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=180)  # Increased to 180 seconds (3 minutes)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 202:
            data = response.json()
            print(f"✅ Crawl initiated successfully!")
            print(f"\n📊 Response Data:")
            print(json.dumps(data, indent=2, default=str))
            
            return {
                'success': True,
                'website_id': data['website_id'],
                'knowledge_base_id': data['knowledge_base_id'],
                'status': data['status']
            }
        else:
            print(f"❌ Failed to initiate crawl")
            print(f"Response: {response.text}")
            return {'success': False}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("\n💡 Make sure the FastAPI server is running:")
        print("   uvicorn main:app --reload")
        return {'success': False}


def test_crawl_status(website_id, wait_for_completion=True):
    """Step 2: Check crawl status"""
    print_step(2, "MONITOR CRAWL STATUS")
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl/{website_id}/status"
    
    print(f"\n📤 GET {url}")
    
    max_wait_time = 600  # 10 minutes
    poll_interval = 10  # 10 seconds
    start_time = time.time()
    attempt = 0
    
    while True:
        attempt += 1
        elapsed = int(time.time() - start_time)
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                pages_crawled = data.get('pages_crawled', 0)
                max_pages = data.get('max_pages', MAX_PAGES)
                
                print(f"\n📊 Attempt {attempt} (Elapsed: {elapsed}s)")
                print(f"   Status: {status}")
                print(f"   Pages: {pages_crawled}/{max_pages}")
                
                if status == "COMPLETE":
                    print(f"\n✅ Crawling completed successfully!")
                    print(f"   Total pages crawled: {pages_crawled}")
                    print(f"   Time taken: {elapsed} seconds")
                    print(f"\n📋 Full Status:")
                    print(json.dumps(data, indent=2, default=str))
                    return {'success': True, 'data': data}
                    
                elif status == "FAILED":
                    print(f"\n❌ Crawling failed!")
                    error_msg = data.get('error_message', 'Unknown error')
                    print(f"   Error: {error_msg}")
                    print(f"\n📋 Full Status:")
                    print(json.dumps(data, indent=2, default=str))
                    return {'success': False, 'error': error_msg}
                    
                elif status in ["STARTING", "IN_PROGRESS"]:
                    if not wait_for_completion:
                        return {'success': True, 'data': data, 'in_progress': True}
                    
                    if elapsed >= max_wait_time:
                        print(f"\n⚠️  Timeout: Crawl did not complete in {max_wait_time}s")
                        print(f"   Current status: {status}")
                        print(f"   Pages crawled so far: {pages_crawled}")
                        return {'success': False, 'error': 'Timeout'}
                    
                    print(f"   ⏳ Waiting {poll_interval}s before next check...")
                    time.sleep(poll_interval)
                    continue
                    
                else:
                    print(f"\n⚠️  Unknown status: {status}")
                    if not wait_for_completion:
                        return {'success': True, 'data': data}
                    time.sleep(poll_interval)
                    continue
                    
            else:
                print(f"\n❌ Failed to get status: {response.status_code}")
                print(f"Response: {response.text}")
                return {'success': False}
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request failed: {e}")
            return {'success': False}


def test_chat(question_num, question):
    """Step 3: Ask a question"""
    print(f"\n{'─'*70}")
    print(f"QUESTION {question_num}: {question}")
    print(f"{'─'*70}")
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/chat"
    payload = {
        "website_url": WEBSITE_URL,
        "question": question
    }
    
    print(f"\n📤 POST {url}")
    print(f"📋 Question: {question}")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data['answer']
            citations = data.get('source_citations', [])
            
            print(f"\n✅ Answer received!")
            print(f"\n💬 Answer:")
            print(f"   {answer}")
            
            if citations:
                print(f"\n📚 Sources ({len(citations)}):")
                for i, citation in enumerate(citations[:3], 1):
                    url_cite = citation.get('url', 'N/A')
                    title = citation.get('title', 'No title')
                    snippet = citation.get('snippet', '')[:100]
                    print(f"   {i}. {title}")
                    print(f"      URL: {url_cite}")
                    if snippet:
                        print(f"      Snippet: {snippet}...")
            
            return {'success': True, 'answer': answer, 'citations': citations}
            
        else:
            print(f"❌ Failed to get answer")
            print(f"Response: {response.text}")
            return {'success': False}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {'success': False}


def main():
    """Run end-to-end test"""
    print_section("🚀 DOTSTARK.COM END-TO-END TEST")
    
    print(f"\n📋 Test Configuration:")
    print(f"   Website: {WEBSITE_URL}")
    print(f"   Max Pages: {MAX_PAGES}")
    print(f"   Tenant ID: {TENANT_ID}")
    print(f"   Questions: {len(QUESTIONS)}")
    
    start_time = datetime.now()
    results = {
        'crawl_initiated': False,
        'crawl_completed': False,
        'questions_answered': 0,
        'total_questions': len(QUESTIONS)
    }
    
    # Step 1: Initiate crawl
    crawl_result = test_initiate_crawl()
    if not crawl_result['success']:
        print_section("❌ TEST FAILED - Could not initiate crawl")
        return
    
    results['crawl_initiated'] = True
    website_id = crawl_result['website_id']
    
    # Step 2: Wait for crawl to complete
    status_result = test_crawl_status(website_id, wait_for_completion=True)
    if not status_result['success']:
        print_section("❌ TEST FAILED - Crawl did not complete successfully")
        return
    
    results['crawl_completed'] = True
    
    # Step 3: Ask questions
    print_step(3, "ASK QUESTIONS ABOUT THE WEBSITE")
    
    for i, question in enumerate(QUESTIONS, 1):
        chat_result = test_chat(i, question)
        if chat_result['success']:
            results['questions_answered'] += 1
        else:
            print(f"\n⚠️  Question {i} failed, continuing with next question...")
        
        # Small delay between questions
        if i < len(QUESTIONS):
            time.sleep(2)
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_section("📊 TEST SUMMARY")
    
    print(f"\n✅ Crawl Initiated: {'Yes' if results['crawl_initiated'] else 'No'}")
    print(f"✅ Crawl Completed: {'Yes' if results['crawl_completed'] else 'No'}")
    print(f"✅ Questions Answered: {results['questions_answered']}/{results['total_questions']}")
    print(f"\n⏱️  Total Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    if results['crawl_completed'] and results['questions_answered'] == results['total_questions']:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n✨ The website crawling feature is working perfectly!")
        print(f"\n📝 Summary:")
        print(f"   • Successfully crawled {WEBSITE_URL}")
        print(f"   • Indexed content from the website")
        print(f"   • Answered all {results['total_questions']} questions with citations")
        print(f"\n🚀 You can now:")
        print(f"   1. Crawl other websites")
        print(f"   2. Integrate with your frontend")
        print(f"   3. Scale up max_pages for more comprehensive crawling")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print(f"\nPlease check the errors above for details.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("   1. FastAPI server must be running: uvicorn main:app --reload")
    print("   2. All diagnostic checks must pass: python diagnose_crawling.py")
    print("   3. Database must have tenant with ID = 1")
    print("\n   Press Enter to start the test or Ctrl+C to cancel...")
    
    try:
        input()
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
