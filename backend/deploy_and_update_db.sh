#!/bin/bash

# Complete deployment: Update code + Update database

echo "======================================================================="
echo "  🚀 DEPLOY NEW COLLECTION FIX"
echo "======================================================================="
echo ""

SERVER="ubuntu@ip-172-31-45-238"
SERVER_PATH="~/DotStarkRag365/backend"

echo "Server: $SERVER"
echo "Path: $SERVER_PATH"
echo ""

# Step 1: Copy updated files
echo "1️⃣  Copying files to server..."
echo ""

echo "   📄 Copying rag_website.py..."
scp rag_model/rag_website.py $SERVER:$SERVER_PATH/rag_model/
if [ $? -ne 0 ]; then
    echo "   ❌ Failed to copy rag_website.py"
    exit 1
fi

echo "   📄 Copying update_db_collection.py..."
scp update_db_collection.py $SERVER:$SERVER_PATH/
if [ $? -ne 0 ]; then
    echo "   ❌ Failed to copy update_db_collection.py"
    exit 1
fi

echo "   ✅ Files copied"
echo ""

# Step 2: Update database on server
echo "2️⃣  Updating database on server..."
echo ""
ssh $SERVER "cd $SERVER_PATH && python update_db_collection.py"
if [ $? -ne 0 ]; then
    echo "   ❌ Failed to update database"
    echo ""
    echo "   Troubleshooting:"
    echo "   - Check if DATABASE_URL is set in .env"
    echo "   - Check if database is accessible"
    echo "   - Try running manually on server:"
    echo "     ssh $SERVER"
    echo "     cd $SERVER_PATH"
    echo "     python update_db_collection.py"
    exit 1
fi

echo ""

# Step 3: Restart Docker container
echo "3️⃣  Restarting Docker container..."
ssh $SERVER "cd $SERVER_PATH && sudo docker-compose restart"
if [ $? -eq 0 ]; then
    echo "   ✅ Container restarted"
else
    echo "   ❌ Failed to restart container"
    exit 1
fi

echo ""

# Step 4: Wait for container
echo "4️⃣  Waiting for container to be ready (15 seconds)..."
sleep 15
echo "   ✅ Ready"

echo ""

# Step 5: Check logs
echo "5️⃣  Checking logs..."
echo ""
ssh $SERVER "sudo docker logs --tail 30 fastapi-backend"

echo ""
echo "======================================================================="
echo "  ✅ DEPLOYMENT COMPLETE"
echo "======================================================================="
echo ""
echo "What was done:"
echo "  ✅ Updated rag_website.py with new collection ID"
echo "  ✅ Updated database with new collection record"
echo "  ✅ Restarted Docker container"
echo ""
echo "Next steps:"
echo "  1. Test a crawl:"
echo ""
echo "     curl -X POST \"http://YOUR_SERVER_IP:8000/api/crawl/start\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"agent_id\": 532, \"website_url\": \"https://vyauma.com/\", \"max_pages\": 1}'"
echo ""
echo "  2. Monitor logs:"
echo ""
echo "     ssh $SERVER \"sudo docker logs -f fastapi-backend\""
echo ""
echo "  3. Expected result:"
echo "     ✅ Using hardcoded collection for agent 132"
echo "     ✅ Collection ID: 3wwawnad009sxxxdsnni"
echo "     ✅ Knowledge Base created successfully"
echo "     ✅ NO 403 errors!"
echo ""
