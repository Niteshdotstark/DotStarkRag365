"""
Delete specific knowledge bases to free up ingestion job slots
"""
import boto3
import os
import sys
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def delete_knowledge_bases(kb_ids):
    """Delete specific knowledge bases by ID"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    print(f"\n{'='*70}")
    print(f"  DELETING KNOWLEDGE BASES")
    print(f"{'='*70}\n")
    
    for kb_id in kb_ids:
        try:
            # Get KB details first
            kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
            kb_name = kb_response['knowledgeBase']['name']
            
            print(f"🗑️  Deleting: {kb_name} ({kb_id})")
            
            bedrock_agent.delete_knowledge_base(knowledgeBaseId=kb_id)
            print(f"   ✅ Deleted successfully\n")
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

if __name__ == "__main__":
    # Knowledge bases with active ingestion jobs
    active_kb_ids = [
        'SZKBSDEPAK',  # kb-agent-10
        'PAWPFRI1DG',  # kb-agent-8
        'KIPTVOBXOF',  # kb-agent-11
        'E0SCRQ6ALB',  # kb-agent-9
        'BEJCAIHHJD',  # kb-agent-7
        '6ESU49O43K',  # kb-agent-6
    ]
    
    print(f"\n⚠️  This will delete {len(active_kb_ids)} knowledge bases with active jobs")
    print(f"This will free up ingestion job slots.\n")
    
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm == 'DELETE':
        delete_knowledge_bases(active_kb_ids)
        print(f"✅ Deleted {len(active_kb_ids)} knowledge bases")
        print(f"💡 You can now start new crawls")
    else:
        print("❌ Cancelled")
