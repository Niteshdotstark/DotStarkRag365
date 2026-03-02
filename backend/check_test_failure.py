"""
Comprehensive check to identify why the test failed
"""
import os
import sys
import boto3
from sqlalchemy import text
from database import SessionLocal
from models import Tenant, WebsiteCrawl, TenantCollection
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path(".").resolve() / "env"
load_dotenv(dotenv_path=env_path)

def check_database():
    """Check database connectivity and schema"""
    print("\n" + "="*70)
    print("1. CHECKING DATABASE")
    print("="*70)
    
    try:
        db = SessionLocal()
        
        # Test connection
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Check if tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == 1).first()
        if tenant:
            print(f"✅ Tenant 1 exists: {tenant.name}")
        else:
            print("❌ Tenant 1 does not exist")
            print("   Create a tenant first or use a different tenant_id")
            return False
        
        # Check if tables exist
        try:
            db.execute(text("SELECT * FROM website_crawls LIMIT 1"))
            print("✅ website_crawls table exists")
        except Exception as e:
            print(f"❌ website_crawls table missing: {e}")
            print("   Run: alembic upgrade head")
            return False
        
        try:
            db.execute(text("SELECT * FROM tenant_collections LIMIT 1"))
            print("✅ tenant_collections table exists")
        except Exception as e:
            print(f"❌ tenant_collections table missing: {e}")
            print("   Run: alembic upgrade head")
            return False
        
        # Check for existing crawls
        crawls = db.query(WebsiteCrawl).filter(WebsiteCrawl.tenant_id == 1).all()
        if crawls:
            print(f"\n📊 Found {len(crawls)} existing crawls for tenant 1:")
            for crawl in crawls[:5]:  # Show first 5
                print(f"   - {crawl.website_url} (Status: {crawl.status}, ID: {crawl.website_id})")
        else:
            print("\n📊 No existing crawls for tenant 1")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_aws_bedrock():
    """Check AWS Bedrock connectivity"""
    print("\n" + "="*70)
    print("2. CHECKING AWS BEDROCK")
    print("="*70)
    
    try:
        region = os.getenv('AWS_REGION')
        bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        
        # Try to list knowledge bases
        response = bedrock_agent.list_knowledge_bases(maxResults=5)
        kb_count = len(response.get('knowledgeBaseSummaries', []))
        
        print(f"✅ Bedrock Agent accessible")
        print(f"   Existing knowledge bases: {kb_count}")
        
        if kb_count > 0:
            print("\n   Recent knowledge bases:")
            for kb in response['knowledgeBaseSummaries'][:3]:
                print(f"   - {kb['name']} ({kb['knowledgeBaseId']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock error: {e}")
        return False


def check_opensearch():
    """Check OpenSearch Serverless"""
    print("\n" + "="*70)
    print("3. CHECKING OPENSEARCH SERVERLESS")
    print("="*70)
    
    try:
        region = os.getenv('AWS_REGION')
        aoss_client = boto3.client('opensearchserverless', region_name=region)
        
        # List collections
        response = aoss_client.list_collections()
        collections = response.get('collectionSummaries', [])
        
        print(f"✅ OpenSearch Serverless accessible")
        print(f"   Existing collections: {len(collections)}")
        
        if collections:
            print("\n   Collections:")
            for coll in collections:
                print(f"   - {coll['name']} ({coll['status']})")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenSearch error: {e}")
        return False


