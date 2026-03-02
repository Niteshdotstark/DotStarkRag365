# Facebook Webhook & OAuth Token Issues - Complete Fix Guide

## Your Issues

You're experiencing TWO related problems:

### 1. Webhook Verification Failing
```
❌ Verification failed: mode=subscribe, token=chatbottoken@3420, expected=d
```
The `fb_verify_token` is stored as "d" instead of "chatbottoken@3420"

### 2. OAuth Access Token Error
```
Invalid OAuth access token - Cannot parse access token
OAuthException, code 190
```
The `fb_access_token` is truncated and invalid

## Root Cause

Your PostgreSQL database columns are too short:
- `fb_verify_token` is probably VARCHAR(1) → needs VARCHAR(255)
- `fb_access_token` is probably VARCHAR(1) → needs VARCHAR(500)
- `insta_access_token` is probably VARCHAR(1) → needs VARCHAR(500)

This causes all tokens to be truncated when saved.

## Complete Fix (5 Minutes)

### Step 1: SSH to Your Server
```bash
ssh ubuntu@your-server-ip
```

### Step 2: Run the Diagnostic Tool
```bash
cd /home/ubuntu/ChatBotBE/backend
python diagnose_and_fix.py
```

This will:
- ✓ Check your database configuration
- ✓ Identify all truncated columns
- ✓ Show you exactly what's wrong
- ✓ Offer to fix it automatically

When it asks "Apply fix now? (yes/no):", type `yes`

### Step 3: Restart Your Backend
```bash
cd /home/ubuntu/ChatBotBE
docker-compose restart backend
```

Wait 10 seconds for the container to restart.

### Step 4: Update Tokens in Admin UI

1. Open your admin UI in browser
2. Go to Organizations page
3. Click Edit on tenant 7
4. Update these fields with COMPLETE tokens:
   - **FB/INSTA VERIFY TOKEN**: `chatbottoken@3420`
   - **FACEBOOK PAGE ACCESS TOKEN**: [Your full token from Facebook]
   - **INSTAGRAM ACCESS TOKEN**: [Your full token from Instagram]
5. Click Save

### Step 5: Verify the Fix
```bash
cd /home/ubuntu/ChatBotBE/backend
python diagnose_and_fix.py
```

You should now see:
- ✅ No issues found!
- Token lengths are correct (200+ chars for access tokens)

### Step 6: Test

1. **Test Webhook Verification**:
   - Go to Facebook Developer Console
   - Try subscribing to webhook again
   - Should see: ✅ Webhook verified

2. **Test Messaging**:
   - Send a message to your Facebook page
   - Should receive a response
   - No OAuth errors in logs

## Quick Reference Commands

```bash
# Check if tokens are truncated
python check_access_tokens.py

# Fix database columns
python diagnose_and_fix.py

# Restart backend
docker-compose restart backend

# View logs
docker logs -f fastapi-backend
```

## How to Get Facebook Access Token

1. Go to https://developers.facebook.com/
2. Select your app
3. Go to Messenger → Settings
4. Under "Access Tokens", select your page
5. Click "Generate Token"
6. Copy the ENTIRE token (it's 200-300 characters!)
7. Paste in your admin UI

**Important**: Copy the complete token, not just part of it!

## Troubleshooting

### Still seeing "expected=d"?
- Database columns not fixed yet
- Run `python diagnose_and_fix.py` and answer "yes"

### Still seeing OAuth error?
- Access token not updated after fixing columns
- Generate a new token from Facebook
- Make sure you copy the COMPLETE token
- Update in admin UI

### Token expires?
- Facebook tokens can expire
- Generate a new one from Facebook Developer Console
- Update in your admin UI

## Files Created for You

- `diagnose_and_fix.py` - Main diagnostic and fix tool
- `check_access_tokens.py` - Check token lengths
- `test_postgres_column.py` - PostgreSQL-specific checks
- `FIX_FACEBOOK_TOKEN_ERROR.md` - Detailed OAuth error guide
- `TESTING_INSTRUCTIONS.md` - Step-by-step testing guide

## Need Help?

Run the diagnostic tool and share the output:
```bash
python diagnose_and_fix.py > debug_output.txt 2>&1
cat debug_output.txt
```

## Summary

The fix is simple:
1. Run `python diagnose_and_fix.py` → answer "yes"
2. Restart backend: `docker-compose restart backend`
3. Update tokens in admin UI with COMPLETE values
4. Test webhook and messaging

Both issues will be resolved! 🎉
