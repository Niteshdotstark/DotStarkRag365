# Testing Instructions for fb_verify_token Issue

## Quick Start - Run This First

Since you're using PostgreSQL, run this script on your server:

```bash
cd ChatBotBE/backend
python test_postgres_column.py
```

This will:
1. Show you the exact column definition in PostgreSQL
2. Show you the actual data stored for all tenants
3. Identify if tenant 7's token is truncated
4. Offer to fix the column length automatically

## What You'll See

The script will show output like:

```
Column Name               Data Type       Max Length   Nullable  
----------------------------------------------------------------------
fb_verify_token          varchar         1            YES       
```

If "Max Length" is 1 or any small number, that's your problem!

## Expected vs Actual

- **Expected**: `fb_verify_token` should be VARCHAR(255) or longer
- **Actual**: It's probably VARCHAR(1), which is why only "d" is stored

## How to Fix

The script will offer to fix it automatically. Just answer "yes" when prompted.

Or run manually:

```bash
python fix_column_length.py
```

## After Fixing

1. Restart your FastAPI app:
   ```bash
   # Stop the current process (Ctrl+C if running in terminal)
   # Or restart your Docker container
   docker-compose restart backend
   ```

2. Update tenant 7 through your admin UI:
   - Go to Organizations page
   - Edit tenant 7
   - Set fb_verify_token to: `chatbottoken@3420`
   - Save

3. Verify it worked:
   ```bash
   python test_postgres_column.py
   ```
   
   You should now see the full token stored.

4. Test webhook verification:
   - Try subscribing to the webhook again from Facebook
   - Check your logs - you should see "✅ Webhook verified" instead of "❌ Verification failed"

## Additional Testing Scripts

If you want to test other aspects:

### Check Database Configuration
```bash
python check_database.py
```

### Test Direct Database Access
```bash
python test_tenant_update.py
```

### Test API Endpoint
```bash
python test_api_update.py
```
(You'll need to login first and provide your access token)

## Still Having Issues?

If the column length is correct but you're still seeing "d":

1. Check if there's any frontend validation limiting input
2. Check browser network tab to see what's actually being sent
3. Enable SQLAlchemy query logging in `database.py`:
   ```python
   engine = create_engine(DATABASE_URL, echo=True)
   ```
4. Check for any Pydantic validators in `schemas.py`

## Quick Verification Query

You can also check directly in PostgreSQL:

```bash
psql -U postgres -d multi_tenant_admin
```

Then run:
```sql
SELECT id, name, fb_verify_token, LENGTH(fb_verify_token) 
FROM tenants 
WHERE id = 7;
```

Expected output:
```
 id | name | fb_verify_token    | length 
----+------+--------------------+--------
  7 | ...  | chatbottoken@3420  |     18
```

If you see length = 1, the column needs to be fixed.
