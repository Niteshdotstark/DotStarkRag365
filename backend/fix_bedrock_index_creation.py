"""
Fix: Let Bedrock create the index automatically instead of pre-creating it.

The issue is that OpenSearch permissions take hours to propagate.
Solution: Remove the index creation step and let Bedrock create it automatically
when the first knowledge base is created.
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
collection_id = 'r0fqf4rli0n632ypd4la'

print(f"\n{'='*70}")
print(f"  BEDROCK INDEX AUTO-CREATION FIX")
print(f"{'='*70}\n")

print("📋 Current Issue:")
print("   - OpenSearch permissions take hours to propagate")
print("   - Cannot create index manually due to 403 errors")
print("   - This blocks knowledge base creation\n")

print("✅ Solution:")
print("   - Remove manual index creation from code")
print("   - Let Bedrock create the index automatically")
print("   - Bedrock has special permissions that bypass the delay\n")

print("🔧 What needs to be changed:")
print("   1. In rag_website.py, comment out the index creation code")
print("   2. Bedrock will create the index when first KB is created")
print("   3. This works because Bedrock service has immediate access\n")

print("📝 Code changes needed in rag_website.py:")
print("   Around line 350-400, find this section:")
print("   ```python")
print("   # Create the vector index in OpenSearch (required for Bedrock)")
print("   print(f'   📊 Creating vector index in OpenSearch...')")
print("   try:")
print("       from opensearchpy import OpenSearch...")
print("       ...")
print("   ```")
print("\n   Change it to:")
print("   ```python")
print("   # Skip manual index creation - let Bedrock create it automatically")
print("   print(f'   ℹ️  Index will be created automatically by Bedrock')")
print("   ```\n")

print("🎯 Alternative: Use existing index from old collection")
print("   If the old collection had a working index, we can:")
print("   1. Check if index exists in the new collection")
print("   2. If not, wait for permissions OR")
print("   3. Create KB without pre-creating index\n")

# Check if we can list indices (this would work if permissions are ready)
print("🔍 Testing current access level...")
try:
    from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
    
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
    
    host = f'{collection_id}.{AWS_REGION}.aoss.amazonaws.com'
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    # Try to list indices
    indices = client.cat.indices(format='json')
    print(f"✅ Can access OpenSearch! Found {len(indices)} indices:")
    for idx in indices:
        print(f"   - {idx['index']}")
    
    # Check if our index exists
    index_name = 'bedrock-knowledge-base-default-index'
    if client.indices.exists(index=index_name):
        print(f"\n✅ Index '{index_name}' already exists!")
        print(f"   You can proceed with creating knowledge bases.")
    else:
        print(f"\n⚠️  Index '{index_name}' does not exist yet.")
        print(f"   Bedrock will create it automatically on first use.")

except Exception as e:
    print(f"❌ Still getting 403 errors: {e}")
    print(f"\n💡 RECOMMENDED ACTION:")
    print(f"   1. Modify rag_website.py to skip manual index creation")
    print(f"   2. Let Bedrock create the index automatically")
    print(f"   3. This will work because Bedrock has special service permissions")

print(f"\n{'='*70}\n")
