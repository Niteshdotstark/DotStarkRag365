"""
Check crawl status on the server via API
"""
import requests
import json
import sys

# Update this with your server URL
SERVER_URL = "http://your-server-url"  # e.g., "http://3.110.123.45:8000"

def check_agent_crawls(agent_id: int, token: str = None):
    """Check crawls for a specific agent via API"""
    
    url = f"{SERVER_URL}/api/agents/{agent_id}/crawls"
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n{'='*70}")
        print(f"  CRAWLS FOR AGENT {agent_id}")
        print(f"{'='*70}\n")
        
        print(f"Total Crawls: {data.get('total_crawls', 0)}\n")
        
        for crawl in data.get('crawls', []):
            print(f"📊 Crawl:")
            print(f"   URL: {crawl.get('website_url')}")
            print(f"   Status: {crawl.get('status')}")
            print(f"   Knowledge Base ID: {crawl.get('knowledge_base_id')}")
            print(f"   Pages Crawled: {crawl.get('pages_crawled')}/{crawl.get('max_pages')}")
            print(f"   Created: {crawl.get('created_at')}")
            if crawl.get('error_message'):
                print(f"   ❌ Error: {crawl.get('error_message')}")
            print(f"\n{'-'*70}\n")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to server: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_server_crawl.py <agent_id> [server_url] [token]")
        sys.exit(1)
    
    agent_id = int(sys.argv[1])
    
    if len(sys.argv) > 2:
        SERVER_URL = sys.argv[2]
    
    token = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Checking server: {SERVER_URL}")
    check_agent_crawls(agent_id, token)
