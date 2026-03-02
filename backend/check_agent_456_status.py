"""
Check status of agent 456 crawls and knowledge bases
"""
import boto3
from database import SessionLocal
from models import WebsiteCrawl

AWS_REGION = 'us-east-1'

db = SessionLocal()

# Get all crawls for agent 456
crawls = db.query(WebsiteCrawl).filter_by(agent_id=456).all()

print(f"Found {len(crawls)} crawls for agent 456\n")

bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)

for crawl in crawls:
    print(f"Crawl: {crawl.website_id}")
    print(f"  Status (DB): {crawl.status}")
    print(f"  KB ID: {crawl.knowledge_base_id}")
    print(f"  Data Source ID: {crawl.data_source_id}")
    print(f"  Ingestion Job ID: {crawl.ingestion_job_id}")
    
    if crawl.knowledge_base_id and crawl.data_source_id and crawl.ingestion_job_id:
        try:
            # Check ingestion job status
            response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=crawl.knowledge_base_id,
                dataSourceId=crawl.data_source_id,
                ingestionJobId=crawl.ingestion_job_id
            )
            
            job = response['ingestionJob']
            print(f"  Status (AWS): {job['status']}")
            
            if job.get('statistics'):
                stats = job['statistics']
                print(f"  Documents scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                print(f"  Documents indexed: {stats.get('numberOfDocumentsIndexed', 0)}")
                print(f"  Documents failed: {stats.get('numberOfDocumentsFailed', 0)}")
        except Exception as e:
            print(f"  Error checking AWS status: {e}")
    
    print()

db.close()
