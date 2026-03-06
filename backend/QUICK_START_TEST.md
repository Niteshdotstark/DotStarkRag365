# Quick Start - Test the OpenSearch Fix

## TL;DR - Run These Commands

```bash
# SSH into your server
ssh ubuntu@your-server-ip

# Navigate to backend directory
cd ~/DotStarkRag365/backend

# Pull latest code
git pull origin main

# Restart backend
sudo docker-compose restart fastapi-backend

# Wait 10 seconds for restart
sleep 10

# Verify everything is ready
sudo docker exec -it fastapi-backend python verify_fix_ready.py

# Test the crawl
sudo docker exec -it fastapi-backend python test_new_crawl.py
```

## What to Expect

### 1. After `verify_fix_ready.py`:

```
======================================================================
  ✅ ALL CHECKS PASSED - READY TO TEST!
======================================================================

You can now test the crawl:
  sudo docker exec -it fastapi-backend python test_new_crawl.py
```

### 2. After `test_new_crawl.py`:

```
1️⃣  Initiating crawl...
✅ Crawl initiated!

2️⃣  Checking crawl status...
✅ Status retrieved!
📊 Crawl:
   URL: https://example.com
   Status: STARTING (or IN_PROGRESS)
   KB ID: XXXXXXXXXX
```

## If You See Errors

### Error: "Collection not found"
```bash
# Check what collections exist
sudo docker exec -it fastapi-backend python -c "
import boto3, os
from dotenv import load_dotenv
load_dotenv('env')
aoss = boto3.client('opensearchserverless', region_name=os.getenv('AWS_REGION'))
for c in aoss.list_collections()['collectionSummaries']:
    print(f'{c[\"name\"]}: {c[\"id\"]} ({c[\"status\"]})')
"
```

### Error: "403 Forbidden"
This should NOT happen anymore with the fix. If you see it:
```bash
# Check the code was updated
sudo docker exec -it fastapi-backend grep -A 2 "Index will be created automatically" /app/rag_model/rag_website.py
```

Should show:
```python
print(f"   ℹ️  Index will be created automatically by Bedrock on first use")
print(f"   ℹ️  This avoids OpenSearch permission propagation delays")
```

### Error: "Knowledge Base creation failed"
```bash
# Check Bedrock role
sudo docker exec -it fastapi-backend python check_bedrock_role.py

# Check permissions
sudo docker exec -it fastapi-backend python check_current_permissions.py
```

## Success Criteria

✅ Crawl status is "STARTING" or "IN_PROGRESS" (not "FAILED")
✅ Knowledge Base ID is present
✅ No 403 errors in the output
✅ Message shows "Index will be created automatically by Bedrock"

## What Changed

**Before:**
- System tried to create OpenSearch index manually
- Got 403 errors due to permission propagation delays
- Crawls failed immediately

**After:**
- System skips manual index creation
- Bedrock creates index automatically (has immediate access)
- Crawls start successfully

## Monitor First Crawl

After starting a crawl, monitor it:

```bash
# Check status every 30 seconds
watch -n 30 'sudo docker exec -it fastapi-backend python -c "
import requests
r = requests.get(\"http://localhost:8000/tenants/999/websites/status\")
print(r.json())
"'
```

Or check logs:
```bash
sudo docker logs -f fastapi-backend
```

## Production Ready

Once the test crawl succeeds:
- ✅ System is ready for production
- ✅ All agents can create knowledge bases
- ✅ Crawls will work automatically
- ✅ No manual intervention needed

## Need Help?

Check these files:
- `OPENSEARCH_PERMISSION_FIX_SUMMARY.md` - Detailed explanation
- `DEPLOY_AND_TEST_FIX.md` - Full deployment guide
- `verify_fix_ready.py` - Verification script
- `test_kb_creation_direct.py` - Direct test (no API)

Or run diagnostics:
```bash
sudo docker exec -it fastapi-backend python check_bedrock_role.py
sudo docker exec -it fastapi-backend python check_current_permissions.py
```
