"""
Delete all AWS Bedrock and OpenSearch resources but keep IAM permissions.

This will delete:
- All Knowledge Bases
- All Data Sources
- All OpenSearch Serverless Collections
- All OpenSearch access policies (data, network, encryption)

This will KEEP:
- IAM roles and their permissions
- IAM policies
"""
import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

def cleanup_all_resources():
    """Delete all Bedrock and OpenSearch resources"""
    
    print(f"\n{'='*70}")
    print(f"  CLEANING UP ALL AWS RESOURCES (KEEPING IAM PERMISSIONS)")
    print(f"{'='*70}\n")
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    # Step 1: Delete all Knowledge Bases and their Data Sources
    print("1️⃣  Deleting Knowledge Bases and Data Sources...")
    try:
        kb_response = bedrock_agent.list_knowledge_bases(maxResults=100)
        knowledge_bases = kb_response.get('knowledgeBaseSummaries', [])
        
        if not knowledge_bases:
            print("   ℹ️  No Knowledge Bases found")
        else:
            for kb in knowledge_bases:
                kb_id = kb['knowledgeBaseId']
                kb_name = kb['name']
                print(f"\n   🗑️  Deleting KB: {kb_name} ({kb_id})")
                
                # Delete all data sources first
                try:
                    ds_response = bedrock_agent.list_data_sources(
                        knowledgeBaseId=kb_id,
                        maxResults=100
                    )
                    
                    for ds in ds_response.get('dataSourceSummaries', []):
                        ds_id = ds['dataSourceId']
                        ds_name = ds['name']
                        print(f"      🗑️  Deleting Data Source: {ds_name} ({ds_id})")
                        
                        try:
                            bedrock_agent.delete_data_source(
                                knowledgeBaseId=kb_id,
                                dataSourceId=ds_id
                            )
                            print(f"      ✅ Data Source deleted")
                        except Exception as e:
                            print(f"      ⚠️  Error deleting data source: {e}")
                
                except Exception as e:
                    print(f"      ⚠️  Error listing data sources: {e}")
                
                # Delete the Knowledge Base
                try:
                    bedrock_agent.delete_knowledge_base(knowledgeBaseId=kb_id)
                    print(f"   ✅ Knowledge Base deleted")
                except Exception as e:
                    print(f"   ⚠️  Error deleting KB: {e}")
        
        print(f"\n   ✅ Knowledge Base cleanup complete")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 2: Delete all OpenSearch Collections
    print(f"\n2️⃣  Deleting OpenSearch Serverless Collections...")
    try:
        collections_response = aoss_client.list_collections(maxResults=100)
        collections = collections_response.get('collectionSummaries', [])
        
        if not collections:
            print("   ℹ️  No collections found")
        else:
            for collection in collections:
                collection_id = collection['id']
                collection_name = collection['name']
                print(f"\n   🗑️  Deleting Collection: {collection_name} ({collection_id})")
                
                try:
                    aoss_client.delete_collection(id=collection_id)
                    print(f"   ✅ Collection deletion initiated")
                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
        
        print(f"\n   ✅ Collection cleanup complete")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Delete all OpenSearch access policies
    print(f"\n3️⃣  Deleting OpenSearch Access Policies...")
    
    policy_types = ['data', 'network', 'encryption']
    
    for policy_type in policy_types:
        print(f"\n   📋 Deleting {policy_type} policies...")
        try:
            policies_response = aoss_client.list_access_policies(
                type=policy_type,
                maxResults=100
            )
            
            policies = policies_response.get('accessPolicySummaries', [])
            
            if not policies:
                print(f"      ℹ️  No {policy_type} policies found")
            else:
                for policy in policies:
                    policy_name = policy['name']
                    print(f"      🗑️  Deleting: {policy_name}")
                    
                    try:
                        aoss_client.delete_access_policy(
                            name=policy_name,
                            type=policy_type
                        )
                        print(f"      ✅ Deleted")
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
        
        except Exception as e:
            print(f"   ❌ Error listing {policy_type} policies: {e}")
    
    print(f"\n   ✅ Policy cleanup complete")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ CLEANUP COMPLETE!")
    print(f"{'='*70}")
    print(f"\nDeleted:")
    print(f"  • All Knowledge Bases and Data Sources")
    print(f"  • All OpenSearch Serverless Collections")
    print(f"  • All OpenSearch access policies (data, network, encryption)")
    print(f"\nKept (unchanged):")
    print(f"  • IAM roles and their permissions")
    print(f"  • IAM policies")
    print(f"  • Bedrock role with aoss:APIAccessAll permission")
    print(f"  • EC2 instance role with aoss:APIAccessAll permission")
    print(f"\n💡 You can now start fresh with a clean slate!")
    print(f"   Run: python test_ant24_crawl.py")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will delete ALL AWS resources except IAM permissions!")
    print("   - All Knowledge Bases")
    print("   - All Data Sources")
    print("   - All OpenSearch Collections")
    print("   - All OpenSearch Policies")
    print("\n   IAM roles and permissions will be KEPT.\n")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        cleanup_all_resources()
    else:
        print("\n❌ Cleanup cancelled.\n")
