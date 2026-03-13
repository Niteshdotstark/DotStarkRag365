# Deploy New Collection Fix - Instructions

## What This Does

1. Updates `rag_website.py` with hardcoded fallback for new collection
2. Updates database with new collection ID `3wwawnad009sxxxdsnni`
3. Restarts Docker container
4. Verifies everything is working

## Quick Deploy (One Command)

```bash
cd ChatBotBE/backend
chmod +x deploy_and_update_db.sh
./deploy_and_update_db.sh
```

This will:
- Copy updated files to server
- Run database update script on server
- Restart Docker container
- Show logs

## Manual Deploy (Step by Step)

If the automated script fails, do it manually:

### Step 1: Copy Files

```bash
# Copy updated code
scp rag_model/rag_website.py ubuntu@ip-172-31-45-238:~/DotStarkRag365/backend/rag_model/

# Copy database update script
scp update_db_collection.py ubuntu@ip-172-31-45-238:~/DotStarkRag365/backend/
```

### Step 2: Update Database

```bash
# SSH to server
ssh ubuntu@ip-172-31-45-238

# Go to backend directory
cd ~/DotStarkRag365/backend

# Run database update
python update_db_collection.py
```

Expected output:
```
💾 UPDATE DATABASE WITH NEW COLLECTION
Collection ID: 3wwawnad009sxxxdsnni
Collection Name: kb-collection-321
Agent ID: 132

1️⃣  Checking agent...
   ✅ Agent 132 exists

2️⃣  Updating collection...
   📝 Updating existing record...
      Old Collection ID: nklj91pvx9jgqeidffll
      New Collection ID: 3wwawnad009sxxxdsnni
   ✅ Record updated

3️⃣  Verifying...
   ✅ Verification successful!

✅ DATABASE UPDATE COMPLETE
```

### Step 3: Restart Container

```bash
# Still on server
cd ~/DotStarkRag365/backend
sudo docker-compose restart
```

### Step 4: Test

```bash
# Test a crawl
curl -X POST "http://YOUR_SERVER_IP:8000/api/crawl/start" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 532,
    "website_url": "https://vyauma.com/",
    "max_pages": 1
  }'

# Check logs
sudo docker logs -f fastapi-backend
```

## Expected Logs (Success)

```
🎯 DEMO MODE: Using shared collection (agent_id 132) for request from agent 532
✅ Reusing existing OpenSearch collection for agent 132
   Collection ID: 3wwawnad009sxxxdsnni
   Collection Name: kb-collection-321

🧠 Creating new Bedrock Knowledge Base for agent 532
🔐 Ensuring data access policy exists for collection...
   ℹ️  Using shared collection policy: kb-policy-132 (collection owner: agent 132)
   ✅ Data access policy already exists: kb-policy-132
✅ Knowledge Base created: kb-XXXXXXXXXX
✅ Knowledge Base is ACTIVE
```

## Troubleshooting

### Issue: Database update fails

**Error:** `ImportError: No module named 'database'`

**Solution:** Make sure you're in the correct directory:
```bash
cd ~/DotStarkRag365/backend
python update_db_collection.py
```

### Issue: Permission denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:** Check file permissions:
```bash
chmod +x deploy_and_update_db.sh
```

### Issue: Still getting 403 errors

**Cause:** Policy needs time to propagate or database not updated.

**Solution:**
```bash
# On server, verify database was updated
ssh ubuntu@ip-172-31-45-238
cd ~/DotStarkRag365/backend
python -c "
from database import SessionLocal
from models import AgentCollection
db = SessionLocal()
col = db.query(AgentCollection).filter_by(agent_id=132).first()
if col:
    print(f'Collection ID: {col.collection_id}')
else:
    print('No collection found!')
"
```

Should show: `Collection ID: 3wwawnad009sxxxdsnni`

If not, run `python update_db_collection.py` again.

## Files Changed

1. **rag_model/rag_website.py** - Added hardcoded fallback for collection
2. **Database** - Updated AgentCollection record for agent 132

## Summary

The deployment script does everything automatically:
1. ✅ Copies updated code
2. ✅ Updates database
3. ✅ Restarts container
4. ✅ Shows logs

Just run: `./deploy_and_update_db.sh`

Then test a crawl - should work without 403 errors!
