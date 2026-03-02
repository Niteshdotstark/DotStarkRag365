"""
Sync crawl status from AWS to database
"""
import boto3
import sys
import os
from dotenv import load_dotenv
from database import get_db
from models import WebsiteCrawl

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def sync_crawl_by_kb_id(kb_id: str):
    """Sync crawl status by knowledge base ID"""
    
    db = next(get_db())
    
    try:
        # Find crawl in database
        crawl = db.query(WebsiteCrawl).filter(
            WebsiteCrawl.knowledge_base_id == kb_id
        ).first()
        
        if not crawl:
            print(f"❌ No crawl found with KB ID: {kb_id}")
            return
        
        print(f"\n📊 Current Database Status:")
        print(f"   Agent ID: {crawl.agent_id}")
        print(f"   URL: {crawl.website_url}")
        print(f"   Status: {crawl.status}")
        print(f"   Pages Crawled: {crawl.pages_crawled}")
        print(f"   KB ID: {crawl.knowledge_base_id}")
        print(f"   DS ID: {crawl.data_source_id}")
        print(f"   Job ID: {crawl.ingestion_job_id}")
        
        # Check AWS status
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
        if not crawl.data_source_id or not crawl.ingestion_job_id:
            # Try to find the data source and job
            print(f"\n🔍 Looking for data source and ingestion job...")
            
            ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            
            if ds_response.get('dataSourceSummaries'):
                ds = ds_response['dataSourceSummaries'][0]
                crawl.data_source_id = ds['dataSourceId']
                
                # Get latest ingestion job
                jobs_response = bedrock_agent.list_ingestion_jobs(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds['dataSourceId'],
                    maxResults=1
                )
                
                if jobs_response.get('ingestionJobSummaries'):
                    job = jobs_response['ingestionJobSummaries'][0]
                    crawl.ingestion_job_id = job['ingestionJobId']
                    
                    print(f"   ✅ Found DS ID: {crawl.data_source_id}")
                    print(f"   ✅ Found Job ID: {crawl.ingestion_job_id}")
        
        # Get job details
        if crawl.data_source_id and crawl.ingestion_job_id:
            print(f"\n🔍 Checking AWS status...")
            
            job_response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=crawl.data_source_id,
                ingestionJobId=crawl.ingestion_job_id
            )
            
            job = job_response['ingestionJob']
            aws_status = job['status']
            
            print(f"\n📊 AWS Status:")
            print(f"   Status: {aws_status}")
            
            if 'statistics' in job:
                stats = job['statistics']
                docs_scanned = stats.get('numberOfDocumentsScanned', 0)
                docs_indexed = stats.get('numberOfNewDocumentsIndexed', 0)
                docs_failed = stats.get('numberOfDocumentsFailed', 0)
                
                print(f"   Documents Scanned: {docs_scanned}")
                print(f"   Documents Indexed: {docs_indexed}")
                print(f"   Documents Failed: {docs_failed}")
                
                # Update database
                print(f"\n💾 Updating database...")
                crawl.status = aws_status
                crawl.pages_crawled = docs_scanned
                
                if docs_failed > 0 and job.get('failureReasons'):
                    crawl.error_message = str(job['failureReasons'])
                
                db.commit()
                
                print(f"   ✅ Database updated!")
                print(f"   New Status: {crawl.status}")
                print(f"   Pages Crawled: {crawl.pages_crawled}")
            else:
                print(f"   ⚠️  No statistics available yet")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sync_crawl_status.py <knowledge_base_id>")
        sys.exit(1)
    
    kb_id = sys.argv[1]
    sync_crawl_by_kb_id(kb_id)
