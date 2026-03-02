"""
Check the crawl status in the database and AWS.
"""
from database import get_db
from models import WebsiteCrawl
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def main():
    db = next(get_db())
    
    # Get all website crawls for tenant 1
    crawls = db.query(WebsiteCrawl).filter(WebsiteCrawl.tenant_id == 1).all()
    
    print(f"\n{'='*70}")
    print(f"  WEBSITE CRAWLS FOR TENANT 1")
    print(f"{'='*70}\n")
    
    if not crawls:
        print("❌ No crawls found for tenant 1")
        return
    
    for crawl in crawls:
        print(f"\n📊 Crawl Record:")
        print(f"   Website ID: {crawl.website_id}")
        print(f"   URL: {crawl.website_url}")
        print(f"   Status (DB): {crawl.status}")
        print(f"   Knowledge Base ID: {crawl.knowledge_base_id}")
        print(f"   Data Source ID: {crawl.data_source_id}")
        print(f"   Ingestion Job ID: {crawl.ingestion_job_id}")
        print(f"   Pages Crawled: {crawl.pages_crawled}")
        print(f"   Max Pages: {crawl.max_pages}")
        print(f"   Created: {crawl.created_at}")
        
        # Check AWS status if we have the IDs
        if crawl.knowledge_base_id and crawl.data_source_id and crawl.ingestion_job_id:
            print(f"\n   🔍 Checking AWS status...")
            
            try:
                bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
                
                response = bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=crawl.knowledge_base_id,
                    dataSourceId=crawl.data_source_id,
                    ingestionJobId=crawl.ingestion_job_id
                )
                
                job = response['ingestionJob']
                aws_status = job['status']
                
                print(f"   Status (AWS): {aws_status}")
                
                if 'statistics' in job:
                    stats = job['statistics']
                    print(f"   Documents Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                    print(f"   Documents Indexed: {stats.get('numberOfNewDocumentsIndexed', 0)}")
                    print(f"   Documents Modified: {stats.get('numberOfModifiedDocumentsIndexed', 0)}")
                    print(f"   Documents Deleted: {stats.get('numberOfDocumentsDeleted', 0)}")
                    print(f"   Documents Failed: {stats.get('numberOfDocumentsFailed', 0)}")
                
                if aws_status != crawl.status:
                    print(f"\n   ⚠️  DATABASE STATUS MISMATCH!")
                    print(f"   DB Status: {crawl.status}")
                    print(f"   AWS Status: {aws_status}")
                    print(f"\n   💡 Updating database...")
                    
                    crawl.status = aws_status
                    if 'statistics' in job:
                        crawl.pages_crawled = stats.get('numberOfDocumentsScanned', 0)
                    
                    db.commit()
                    print(f"   ✅ Database updated!")
                
            except Exception as e:
                print(f"   ❌ Error checking AWS: {e}")
        
        print(f"\n{'-'*70}")
    
    db.close()
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
