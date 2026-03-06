"""
List all active ingestion jobs across all knowledge bases
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def list_all_ingestion_jobs():
    """List all active ingestion jobs"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    print(f"\n{'='*70}")
    print(f"  ACTIVE INGESTION JOBS")
    print(f"{'='*70}\n")
    
    try:
        # List all knowledge bases
        kb_response = bedrock_agent.list_knowledge_bases(maxResults=100)
        knowledge_bases = kb_response.get('knowledgeBaseSummaries', [])
        
        print(f"Found {len(knowledge_bases)} knowledge bases\n")
        
        total_jobs = 0
        active_jobs = 0
        
        for kb in knowledge_bases:
            kb_id = kb['knowledgeBaseId']
            kb_name = kb['name']
            kb_status = kb['status']
            
            print(f"📚 Knowledge Base: {kb_name}")
            print(f"   ID: {kb_id}")
            print(f"   Status: {kb_status}")
            
            # List data sources for this KB
            try:
                ds_response = bedrock_agent.list_data_sources(
                    knowledgeBaseId=kb_id,
                    maxResults=100
                )
                
                for ds in ds_response.get('dataSourceSummaries', []):
                    ds_id = ds['dataSourceId']
                    ds_name = ds['name']
                    
                    # List ingestion jobs for this data source
                    try:
                        jobs_response = bedrock_agent.list_ingestion_jobs(
                            knowledgeBaseId=kb_id,
                            dataSourceId=ds_id,
                            maxResults=10
                        )
                        
                        for job in jobs_response.get('ingestionJobSummaries', []):
                            total_jobs += 1
                            job_id = job['ingestionJobId']
                            job_status = job['status']
                            started_at = job.get('startedAt', 'N/A')
                            
                            status_emoji = {
                                'STARTING': '🟡',
                                'IN_PROGRESS': '🔵',
                                'COMPLETE': '✅',
                                'FAILED': '❌'
                            }.get(job_status, '⚪')
                            
                            print(f"\n   {status_emoji} Ingestion Job:")
                            print(f"      Job ID: {job_id}")
                            print(f"      Status: {job_status}")
                            print(f"      Started: {started_at}")
                            
                            if job_status in ['STARTING', 'IN_PROGRESS']:
                                active_jobs += 1
                                
                                # Get detailed stats
                                try:
                                    job_detail = bedrock_agent.get_ingestion_job(
                                        knowledgeBaseId=kb_id,
                                        dataSourceId=ds_id,
                                        ingestionJobId=job_id
                                    )
                                    stats = job_detail['ingestionJob'].get('statistics', {})
                                    print(f"      Documents Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                                except:
                                    pass
                    
                    except Exception as e:
                        print(f"   ⚠️  Could not list jobs for data source {ds_id}: {e}")
            
            except Exception as e:
                print(f"   ⚠️  Could not list data sources: {e}")
            
            print()
        
        print(f"{'='*70}")
        print(f"📊 SUMMARY:")
        print(f"   Total Jobs: {total_jobs}")
        print(f"   Active Jobs (STARTING/IN_PROGRESS): {active_jobs}")
        print(f"   AWS Limit: 5 concurrent jobs")
        print(f"   Available Slots: {max(0, 5 - active_jobs)}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_all_ingestion_jobs()
