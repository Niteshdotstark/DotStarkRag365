# E2E Test Status

## Current Issue
The e2e test for website crawling is failing due to AWS OpenSearch Serverless authentication (401 error).

## What We Fixed
1. ✅ Syntax error in `rag_website.py` (line 575 - unterminated string)
2. ✅ Installed `opensearch-py` package in venv
3. ✅ Updated Bedrock IAM role trust policy and permissions
4. ✅ Recreated OpenSearch data access policy with correct principals
5. ✅ Increased test timeout from 30s to 180s
6. ✅ FastAPI server is running successfully

## Remaining Issue
**OpenSearch Serverless 401 Authentication Error**

When Bedrock tries to create a Knowledge Base, it fails with:
```
ValidationException: The knowledge base storage configuration provided is invalid... 
Request failed: [http_exception] server returned 401
```

## Root Cause
The Bedrock service role (`BedrockKnowledgeBaseRole`) cannot authenticate to the OpenSearch Serverless collection, even though:
- The data access policy includes the role ARN
- The role has `aoss:APIAccessAll` permission
- We waited 60+ seconds for policy propagation

## Possible Solutions

### Option 1: Wait Longer for Policy Propagation
AWS policies can take up to 5-10 minutes to fully propagate. Try:
```bash
# Wait 5 minutes, then run test
Start-Sleep -Seconds 300
./venv/Scripts/python test_dotstark_e2e.py
```

### Option 2: Recreate the OpenSearch Collection
The collection might have stale policies. Delete and recreate:
```python
# In AWS Console or CLI:
# 1. Delete knowledge bases using this collection
# 2. Delete the collection: kb-collection-1
# 3. Run the test again (it will create a fresh collection)
```

### Option 3: Use AWS Console to Verify
1. Go to AWS OpenSearch Serverless console
2. Find collection `kb-collection-1`
3. Check "Data access policies" tab
4. Verify `BedrockKnowledgeBaseRole` is listed
5. Check "Network policies" - ensure it allows access

### Option 4: Manual Knowledge Base Creation
Create the knowledge base manually in AWS Bedrock console to verify permissions work, then compare with our code.

## Test Files Created
- `check_tenant.py` - Verify tenant exists in database
- `fix_bedrock_role.py` - Update IAM role permissions
- `fix_opensearch_access.py` - Update OpenSearch data access policy  
- `create_opensearch_index.py` - Manually create vector index (currently fails with 401)

## Next Steps
1. Wait 5-10 minutes for AWS policies to fully propagate
2. Run the test again
3. If still failing, delete and recreate the OpenSearch collection
4. Consider using AWS Bedrock's managed OpenSearch option instead of serverless

## Test Command
```bash
cd ChatBotBE/backend
./venv/Scripts/python test_dotstark_e2e.py
```

## Server Status
FastAPI server is running on http://localhost:8000
- Started with: `./venv/Scripts/uvicorn main:app --reload`
- Process ID available in terminal 2
