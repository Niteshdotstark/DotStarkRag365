"""
Test chat functionality with the crawled DotStark website.
Asks 5 specific questions about DotStark.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
TENANT_ID = 1
WEBSITE_URL = "https://dotstark.com"

# The 5 questions to ask
QUESTIONS = [
    "Who are you?",
    "What is dotstark?",
    "Which Dotstark services it is providing?",
    "Dotstark Offices",
    "How can I reach to dotstark?"
]

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_crawl_status(website_id):
    """Check if the crawl is complete before asking questions."""
    print_section("CHECKING CRAWL STATUS")
    
    url = f"{BASE_URL}/tenants/{TENANT_ID}/websites/crawl/{website_id}/status"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            pages_crawled = data.get('pages_crawled', 0)
            
            print(f"📊 Crawl Status: {status}")
            print(f"📄 Pages Crawled: {pages_crawled}")
            
            if status == "COMPLETE":
                print(f"✅ Crawl is complete! Ready to ask questions.\n")
                return True
            elif status in ["STARTING", "IN_PROGRESS"]:
                print(f"⏳ Crawl is still in progress. Please wait...\n")
                return False
            elif status == "FAILED":
                print(f"❌ Crawl failed: {data.get('error_message', 'Unknown error')}\n")
                return False
            else:
                print(f"⚠️  Unknown status: {status}\n")
                return False
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            print(f"Response: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"❌ Error checking status: {e}\n")
        return False

def ask_question(question_num, question):
    """Ask a question to the chat endpoint."""
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
            answer = data.get('answer', 'No answer provided')
            citations = data.get('source_citations', [])
            
            print(f"\n✅ Answer received!")
            print(f"\n💬 ANSWER:")
            print(f"{answer}")
            
            if citations:
                print(f"\n📚 SOURCES ({len(citations)}):")
                for i, citation in enumerate(citations[:3], 1):
                    url_cite = citation.get('url', 'N/A')
                    title = citation.get('title', 'No title')
                    print(f"   {i}. {title}")
                    print(f"      URL: {url_cite}")
            
            return {'success': True, 'answer': answer, 'citations': citations}
            
        else:
            print(f"\n❌ Failed to get answer")
            print(f"Response: {response.text}")
            return {'success': False}
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return {'success': False}

def main():
    """Main test function."""
    print_section("🤖 DOTSTARK CHAT TEST - 5 QUESTIONS")
    
    print(f"📋 Configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Tenant ID: {TENANT_ID}")
    print(f"   Website: {WEBSITE_URL}")
    print(f"   Questions: {len(QUESTIONS)}")
    
    # First, we need to get the website_id from the most recent crawl
    # For now, let's try to ask questions directly
    # The chat endpoint should find the website by URL
    
    print_section("ASKING QUESTIONS")
    
    results = {
        'total_questions': len(QUESTIONS),
        'successful_answers': 0,
        'failed_answers': 0
    }
    
    for i, question in enumerate(QUESTIONS, 1):
        result = ask_question(i, question)
        
        if result['success']:
            results['successful_answers'] += 1
        else:
            results['failed_answers'] += 1
        
        # Small delay between questions
        if i < len(QUESTIONS):
            time.sleep(2)
    
    # Final summary
    print_section("📊 TEST SUMMARY")
    
    print(f"Total Questions: {results['total_questions']}")
    print(f"✅ Successful Answers: {results['successful_answers']}")
    print(f"❌ Failed Answers: {results['failed_answers']}")
    
    if results['successful_answers'] == results['total_questions']:
        print(f"\n🎉 ALL QUESTIONS ANSWERED SUCCESSFULLY!")
        print(f"\n✨ The website chat feature is working perfectly!")
    else:
        print(f"\n⚠️  SOME QUESTIONS FAILED")
        print(f"Please check the errors above for details.")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("   1. FastAPI server must be running: uvicorn main:app --reload")
    print("   2. Website crawl must be COMPLETE")
    print("   3. Tenant ID 1 must exist in database")
    print("\n   Press Enter to start asking questions or Ctrl+C to cancel...")
    
    try:
        input()
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
