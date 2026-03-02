"""
Cleanup script to delete ALL OpenSearch collections EXCEPT one for demo.
Keeps the most recently used collection.

💰 Saves: ~$700/month per deleted collection
"""
import boto3
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables
env_path = Path("..").resolve() / "env"
load_dotenv(dotenv_path=env_path)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def get_collection_last_used(collection_id):
    """Get the last time a collection was used (via knowledge bases)"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    try:
        # List all knowledge bases
        response = bedrock_agent.list_knowledge_bases(maxResults=100)
        kbs = response.get('knowledgeBaseSummaries', [])
        
        # Find KBs using this collection
        latest_update = None
        for kb in kbs:
            try:
                kb_detail = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb['knowledgeBaseId'])
                kb_info = kb_detail['knowledgeBase']
                
                # Check if this KB uses our collection
                storage_config = kb_info.get('storageConfiguration', {})
                if storage_config.get('type') == 'OPENSEARCH_SERVERLESS':
                    # Compare collection ARNs or names
                    updated_at = kb.get('updatedAt')
                    if updated_at and (not latest_update or updated_at > latest_update):
                        latest_update = updated_at
            except:
                continue
        
        return latest_update
    except:
        return None

def cleanup_keep_one_demo():
    """Delete all collections except the most recently used one"""
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    print("\n" + "="*70)
    print("⚠️  CLEANUP: KEEP ONE DEMO COLLECTION")
    print("="*70)
    print("\nThis script will:")
    print("  ✅ Keep the most recently used collection for demo")
    print("  🗑️  Delete all other collections")
    print("  💰 Save ~$700/month per deleted collection")
    print("="*70)
    
    # List all collections
    try:
        response = aoss_client.list_collections()
        collections = response.get('collectionSummaries', [])
    except Exception as e:
        print(f"\n❌ Error listing collections: {e}")
        return
    
    if not collections:
        print("\n✅ No collections found. Nothing to delete.")
        return
    
    print(f"\n📋 Found {len(collections)} collections\n")
    
    # Find the most recently used collection
    collection_usage = []
    for col in collections:
        last_used = get_collection_last_used(col['id'])
        collection_usage.append({
            'collection': col,
            'last_used': last_used or datetime.min
        })
        
        status = "🟢 ACTIVE" if last_used else "⚪ UNUSED"
        print(f"{status} {col['name']}")
        print(f"     ID: {col['id']}")
        print(f"     Last used: {last_used or 'Never'}")
        print()
    
    # Sort by last used (most recent first)
    collection_usage.sort(key=lambda x: x['last_used'], reverse=True)
    
    keep_collection = collection_usage[0]['collection']
    delete_collections = [item['collection'] for item in collection_usage[1:]]
    
    print("\n" + "="*70)
    print("📌 PLAN")
    print("="*70)
    print(f"\n✅ KEEP (for demo): {keep_collection['name']}")
    print(f"   ID: {keep_collection['id']}")
    print(f"   💰 Cost: ~$700/month")
    
    if delete_collections:
        print(f"\n🗑️  DELETE ({len(delete_collections)} collections):")
        for col in delete_collections:
            print(f"   • {col['name']} (ID: {col['id']})")
        print(f"\n💰 Total savings: ~${len(delete_collections) * 700}/month")
    else:
        print("\n✅ No other collections to delete.")
    
    print("="*70)
    
    if not delete_collections:
        print("\n✅ Only one collection exists. Nothing to delete.")
        return
    
    # Confirm
    response = input(f"\nType 'DELETE {len(delete_collections)}' to confirm (or anything else to cancel): ")
    if response != f'DELETE {len(delete_collections)}':
        print("\n❌ Cancelled. No resources were deleted.")
        return
    
    print("\n🚀 Starting cleanup...\n")
    
    deleted_count = 0
    
    for col in delete_collections:
        print(f"\n{'='*70}")
        print(f"Deleting: {col['name']}")
        print(f"{'='*70}")
        
        # Step 1: Find and delete associated Knowledge Bases
        try:
            kb_response = bedrock_agent.list_knowledge_bases(maxResults=100)
            kbs = kb_response.get('knowledgeBaseSummaries', [])
            
            for kb in kbs:
                try:
                    kb_detail = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb['knowledgeBaseId'])
                    kb_info = kb_detail['knowledgeBase']
                    
                    # Check if this KB uses our collection
                    storage_config = kb_info.get('storageConfiguration', {})
                    if storage_config.get('type') == 'OPENSEARCH_SERVERLESS':
                        collection_arn = storage_config.get('opensearchServerlessConfiguration', {}).get('collectionArn', '')
                        if col['id'] in collection_arn or col['name'] in collection_arn:
                            print(f"   🗑️  Deleting Knowledge Base: {kb['name']}...")
                            bedrock_agent.delete_knowledge_base(knowledgeBaseId=kb['knowledgeBaseId'])
                            print(f"      ✅ Deleted")
                except Exception as e:
                    print(f"      ⚠️  Error: {e}")
        except Exception as e:
            print(f"   ⚠️  Error listing KBs: {e}")
        
        # Step 2: Delete security policies
        if col['name'].startswith('kb-collection-'):
            tenant_id = col['name'].replace('kb-collection-', '')
            
            # Encryption policy
            try:
                print(f"   🗑️  Deleting encryption policy...")
                aoss_client.delete_security_policy(
                    name=f'kb-encryption-{tenant_id}',
                    type='encryption'
                )
                print(f"      ✅ Deleted")
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"      ⚠️  {e}")
            
            # Network policy
            try:
                print(f"   🗑️  Deleting network policy...")
                aoss_client.delete_security_policy(
                    name=f'kb-network-{tenant_id}',
                    type='network'
                )
                print(f"      ✅ Deleted")
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"      ⚠️  {e}")
            
            # Data access policy
            try:
                print(f"   🗑️  Deleting data access policy...")
                aoss_client.delete_access_policy(
                    name=f'kb-policy-{tenant_id}',
                    type='data'
                )
                print(f"      ✅ Deleted")
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"      ⚠️  {e}")
        
        # Step 3: Delete collection
        try:
            print(f"   🗑️  Deleting collection...")
            aoss_client.delete_collection(id=col['id'])
            print(f"      ✅ Deletion initiated")
            print(f"      💰 Will save ~$700/month")
            deleted_count += 1
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("🎉 CLEANUP COMPLETE")
    print("="*70)
    print(f"\n✅ Kept for demo: {keep_collection['name']}")
    print(f"🗑️  Deleted: {deleted_count} collections")
    print(f"💰 Monthly savings: ~${deleted_count * 700}")
    print(f"💰 Remaining cost: ~$700/month (1 demo collection)")
    print("\n⚠️  Note: Collections take a few minutes to fully delete.")
    print("="*70 + "\n")

if __name__ == "__main__":
    cleanup_keep_one_demo()
