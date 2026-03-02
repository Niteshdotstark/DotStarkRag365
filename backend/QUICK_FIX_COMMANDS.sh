#!/bin/bash
# Quick fix commands for Facebook OAuth token error

echo "=========================================="
echo "Facebook OAuth Token Error - Quick Fix"
echo "=========================================="
echo ""

# Navigate to backend directory
cd /home/ubuntu/ChatBotBE/backend

echo "Step 1: Checking access tokens..."
python check_access_tokens.py

echo ""
echo "Step 2: Running diagnostic and fix..."
python diagnose_and_fix.py

echo ""
echo "Step 3: Restarting backend container..."
cd /home/ubuntu/ChatBotBE
docker-compose restart backend

echo ""
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to your admin UI"
echo "2. Edit tenant 7 (Organizations page)"
echo "3. Re-enter the FULL Facebook access token"
echo "4. Save"
echo "5. Test by sending a message to your Facebook page"
echo ""
