# Debugging fb_verify_token Truncation Issue

## Problem
The `fb_verify_token` for tenant 7 is being stored as "d" instead of the full value "chatbottoken@3420".

## Root Cause
The database column `fb_verify_token` is likely too short (possibly VARCHAR(1) or similar), causing the value to be truncated.

## Testing Steps

### Step 1: Test Database Column
Run this on your server to check what's happening at the database level:

```bash
cd ChatBotBE/backend
python test_tenant_update.py
```

This will show you:
- Current value in the database
- Column definition and type
- Test if updating works
- Whether truncation is happening

### Step 2: Test API Update
Run this to test the full API flow:

```bash
cd ChatBotBE/backend
python test_api_update.py
```

You'll need to:
1. Login to your application first
2. Copy your access token
3. Paste it when prompted

This will show you:
- What data is sent to the API
- What data is returned from the API
- What data is actually stored in the database

### Step 3: Check Database Directly
If you have direct database access, run these queries:

**For SQLite:**
```sql
-- Check column definition
PRAGMA table_info(tenants);

-- Check current value
SELECT id, name, fb_verify_token, length(fb_verify_token) as token_length 
FROM tenants 
WHERE id = 7;
```

**For PostgreSQL:**
```sql
-- Check column definition
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'tenants' AND column_name = 'fb_verify_token';

-- Check current value
SELECT id, name, fb_verify_token, length(fb_verify_token) as token_length 
FROM tenants 
WHERE id = 7;
```

**For MySQL:**
```sql
-- Check column definition
DESCRIBE tenants;

-- Check current value
SELECT id, name, fb_verify_token, LENGTH(fb_verify_token) as token_length 
FROM tenants 
WHERE id = 7;
```

## Fixing the Issue

### Option 1: Run the Fix Script (Recommended)
```bash
cd ChatBotBE/backend
python fix_column_length.py
```

This will automatically detect your database type and fix the column length.

### Option 2: Manual Database Fix

**For SQLite:**
SQLite doesn't support ALTER COLUMN, so you need to recreate the table:
```sql
-- Backup
CREATE TABLE tenants_backup AS SELECT * FROM tenants;

-- Drop and recreate
DROP TABLE tenants;
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    fb_url VARCHAR(500),
    insta_url VARCHAR(500),
    fb_verify_token VARCHAR(255),
    fb_access_token VARCHAR(500),
    insta_access_token VARCHAR(500),
    telegram_bot_token VARCHAR(255),
    telegram_chat_id VARCHAR(255),
    created_at TIMESTAMP,
    creator_id INTEGER NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- Restore data
INSERT INTO tenants SELECT * FROM tenants_backup;
DROP TABLE tenants_backup;
```

**For PostgreSQL:**
```sql
ALTER TABLE tenants ALTER COLUMN fb_verify_token TYPE VARCHAR(255);
ALTER TABLE tenants ALTER COLUMN fb_access_token TYPE VARCHAR(500);
ALTER TABLE tenants ALTER COLUMN insta_access_token TYPE VARCHAR(500);
ALTER TABLE tenants ALTER COLUMN telegram_bot_token TYPE VARCHAR(255);
```

**For MySQL:**
```sql
ALTER TABLE tenants MODIFY COLUMN fb_verify_token VARCHAR(255);
ALTER TABLE tenants MODIFY COLUMN fb_access_token VARCHAR(500);
ALTER TABLE tenants MODIFY COLUMN insta_access_token VARCHAR(500);
ALTER TABLE tenants MODIFY COLUMN telegram_bot_token VARCHAR(255);
```

### Option 3: Recreate Database (Development Only)
If you're in development and don't need to preserve data:

```bash
# Backup your database file first!
# Then delete it and restart your app
rm your_database.db  # or whatever your database file is named
# Restart your FastAPI app - it will recreate the database with correct schema
```

## After Fixing

1. Restart your FastAPI application
2. Update tenant 7's fb_verify_token through your admin UI
3. Verify the token is stored correctly:
   ```bash
   python test_tenant_update.py
   ```
4. Test the webhook verification again

## Verification Checklist

- [ ] Database column is VARCHAR(255) or longer
- [ ] Test script shows full token is stored
- [ ] API returns full token after update
- [ ] Webhook verification succeeds (no more "expected=d" error)

## Additional Debugging

If the issue persists after fixing the column:

1. Check if there's any middleware or validation truncating the value
2. Check if there's a Pydantic validator on the field
3. Check nginx/proxy configuration for request body size limits
4. Enable SQLAlchemy echo to see actual SQL queries:
   ```python
   # In database.py
   engine = create_engine(DATABASE_URL, echo=True)
   ```

## Need More Help?

Run all three test scripts and share the output:
```bash
python test_tenant_update.py > debug_output.txt 2>&1
python test_api_update.py >> debug_output.txt 2>&1
```
