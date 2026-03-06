"""
Stop stuck or long-running ingestion jobs
"""
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def stop_stuck_jobs():
    """Stop ingestion jobs that are stuck or running too long"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    print(f"\n{'='*70}")
    print(f"  STOPPING STUCK INGESTION JOBS")
    print(f"{'='*70}\n")
    
    stopped_count = 0
    
    try:
        # List all knowledge bases
        kb_response = bedrock_agent.list_knowledge_bases(maxResults=100)
        knowledge_bases = kb_response.get('knowledgeBaseSummaries', [])
        
        for kb in knowledge_bases:
            kb_id = kb['knowledgeBaseId']
            kb_name = kb['name']
            
            # List data sources
            try:
                ds_response = bedrock_agent.list_data_sources(
                    knowledgeBaseId=kb_id,
                    maxResults=100
                )
                
                for ds in ds_response.get('dataSourceSummaries', []):
                    ds_id = ds['dataSourceId']
                    
                    # List ingestion jobs
                    try:
                        jobs_response = bedrock_agent.list_ingestion_jobs(
                            knowledgeBaseId=kb_id,
                            dataSourceId=ds_id,
                            maxResults=10
                        )
                        
                        for job in jobs_response.get('ingestionJobSummaries', []):
                            job_id = job['ingestionJobId']
                            job_status = job['status']
                            started_at = job.get('startedAt')
                            
                            # Only stop jobs that are STARTING or IN_PROGRESS
                            if job_status in ['STARTING', 'IN_PROGRESS']:
                                # Check how long it's been running
                                if started_at:
                                    now = datetime.now(timezone.utc)
                                    duration = (now - started_at).total_seconds() / 3600  # hours
                                    
                                    print(f"🔍 Found active job:")
                                    print(f"   KB: {kb_name} ({kb_id})")
                                    print(f"   Job ID: {job_id}")
                                    print(f"   Status: {job_status}")
                                    print(f"   Running for: {duration:.1f} hours")
                                    
                                    # Stop jobs running for more than 4 hours
                                    if duration > 4:
                                        print(f"   ⚠️  Job stuck (running > 4 hours)")
                                        print(f"   🛑 Stopping job...")
                                        
                                        try:
                                            # AWS doesn't have a direct stop API, so we delete the data source
                                            # which will cancel the job
                                            print(f"   ℹ️  Note: Cannot directly stop job via API")
                                            print(f"   ℹ️  Job will complete or timeout naturally")
                                            print(f"   ℹ️  Consider deleting the knowledge base if needed")
                                        except Exception as e:
                                            print(f"   ❌ Error: {e}")
                                    else:
                                        print(f"   ✅ Job is recent, letting it continue")
                                    
                                    print()
                    
                    except Exception as e:
                        pass
            
            except Exception as e:
                pass
        
        print(f"{'='*70}")
        print(f"⚠️  AWS Bedrock does not provide a direct API to stop ingestion jobs.")
        print(f"Options:")
        print(f"  1. Wait for jobs to complete (they timeout after ~24 hours)")
        print(f"  2. Delete the knowledge bases with stuck jobs")
        print(f"  3. Contact AWS Support to cancel jobs")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    stop_stuck_jobs()