def check_recent_crawls():
    """Check for recent crawl attempts and their status"""
    print("\n" + "="*70)
    print("4. CHECKING RECENT CRAWL ATTEMPTS")
    print("="*70)
    
    try:
        db = SessionLocal()
        
        # Get most recent crawls
        recent_crawls = db.query(WebsiteCrawl).order_by(
            WebsiteCrawl.created_at.desc()
        ).limit(5).all()
        
        if not recent_crawls:
            print("📊 No crawl attempts found")
            return True
        
        print(f"📊 Found {len(recent_crawls)} recent crawl attempts:\n")
        
        for i, crawl in enumerate(recent_crawls, 1):
            print(f"   {i}. Website: {crawl.website_url}")
            print(f"      Status: {crawl.status}")
            print(f"      Created: {crawl.created_at}")
            print(f"      Pages: {crawl.pages_crawled}/{crawl.max_pages}")
            
            if crawl.status == "FAILED":
                print(f"      ❌ Error: {crawl.error_message}")
            
            if crawl.knowledge_base_id:
                print(f"      KB ID: {crawl.knowledge_base_id}")
            
            print()
        
        # Check for stuck crawls
        stuck_crawls = db.query(WebsiteCrawl).filter(
            WebsiteCrawl.status.in_(['STARTING', 'IN_PROGRESS'])
        ).all()
        
        if stuck_crawls:
            print(f"⚠️  Found {len(stuck_crawls)} crawls that might be stuck:")
            for crawl in stuck_crawls:
                print(f"   - {crawl.website_url} ({crawl.status}) - Created: {crawl.created_at}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking crawls: {e}")
        return False


def check_dotstark_specific():
    """Check for dotstark.com specific issues"""
    print("\n" + "="*70)
    print("5. CHECKING DOTSTARK.COM SPECIFIC")
    print("="*70)
    
    try:
        db = SessionLocal()
        
        # Check for dotstark crawls
        dotstark_crawls = db.query(WebsiteCrawl).filter(
            WebsiteCrawl.website_url.like('%dotstark%')
        ).all()
        
        if not dotstark_crawls:
            print("📊 No previous dotstark.com crawls found")
            print("   This will be a fresh crawl")
            return True
        
        print(f"📊 Found {len(dotstark_crawls)} previous dotstark.com crawls:\n")
        
        for crawl in dotstark_crawls:
            print(f"   URL: {crawl.website_url}")
            print(f"   Status: {crawl.status}")
            print(f"   Created: {crawl.created_at}")
            print(f"   Website ID: {crawl.website_id}")
            
            if crawl.status == "COMPLETE":
                print(f"   ✅ Successfully crawled {crawl.pages_crawled} pages")
            elif crawl.status == "FAILED":
                print(f"   ❌ Failed: {crawl.error_message}")
            elif crawl.status in ["STARTING", "IN_PROGRESS"]:
                print(f"   ⏳ Still in progress")
            
            print()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_url_accessibility():
    """Check if dotstark.com is accessible"""
    print("\n" + "="*70)
    print("6. CHECKING URL ACCESSIBILITY")
    print("="*70)
    
    try:
        import requests
        
        url = "https://dotstark.com"
        print(f"Testing: {url}")
        
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        print(f"✅ URL is accessible")
        print(f"   Status Code: {response.status_code}")
        print(f"   Final URL: {response.url}")
        print(f"   Content Length: {len(response.content)} bytes")
        
        # Check robots.txt
        robots_url = "https://dotstark.com/robots.txt"
        try:
            robots_response = requests.get(robots_url, timeout=5)
            if robots_response.status_code == 200:
                print(f"\n   robots.txt found:")
                print(f"   {robots_response.text[:200]}")
        except:
            print(f"\n   No robots.txt found (this is okay)")
        
        return True
        
    except Exception as e:
        print(f"❌ URL not accessible: {e}")
        print("   This might cause crawling to fail")
        return False


def main():
    """Run all checks"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST FAILURE DIAGNOSIS")
    print("="*70)
    
    results = {
        'Database': check_database(),
        'AWS Bedrock': check_aws_bedrock(),
        'OpenSearch': check_opensearch(),
        'Recent Crawls': check_recent_crawls(),
        'DotStark Specific': check_dotstark_specific(),
        'URL Accessibility': check_url_accessibility()
    }
    
    print("\n" + "="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {check}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n   Score: {passed_count}/{total_count} checks passed")
    
    if passed_count == total_count:
        print("\n✅ All checks passed!")
        print("\nThe system appears to be working correctly.")
        print("If the test still fails, please run:")
        print("   python debug_test.py")
        print("\nAnd share the output to see the exact error.")
    else:
        print("\n❌ Some checks failed.")
        print("\nPlease fix the issues above before running the test.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
