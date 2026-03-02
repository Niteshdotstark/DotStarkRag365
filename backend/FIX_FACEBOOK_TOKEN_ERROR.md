# Fix: Invalid OAuth Access Token Error

## Error Message
```
Invalid OAuth access token - Cannot parse access token
OAuthException, code 190
```

## Root Cause
Your Facebook access token is being truncated in the database. Facebook access tokens are typically 200-300 characters long, but your database column is too short (probably VARCHAR(1) or similar).

## Quick Fix

### Step 1: Check the Issue
Run this on your server:
```bash
cd /home/ubuntu/ChatBotBE/backend
python check_access_tokens.py
```

This will show you:
- Current column length for `fb_access_token`
- Actual token length stored in database
- Whether tenant 7's token is truncated

### Step 2: Fix the Database Schema
Run the comprehensive fix script:
```bash
python diagnose_and_fix.py
```

Answer "yes" when it asks to fix the columns. This will:
- Change `fb_verify_token` to VARCHAR(255)
- Change `fb_access_token` to VARCHAR(500)
- Change `insta_access_token` to VARCHAR(500)
- Change `telegram_bot_token` to VARCHAR(255)

### Step 3: Restart Your Application
```bash
cd /home/ubuntu/ChatBotBE
docker-compose restart backend
```

Or if not using docker-compose:
```bash
docker restart fastapi-backend
```

### Step 4: Update the Access Token

1. Go to your admin UI (the form you showed in the screenshot)
2. Edit tenant 7 (Organizations page)
3. Re-enter the FULL Facebook Page Access Token
4. Make sure you copy the COMPLETE token from Facebook
5. Save

### Step 5: Verify the Fix
```bash
python check_access_tokens.py
```

You should now see:
- `fb_access_token` length: 200+ characters (not just a few)
- No truncation warnings

### Step 6: Test Webhook
Send a test message to your Facebook page. You should see:
- ✅ Message received
- ✅ Response generated
- ✅ Reply sent successfully

Instead of the OAuth error.

## How to Get a Valid Facebook Access Token

If you need to generate a new token:

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Select your app
3. Go to "Messenger" → "Settings"
4. Under "Access Tokens", select your page
5. Click "Generate Token"
6. Copy the ENTIRE token (it's very long!)
7. Paste it in your admin UI

**Important**: Make sure you copy the complete token. It should look like:
```
EAAKgyth24vEBPCOP16Fw4cnnGW0t9N6qoeSCtp5VlWMzSXlnsZCEUM5YWtFzQqCq2BZChkF3FKD6tszoybJ21KbpDecvga0Xr0WGlXMChSICVB9KDfHFmnT0rrUVs3DkOJlKtk5OZCq55zkls1FfSpJ0vRnnHGVAln5Y1bRqnNX3u5ZCqISAeil3X4Yc6N2XnmuJAwZDZD
```
(This is just an example - yours will be different)

## Verification Checklist

- [ ] Database columns are VARCHAR(500) for access tokens
- [ ] `check_access_tokens.py` shows token length > 200 chars
- [ ] Backend container restarted
- [ ] Token updated in admin UI
- [ ] Test message sent successfully
- [ ] No OAuth errors in logs

## Still Getting Errors?

If you still see OAuth errors after fixing:

1. **Token Expired**: Facebook tokens can expire. Generate a new one.
2. **Wrong Token Type**: Make sure you're using a "Page Access Token", not a "User Access Token"
3. **Permissions**: Ensure the token has `pages_messaging` permission
4. **App Review**: Some features require Facebook app review

## Check Token Validity

You can test if your token is valid:
```bash
curl "https://graph.facebook.com/v19.0/me?access_token=YOUR_TOKEN_HERE"
```

If valid, you'll see page information. If invalid, you'll see an error.

## Related Issues

This same problem affects:
- `fb_verify_token` (webhook verification)
- `insta_access_token` (Instagram messaging)
- `telegram_bot_token` (Telegram bot)

The `diagnose_and_fix.py` script fixes all of them at once.
