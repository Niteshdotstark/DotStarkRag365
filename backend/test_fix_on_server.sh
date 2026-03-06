#!/bin/bash

echo "======================================================================="
echo "  TESTING OPENSEARCH FIX ON SERVER"
echo "======================================================================="
echo ""

# Check if running in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   cd ~/DotStarkRag365/backend"
    exit 1
fi

echo "1️⃣  Checking if code was updated..."
if grep -q "Index will be created automatically by Bedrock" rag_model/rag_website.py; then
    echo "   ✅ Code has been updated with the fix"
else
    echo "   ❌ Code not updated. Run: git pull origin main"
    exit 1
fi

echo ""
echo "2️⃣  Checking Docker container status..."
if sudo docker ps | grep -q fastapi-backend; then
    echo "   ✅ Container is running"
else
    echo "   ❌ Container is not running"
    echo "   Run: sudo docker-compose up -d"
    exit 1
fi

echo ""
echo "3️⃣  Rebuilding container with new code..."
echo "   This will take 1-2 minutes..."
sudo docker-compose up -d --build backend

echo ""
echo "4️⃣  Waiting for container to be ready..."
sleep 15

echo ""
echo "5️⃣  Testing the fix..."
sudo docker exec -it fastapi-backend python -c "
import sys
sys.path.insert(0, '/app')

print('Testing OpenSearch fix...')
print('')

# Check if the fix is in the code
with open('/app/rag_model/rag_website.py', 'r') as f:
    content = f.read()
    if 'Index will be created automatically by Bedrock' in content:
        print('✅ Fix is present in container')
    else:
        print('❌ Fix not found in container')
        sys.exit(1)

print('')
print('Testing AWS access...')

import boto3
import os
from dotenv import load_dotenv

load_dotenv('/app/env')

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Test AWS credentials
try:
    sts = boto3.client('sts', region_name=AWS_REGION)
    identity = sts.get_caller_identity()
    print(f'✅ AWS credentials valid')
    print(f'   Account: {identity[\"Account\"]}')
except Exception as e:
    print(f'❌ AWS credentials error: {e}')
    sys.exit(1)

print('')
print('Testing OpenSearch collection...')

# Check collection
try:
    aoss = boto3.client('opensearchserverless', region_name=AWS_REGION)
    collection_id = 'r0fqf4rli0n632ypd4la'
    response = aoss.batch_get_collection(ids=[collection_id])
    
    if response['collectionDetails']:
        coll = response['collectionDetails'][0]
        print(f'✅ Collection is {coll[\"status\"]}')
        print(f'   Name: {coll[\"name\"]}')
    else:
        print(f'❌ Collection not found')
        sys.exit(1)
except Exception as e:
    print(f'❌ Collection error: {e}')
    sys.exit(1)

print('')
print('='*70)
print('  ✅ ALL CHECKS PASSED - READY TO TEST CRAWL!')
print('='*70)
print('')
print('Run this command to test a crawl:')
print('  sudo docker exec -it fastapi-backend python test_new_crawl.py')
"

echo ""
echo "======================================================================="
echo "  TEST COMPLETE"
echo "======================================================================="
