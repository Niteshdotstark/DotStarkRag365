"""
IMMEDIATE CLEANUP - Delete OpenSearch Collections NOW
Run this immediately after testing to avoid $700/month charges!

Usage:
    python IMMEDIATE_CLEANUP.py
"""
import boto3
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("..").resolve() / "env"
load_dotenv(dotenv_path=env_path)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

print("\n" + "="*70)
print("⚠️  IMMEDIATE CLEANUP - STOP OPENSEARCH CHARGES")
print("="*70)
print("\n🎯 This script will:")
print("  1. List all OpenSearch Serverless collections")
print("  2. List all Bedrock Knowledge Bases")
print("  3. Delete ALL of them to stop charges")
print("\n💰 Estimated savings: ~$700/month per collection")
print("="*70)

def delete_all_now():
    """Delete everything immediately"""
    
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    # Step 1: Delete all Knowledge Bases
    print("\n" + "="*70)
    print("STEP 1: DELETING KNOWLEDGE BASES")
    print("="*70)
    
    try:
        response = bedrock_agent.list_knowledge_bases(maxResults=100)
        kbs = response.get('knowledgeBaseSummaries', [])
        
        if not kbs:
            print("\n✅ No Knowledge Bases found")
        else:
            print(f"\nFound {len(kbs)} Knowledge Bases\n")
            for kb in kbs:
                try:
                    print(f"🗑️  Deleting: {kb['name']} ({kb['knowledgeBaseId']})")
                    bedrock_agent.delete_knowledge_base(knowledgeBaseId=kb['knowledgeBaseId'])
                    print(f"   ✅ Deleted")
                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
    except Exception as e:
        print(f"❌ Error listing KBs: {e}")
    
    # Step 2: Delete all Collections
    print("\n" + "="*70)
    print("STEP 2: DELETING OPENSEARCH COLLECTIONS")
    print("="*70)
    
    try:
        response = aoss_client.list_collections()
        collections = response.get('collectionSummaries', [])
        
        if not collections:
            print("\n✅ No OpenSearch collections found")
            print("💰 You're not being charged for OpenSearch!")
        else:
            print(f"\nFound {len(collections)} collections\n")
            
            for col in collections:
                print(f"🗑️  Deleting: {col['name']} ({col['id']})")
                
                # Delete associated policies
                if col['name'].startswith('kb-collection-'):
                    tenant_id = col['name'].replace('kb-collection-', '')
                    
                    # Encryption policy
                    try:
                        aoss_client.delete_security_policy(
                            name=f'kb-encryption-{tenant_id}',
                            type='encryption'
                        )
                        print(f"   ✅ Deleted encryption policy")
                    except:
                        pass
                    
                    # Network policy
                    try:
                        aoss_client.delete_security_policy(
                            name=f'kb-network-{tenant_id}',
                            type='network'
                        )
                        print(f"   ✅ Deleted network policy")
                    except:
                        pass
                    
                    # Data access policy
                    try:
                        aoss_client.delete_access_policy(
                            name=f'kb-policy-{tenant_id}',
                            type='data'
                        )
                        print(f"   ✅ Deleted data access policy")
                    except:
                        pass
                
                # Delete collection
                try:
                    aoss_client.delete_collection(id=col['id'])
                    print(f"   ✅ Collection deletion initiated")
                    print(f"   💰 Will save ~$700/month")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ CLEANUP COMPLETE")
    print("="*70)
    print("\n💰 OpenSearch charges will stop within the hour")
    print("⏰ Collections take a few minutes to fully delete")
    print("\n🔍 Verify deletion:")
    print("   aws opensearchserverless list-collections --region us-east-1")
    print("   aws bedrock-agent list-knowledge-bases --region us-east-1")
    print("="*70 + "\n")

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will delete ALL OpenSearch collections and Knowledge Bases!")
    print("Type 'DELETE NOW' to confirm: ", end="")
    
    confirmation = input().strip()
    
    if confirmation == "DELETE NOW":
        delete_all_now()
    else:
        print("\n❌ Cancelled. No resources were deleted.")
        print("💡 Run again and type 'DELETE NOW' to proceed.\n")
