"""
Check Knowledge Base and Ingestion Job status directly in AWS
"""
import boto3
import sys
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def check_knowledge_base(kb_id: str):
    """Check knowledge base status"""
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
        print(f"\n{'='*70}")
        print(f"  KNOWLEDGE BASE: {kb_id}")
        print(f"{'='*70}\n")
        
        # Get knowledge base details
        kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        kb = kb_response['knowledgeBase']
        
        print(f"📚 Knowledge Base:")
        print(f"   Name: {kb.get('name')}")
        print(f"   Status: {kb.get('status')}")
        print(f"   Created: {kb.get('createdAt')}")
        print(f"   Updated: {kb.get('updatedAt')}")
        
        # List data sources
        print(f"\n📂 Data Sources:")
        ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        
        for ds in ds_response.get('dataSourceSummaries', []):
            print(f"\n   Data Source ID: {ds.get('dataSourceId')}")
            print(f"   Name: {ds.get('name')}")
            print(f"   Status: {ds.get('status')}")
            
            # Get ingestion jobs for this data source
            try:
                jobs_response = bedrock_agent.list_ingestion_jobs(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds.get('dataSourceId'),
                    maxResults=5
                )
                
                print(f"\n   📥 Recent Ingestion Jobs:")
                for job in jobs_response.get('ingestionJobSummaries', []):
                    print(f"\n      Job ID: {job.get('ingestionJobId')}")
                    print(f"      Status: {job.get('status')}")
                    print(f"      Started: {job.get('startedAt')}")
                    print(f"      Updated: {job.get('updatedAt')}")
                    
                    if job.get('statistics'):
                        stats = job['statistics']
                        print(f"      Documents Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                        print(f"      Documents Indexed: {stats.get('numberOfNewDocumentsIndexed', 0)}")
                        print(f"      Documents Failed: {stats.get('numberOfDocumentsFailed', 0)}")
                    
                    # Get detailed job info
                    if job.get('ingestionJobId'):
                        try:
                            job_detail = bedrock_agent.get_ingestion_job(
                                knowledgeBaseId=kb_id,
                                dataSourceId=ds.get('dataSourceId'),
                                ingestionJobId=job.get('ingestionJobId')
                            )
                            
                            job_info = job_detail['ingestionJob']
                            if job_info.get('failureReasons'):
                                print(f"      ❌ Failure Reasons: {job_info['failureReasons']}")
                        except Exception as e:
                            print(f"      ⚠️  Could not get job details: {e}")
                
            except Exception as e:
                print(f"   ⚠️  Could not list ingestion jobs: {e}")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error checking knowledge base: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_kb_status.py <knowledge_base_id>")
        sys.exit(1)
    
    kb_id = sys.argv[1]
    check_knowledge_base(kb_id)
