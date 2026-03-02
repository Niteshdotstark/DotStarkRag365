# Quick Fix Guide for Website Crawling Issues

## 🚀 Quick Start (If Nothing Works)

Run these commands in order:

```bash
# 1. Check your setup
cd ChatBotBE/backend
python diagnose_crawling.py

# 2. If IAM role is missing, create it
python create_iam_role.py

# 3. Start the server
uvicorn main:app --reload

# 4. In another terminal, test crawling
python test_website_crawling.py
```

## 🔍 Most Common Issues

### 1. URL Not Crawling (Most Common)

**Check these first:**

✅ **URL Format**
- Must start with `https://` or `http://`
- ❌ Wrong: `example.com` or `www.example.com`
- ✅ Correct: `https://example.com`

✅ **Website Accessibility**
- Can you access the website in your browser?
- Is it behind a login/paywall?
- Does it block bots (check robots.txt)?

✅ **AWS Region**
- Your env file shows: `AWS_REGION=ap-south-1`
- Bedrock is available in this region ✅

### 2. AWS Permissions Error

**Quick Fix:**
```bash
# Run this to create the IAM role
python create_iam_role.py
```

**Manual Fix:**
1. Go to AWS IAM Console
2. Find your user
3. Add these policies:
   - `AmazonBedrockFullAccess`
   - `AmazonOpenSearchServiceFullAccess`
4. Create role using `create_iam_role.py`

### 3. Crawl Status Stuck

**If status is stuck at "STARTING" or "IN_PROGRESS":**

```bash
# Check status via API
curl "http://localhost:8000/tenants/1/websites/crawl/{website_id}/status"
```

**Possible causes:**
- Website is too large (reduce max_pages to 10 for testing)
- Website blocks AWS crawlers
- AWS service is slow (can take 5-10 minutes)

**Solution:**
- Wait longer (up to 10 minutes)
- Try a smaller, simpler website first
- Check AWS Bedrock console for errors

### 4. Chat Returns No Answer

**Checklist:**
- [ ] Is crawl status "COMPLETE"? (not "IN_PROGRESS")
- [ ] Did it actually crawl pages? (check pages_crawled > 0)
- [ ] Is your question related to the website content?

**Test with this:**
```bash
# First check status
curl "http://localhost:8000/tenants/1/websites/crawl/{website_id}/status"

# If COMPLETE, try chatting
curl -X POST "http://localhost:8000/tenants/1/websites/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://docs.python.org/3/tutorial/",
    "question": "What is Python?"
  }'
```

## 🛠️ Step-by-Step Debugging

### Step 1: Verify Environment
```bash
# Check if env file has all required variables
cat env | grep -E "AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_REGION|BEDROCK_ROLE_ARN"
```

Should show:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
BEDROCK_ROLE_ARN=arn:aws:iam::...
```

### Step 2: Test AWS Connection
```bash
python diagnose_crawling.py
```

Look for:
- ✅ All checks should pass
- ❌ If any fail, follow the suggested solutions

### Step 3: Test with Simple Website
```python
# Edit test_website_crawling.py
TEST_WEBSITE_URL = "https://docs.python.org/3/tutorial/"
MAX_PAGES = 10  # Start small!
```

### Step 4: Monitor Logs
```bash
# Start server with verbose logging
uvicorn main:app --reload --log-level debug
```

Watch for:
- "🚀 Initiating website crawl" - Crawl started
- "✅ Collection is ACTIVE" - OpenSearch ready
- "✅ Knowledge Base created" - KB ready
- "✅ Ingestion job started" - Crawling started

## 📋 Pre-Flight Checklist

Before starting a crawl, verify:

- [ ] FastAPI server is running (`uvicorn main:app --reload`)
- [ ] Database is running and accessible
- [ ] Tenant exists in database (tenant_id=1)
- [ ] AWS credentials are in env file
- [ ] BEDROCK_ROLE_ARN is set in env file
- [ ] URL starts with https:// or http://
- [ ] Website is publicly accessible

## 🎯 Test Websites (Known to Work)

Use these for testing:

1. **Python Docs** (Recommended for first test)
   ```json
   {
     "url": "https://docs.python.org/3/tutorial/",
     "max_pages": 10,
     "crawl_scope": "HOST"
   }
   ```

2. **Simple Blog**
   ```json
   {
     "url": "https://example.com",
     "max_pages": 5,
     "crawl_scope": "HOST"
   }
   ```

## 🚨 Error Messages and Solutions

### "AWS configuration error: AWS_ACCOUNT_ID is not set"
**Solution:** Add to env file:
```
AWS_ACCOUNT_ID=your_account_id_here
```

### "AWS configuration error: BEDROCK_ROLE_ARN is not set"
**Solution:** Run `python create_iam_role.py` then copy the ARN to env file

### "Invalid URL format"
**Solution:** Add `https://` to the beginning of your URL

### "Tenant not found"
**Solution:** Create a tenant first or use existing tenant_id

### "Website has not been crawled yet"
**Solution:** Crawl the website first using POST /tenants/{id}/websites/crawl

### "Crawling is in progress"
**Solution:** Wait for crawl to complete (check status endpoint)

### "AccessDeniedException"
**Solution:** Add AWS policies to your IAM user (see section 2 above)

## 💡 Pro Tips

1. **Always test with small websites first** (max_pages=10)
2. **Wait for COMPLETE status** before trying to chat
3. **Check pages_crawled > 0** to ensure content was indexed
4. **Use HOST scope** for most websites (not SUBDOMAINS)
5. **Monitor AWS costs** - Bedrock charges per request
6. **Run diagnose_crawling.py** when in doubt

## 📞 Still Not Working?

1. Run diagnostic: `python diagnose_crawling.py`
2. Check server logs for error messages
3. Verify website is accessible: `curl -I https://your-website.com`
4. Check AWS Bedrock console for ingestion job status
5. Try a different website (use Python docs for testing)
6. Reduce max_pages to 5 for faster testing

## ✅ Success Indicators

You'll know it's working when:

1. Diagnostic script shows all ✅ checks passed
2. Crawl initiation returns status 202 with website_id
3. Status endpoint shows "COMPLETE" with pages_crawled > 0
4. Chat endpoint returns an answer with citations
5. No error messages in server logs

## 🎉 Next Steps After Success

1. Test with your actual website
2. Increase max_pages gradually (10 → 50 → 100)
3. Integrate with your frontend
4. Add error handling and retry logic
5. Monitor AWS costs and usage
6. Set up alerts for failed crawls
