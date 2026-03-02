# Website Crawling Troubleshooting Guide

## Issues Fixed

### 1. Incomplete Query Function
**Problem**: The `query_website_knowledge_base` function had an incomplete prompt template string.
**Fix**: Completed the prompt template string with proper closing quote.

### 2. Missing URL Validation
**Problem**: No validation of website URL format before attempting to crawl.
**Fix**: Added regex validation to ensure URLs are properly formatted with http:// or https://.

### 3. Missing AWS Configuration Validation
**Problem**: No check if AWS credentials and configuration are valid before starting operations.
**Fix**: Added `validate_aws_configuration()` function that checks credentials before crawling.

### 4. Poor Error Messages
**Problem**: Generic error messages made it hard to diagnose issues.
**Fix**: Added detailed error messages and validation for all parameters.

## Common Issues and Solutions

### Issue 1: "AWS credentials are invalid"
**Symptoms**: Error when trying to initiate crawl
**Solutions**:
1. Check your `env` file has correct AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_here
   AWS_REGION=ap-south-1
   AWS_ACCOUNT_ID=your_account_id
   ```
2. Run diagnostic: `python diagnose_crawling.py`

### Issue 2: "AccessDeniedException" from AWS
**Symptoms**: Permission denied errors
**Solutions**:
1. Ensure your IAM user has these policies:
   - AmazonBedrockFullAccess
   - AmazonOpenSearchServiceFullAccess
   - Custom policy for bedrock-agent actions
2. Run: `python create_iam_role.py` to create the Bedrock role
3. Verify role ARN in env file matches the created role

### Issue 3: "Knowledge base not found" or "Collection not found"
**Symptoms**: Can't query after crawling
**Solutions**:
1. Check crawl status: `GET /tenants/{tenant_id}/websites/crawl/{website_id}/status`
2. Wait for status to be "COMPLETE" before querying
3. Check AWS console for OpenSearch collection and Knowledge Base

### Issue 4: Crawling starts but never completes
**Symptoms**: Status stuck at "STARTING" or "IN_PROGRESS"
**Solutions**:
1. Check the website URL is accessible from AWS (not behind firewall)
2. Verify the website allows crawling (check robots.txt)
3. Check AWS Bedrock console for ingestion job errors
4. Reduce max_pages to test with smaller crawl

### Issue 5: "Invalid URL format"
**Symptoms**: Error when submitting crawl request
**Solutions**:
1. Ensure URL starts with http:// or https://
2. Examples of valid URLs:
   - ✅ https://example.com
   - ✅ https://docs.python.org/3/tutorial/
   - ❌ example.com (missing protocol)
   - ❌ www.example.com (missing protocol)

### Issue 6: Chat returns empty or irrelevant answers
**Symptoms**: Query works but answer is not helpful
**Solutions**:
1. Check if crawl actually indexed pages (check pages_crawled in status)
2. Increase num_results parameter (default is 12)
3. Try different questions or rephrase
4. Check if the website content is actually relevant to your question

## Diagnostic Steps

### Step 1: Run the diagnostic script
```bash
cd ChatBotBE/backend
python diagnose_crawling.py
```

This will check:
- Environment variables
- AWS credentials
- Bedrock access
- OpenSearch Serverless access
- IAM role configuration
- Database connection

### Step 2: Test with a simple website
Use a small, well-structured website for testing:
```python
TEST_WEBSITE_URL = "https://docs.python.org/3/tutorial/"
MAX_PAGES = 10
```

### Step 3: Monitor the crawl
```bash
# Start the server
uvicorn main:app --reload

# In another terminal, run the test
python test_website_crawling.py
```

### Step 4: Check AWS Console
1. Go to AWS Bedrock console
2. Navigate to Knowledge Bases
3. Find your knowledge base (kb-{tenant_id}-{website_id})
4. Check the data source and ingestion job status

## API Usage Examples

### 1. Initiate Crawl
```bash
curl -X POST "http://localhost:8000/tenants/1/websites/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/tutorial/",
    "max_pages": 10,
    "crawl_scope": "HOST"
  }'
```

### 2. Check Status
```bash
curl "http://localhost:8000/tenants/1/websites/crawl/{website_id}/status"
```

### 3. Query Website
```bash
curl -X POST "http://localhost:8000/tenants/1/websites/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://docs.python.org/3/tutorial/",
    "question": "What is Python?"
  }'
```

## Configuration Parameters

### Crawl Scope Options
- `DEFAULT`: Crawls only the seed URL
- `HOST`: Crawls all pages on the same host (recommended)
- `SUBDOMAINS`: Crawls all subdomains of the host

### Max Pages
- Minimum: 1
- Maximum: 25,000
- Recommended for testing: 10-50
- Recommended for production: 100-1000

### Chunking Configuration
- Strategy: FIXED_SIZE
- Max tokens per chunk: 300
- Overlap percentage: 20%

## Performance Tips

1. **Start small**: Test with max_pages=10 before scaling up
2. **Use HOST scope**: More efficient than SUBDOMAINS for most cases
3. **Monitor costs**: AWS Bedrock charges for:
   - Embedding generation
   - OpenSearch storage
   - Query processing
4. **Cache results**: Store frequently asked questions and answers
5. **Batch operations**: Crawl multiple websites during off-peak hours

## Debugging Checklist

- [ ] Environment variables are set correctly
- [ ] AWS credentials are valid
- [ ] IAM role exists and has correct permissions
- [ ] Database is running and accessible
- [ ] FastAPI server is running
- [ ] Website URL is valid and accessible
- [ ] Tenant exists in database
- [ ] Crawl status is "COMPLETE" before querying
- [ ] OpenSearch collection is ACTIVE
- [ ] Knowledge base exists in AWS

## Getting Help

If you're still experiencing issues:

1. Check the FastAPI server logs for detailed error messages
2. Run `python diagnose_crawling.py` and share the output
3. Check AWS CloudWatch logs for Bedrock errors
4. Verify your AWS region supports Bedrock (ap-south-1 does)
5. Test with the provided test script: `python test_website_crawling.py`

## Next Steps

Once crawling is working:

1. Integrate with your frontend
2. Add user authentication and authorization
3. Implement rate limiting
4. Add caching for common queries
5. Monitor AWS costs
6. Set up alerts for failed crawls
7. Implement automatic retry logic
8. Add support for multiple websites per tenant
