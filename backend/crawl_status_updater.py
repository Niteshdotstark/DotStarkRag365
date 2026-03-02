"""
Background task to automatically update crawl statuses from AWS.
This runs periodically to sync database with AWS Bedrock status.
"""
import time
import boto3
import os
from dotenv import load_dotenv
from database import SessionLocal
from models import WebsiteCrawl
from datetime import datetime, timedelta

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
CHECK_INTERVAL = 30  # Check every 30 seconds

def update_crawl_statuses():
    """
    Check all active crawls and update their status from AWS.
    Only checks crawls that are STARTING or IN_PROGRESS.
    Once a crawl is COMPLETE or FAILED, it won't be checked again.
    """
    db = SessionLocal()
    
    try:
        # Get only crawls that are still in progress (not COMPLETE or FAILED)
        active_crawls = db.query(WebsiteCrawl).filter(
            WebsiteCrawl.status.in_(['STARTING', 'IN_PROGRESS'])
        ).all()
        
        if not active_crawls:
            # Only print this occasionally to avoid spam
            return
        
        print(f"\n[{datetime.now()}] Checking {len(active_crawls)} active crawls...")
        
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
        for crawl in active_crawls:
            # Skip if missing required IDs
            if not crawl.knowledge_base_id or not crawl.data_source_id or not crawl.ingestion_job_id:
                print(f"  ⚠️  Crawl {crawl.website_id} missing AWS IDs, skipping")
                continue
            
            try:
                # Get job status from AWS
                response = bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=crawl.knowledge_base_id,
                    dataSourceId=crawl.data_source_id,
                    ingestionJobId=crawl.ingestion_job_id
                )
                
                job = response['ingestionJob']
                aws_status = job['status']
                statistics = job.get('statistics', {})
                pages_crawled = statistics.get('numberOfDocumentsScanned', 0)
                
                # Check if status changed
                if aws_status != crawl.status:
                    print(f"  📊 Crawl {crawl.website_id} ({crawl.website_url})")
                    print(f"     Status: {crawl.status} → {aws_status}")
                    print(f"     Pages: {pages_crawled}")
                    
                    crawl.status = aws_status
                    crawl.pages_crawled = pages_crawled
                    
                    # Handle failures
                    if aws_status == 'FAILED':
                        failure_reasons = job.get('failureReasons', ['Unknown error'])
                        crawl.error_message = failure_reasons[0] if isinstance(failure_reasons, list) else str(failure_reasons)
                        print(f"     ❌ Error: {crawl.error_message}")
                    
                    db.commit()
                    print(f"     ✅ Database updated")
                else:
                    # Update pages_crawled even if status hasn't changed
                    if pages_crawled != crawl.pages_crawled:
                        crawl.pages_crawled = pages_crawled
                        db.commit()
                
            except Exception as e:
                print(f"  ❌ Error checking crawl {crawl.website_id}: {e}")
                
                # If resource not found, mark as failed
                if 'ResourceNotFoundException' in str(e):
                    crawl.status = 'FAILED'
                    crawl.error_message = f"AWS resource not found: {str(e)}"
                    db.commit()
        
        print(f"[{datetime.now()}] Status check complete\n")
        
    except Exception as e:
        print(f"❌ Error in update_crawl_statuses: {e}")
    finally:
        db.close()

def run_status_updater():
    """
    Run the status updater in a loop.
    """
    print(f"\n{'='*60}")
    print(f"🔄 Crawl Status Updater Started")
    print(f"   Checking every {CHECK_INTERVAL} seconds")
    print(f"{'='*60}\n")
    
    while True:
        try:
            update_crawl_statuses()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n🛑 Status updater stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_status_updater()
