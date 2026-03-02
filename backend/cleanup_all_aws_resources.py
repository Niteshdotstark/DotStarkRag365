"""
Cleanup script to delete ALL OpenSearch Serverless collections and Bedrock Knowledge Bases.
This will save ~$700/month per collection.

⚠️ WARNING: This will delete ALL crawled data. Use only for demo/cost savings.
"""
import boto3
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("..").resolve() / "env"
load_dotenv(dotenv_path=env_path)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def list_all_collections():
    """List all OpenSearch Serverless collections"""
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    try:
        response = aoss_client.list_collections()
        collections = response.get('collectionSummaries', [])
        
        print(f"\n{'='*70}")
        print(f"📋 FOUND {len(collections)} OPENSEARCH SERVERLESS COLLECTIONS")
        print(f"{'='*70}\n")
        
        for col in collections:
            print(f"Collection: {col['name']}")
            print(f"  ID: {col['id']}")
            print(f"  ARN: {col['arn']}")
            print(f"  Status: {col['status']}")
            print(f"  💰 Cost: ~$700/month")
            print()
        
        return collections
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return []

def list_all_knowledge_bases():
    """List all Bedrock Knowledge Bases"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    try:
        response = bedrock_agent.list_knowledge_bases(maxResults=100)
        kbs = response.get('knowledgeBaseSummaries', [])
        
        print(f"\n{'='*70}")
        print(f"🧠 FOUND {len(kbs)} BEDROCK KNOWLEDGE BASES")
        print(f"{'='*70}\n")
        
        for kb in kbs:
            print(f"Knowledge Base: {kb['name']}")
            print(f"  ID: {kb['knowledgeBaseId']}")
            print(f"  Status: {kb['status']}")
            print(f"  Updated: {kb.get('updatedAt', 'N/A')}")
            print()
        
        return kbs
    except Exception as e:
        print(f"❌ Error listing knowledge bases: {e}")
        return []

def delete_knowledge_base(kb_id, kb_name):
    """Delete a Bedrock Knowledge Base"""
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    try:
        print(f"🗑️  Deleting Knowledge Base: {kb_name} ({kb_id})...")
        bedrock_agent.delete_knowledge_base(knowledgeBaseId=kb_id)
        print(f"   ✅ Deleted successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def delete_collection(collection_id, collection_name):
    """Delete an OpenSearch Serverless collection"""
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    try:
        print(f"🗑️  Deleting Collection: {collection_name} ({collection_id})...")
        aoss_client.delete_collection(id=collection_id)
        print(f"   ✅ Deletion initiated (takes a few minutes)")
        print(f"   💰 Will save ~$700/month")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def delete_security_policies(collection_name):
    """Delete security policies associated with a collection"""
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    # Extract tenant_id from collection name (format: kb-collection-{tenant_id})
    if collection_name.startswith('kb-collection-'):
        tenant_id = collection_name.replace('kb-collection-', '')
        
        policies = [
            ('encryption', f'kb-encryption-{tenant_id}'),
            ('network', f'kb-network-{tenant_id}'),
        ]
        
        for policy_type, policy_name in policies:
            try:
                print(f"   🗑️  Deleting {policy_type} policy: {policy_name}...")
                aoss_client.delete_security_policy(
                    name=policy_name,
                    type=policy_type
                )
                print(f"      ✅ Deleted")
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"      ⚠️  {e}")

def delete_data_access_policy(collection_name):
    """Delete data access policy associated with a collection"""
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    # Extract tenant_id from collection name
    if collection_name.startswith('kb-collection-'):
        tenant_id = collection_name.replace('kb-collection-', '')
        policy_name = f'kb-policy-{tenant_id}'
        
        try:
            print(f"   🗑️  Deleting data access policy: {policy_name}...")
            aoss_client.delete_access_policy(
                name=policy_name,
                type='data'
            )
            print(f"      ✅ Deleted")
        except Exception as e:
            if 'ResourceNotFoundException' not in str(e):
                print(f"      ⚠️  {e}")

def cleanup_all():
    """Main cleanup function"""
    print("\n" + "="*70)
    print("⚠️  AWS RESOURCE CLEANUP - COST SAVINGS MODE")
    print("="*70)
    print("\nThis script will delete:")
    print("  • All Bedrock Knowledge Bases")
    print("  • All OpenSearch Serverless collections")
    print("  • All associated security policies")
    print("\n💰 Estimated savings: ~$700/month per collection")
    print("\n⚠️  WARNING: This will delete all crawled data!")
    print("="*70)
    
    # Confirm
    response = input("\nType 'DELETE ALL' to confirm (or anything else to cancel): ")
    if response != 'DELETE ALL':
        print("\n❌ Cancelled. No resources were deleted.")
        return
    
    print("\n🚀 Starting cleanup...\n")
    
    # Step 1: Delete all Knowledge Bases
    print("\n" + "="*70)
    print("STEP 1: DELETING KNOWLEDGE BASES")
    print("="*70 + "\n")
    
    kbs = list_all_knowledge_bases()
    kb_deleted = 0
    
    for kb in kbs:
        if delete_knowledge_base(kb['knowledgeBaseId'], kb['name']):
            kb_deleted += 1
    
    print(f"\n✅ Deleted {kb_deleted}/{len(kbs)} Knowledge Bases")
    
    # Step 2: Delete all Collections
    print("\n" + "="*70)
    print("STEP 2: DELETING OPENSEARCH COLLECTIONS")
    print("="*70 + "\n")
    
    collections = list_all_collections()
    col_deleted = 0
    
    for col in collections:
        # Delete associated policies first
        delete_security_policies(col['name'])
        delete_data_access_policy(col['name'])
        
        # Delete collection
        if delete_collection(col['id'], col['name']):
            col_deleted += 1
    
    print(f"\n✅ Deleted {col_deleted}/{len(collections)} Collections")
    
    # Summary
    print("\n" + "="*70)
    print("🎉 CLEANUP COMPLETE")
    print("="*70)
    print(f"\nDeleted:")
    print(f"  • {kb_deleted} Knowledge Bases")
    print(f"  • {col_deleted} OpenSearch Collections")
    print(f"\n💰 Estimated monthly savings: ~${col_deleted * 700}")
    print("\n⚠️  Note: Collections take a few minutes to fully delete.")
    print("Check AWS Console to confirm deletion.")
    print("="*70 + "\n")

def list_only():
    """Just list resources without deleting"""
    print("\n" + "="*70)
    print("📋 AWS RESOURCE INVENTORY")
    print("="*70)
    
    kbs = list_all_knowledge_bases()
    collections = list_all_collections()
    
    print("\n" + "="*70)
    print("💰 COST ESTIMATE")
    print("="*70)
    print(f"\nKnowledge Bases: {len(kbs)} × ~$1/month = ~${len(kbs)}/month")
    print(f"OpenSearch Collections: {len(collections)} × ~$700/month = ~${len(collections) * 700}/month")
    print(f"\n📊 Total estimated monthly cost: ~${len(kbs) + (len(collections) * 700)}/month")
    print("="*70 + "\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        # Just list resources
        list_only()
    else:
        # Full cleanup
        cleanup_all()
