# Website Crawling Feature - Implementation Complete ✅

## Overview

The dynamic website crawling feature has been successfully implemented using AWS Bedrock Knowledge Bases with Web Crawler data source. This feature enables deep crawling of entire websites with automatic content extraction, embedding generation, and semantic search capabilities.

## What Was Implemented

### 1. Database Layer ✅
- **New Models:**
  - `TenantCollection`: Stores OpenSearch Serverless collection info per tenant
  - `WebsiteCrawl`: Tracks website crawling operations and Bedrock resources
  
- **Schema Updates:**
  - Added relationships to `Tenant` model
  - Automatic table creation on server startup

### 2. AWS Integration Layer ✅
- **New Module:** `rag_model/rag_website.py`
- **Functions:**
  - `create_or_get_opensearch_collection()`: Creates/reuses OpenSearch collections
  - `create_knowledge_base()`: Creates Bedrock Knowledge Bases
  - `create_data_source_and_start_crawl()`: Configures Web Crawler and starts ingestion
  - `check_ingestion_status()`: Monitors crawling progress
  - `query_website_knowledge_base()`: Queries using RetrieveAndGenerate API

### 3. API Endpoints ✅
- **POST `/tenants/{tenant_id}/websites/crawl`**
  - Initiates website crawling
  - Returns immediately with status "STARTING"
  - Crawling happens asynchronously in AWS

- **GET `/tenants/{tenant_id}/websites/crawl/{website_id}/status`**
  - Checks crawl status
  - Returns cached data for COMPLETE/FAILED
  - Queries AWS for STARTING/IN_PROGRESS

- **POST `/tenants/{tenant_id}/websites/chat`**
  - Asks questions about crawled websites
  - Uses semantic search + LLM
  - Returns answer with source citations

### 4. Pydantic Schemas ✅
- `WebsiteCrawlCreate`: Request validation for crawl initiation
- `WebsiteCrawlResponse`: Response for crawl initiation
- `WebsiteCrawlStatus`: Response for status queries
- `WebsiteChatRequest`: Request validation for chat
- `WebsiteChatResponse`: Response for chat with citations
- `SourceCitation`: Citation format with URL, title, snippet

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌────────────────────────────────┐    │
│  │  POST /websites/crawl          │    │
│  │  GET  /websites/crawl/status   │    │
│  │  POST /websites/chat           │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  rag_website.py                │    │
│  │  - create_or_get_collection    │    │
│  │  - create_knowledge_base       │    │
│  │  - start_crawl                 │    │
│  │  - check_status                │    │
│  │  - query_kb                    │    │
│  └────────────────────────────────┘    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         AWS Services                    │
│  ┌────────────────────────────────┐    │
│  │  Bedrock Knowledge Bases       │    │
│  │  - Web Crawler Data Source     │    │
│  │  - Titan Embeddings v2         │    │
│  │  - RetrieveAndGenerate API     │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │  OpenSearch Serverless         │    │
│  │  - Vector Storage (FAISS)      │    │
│  │  - 1024 dimensions             │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## How to Use

### 1. Start the Server

```bash
cd ChatBotBE/backend
uvicorn main:app --reload
```

### 2. Initiate Website Crawl

```bash
curl -X POST "http://localhost:8000/tenants/1/websites/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_pages": 100,
    "crawl_scope": "HOST"
  }'
```

**Response:**
```json
{
  "website_id": "550e8400-e29b-41d4-a716-446655440000",
  "knowledge_base_id": "ABCDEFGHIJ",
  "status": "STARTING",
  "estimated_completion_time": "2024-01-15T10:30:00Z",
  "message": "Website crawling initiated..."
}
```

### 3. Check Crawl Status

```bash
curl "http://localhost:8000/tenants/1/websites/crawl/550e8400-e29b-41d4-a716-446655440000/status"
```

**Response:**
```json
{
  "website_id": "550e8400-e29b-41d4-a716-446655440000",
  "website_url": "https://example.com",
  "knowledge_base_id": "ABCDEFGHIJ",
  "status": "COMPLETE",
  "pages_crawled": 45,
  "max_pages": 100,
  "start_time": "2024-01-15T10:00:00Z",
  "completion_time": "2024-01-15T10:15:00Z",
  "error_message": null
}
```

### 4. Ask Questions

```bash
curl -X POST "http://localhost:8000/tenants/1/websites/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://example.com",
    "question": "What are the main features?"
  }'
```

**Response:**
```json
{
  "answer": "The main features include...",
  "source_citations": [
    {
      "url": "https://example.com/features",
      "title": "Features",
      "snippet": "Our main features are..."
    }
  ],
  "website_status": "COMPLETE",
  "retrieved_chunks": 12,
  "session_id": "abc123"
}
```

## Testing

### Automated Test Script

Run the automated test script:

```bash
cd ChatBotBE/backend
python test_website_crawling.py
```

This will:
1. Initiate a crawl of a small test website
2. Poll status until complete
3. Ask a test question
4. Verify the complete flow works

### Manual Testing

1. **Test Crawl Initiation:**
   - Use a small website (< 10 pages) for quick testing
   - Check database for new records in `website_crawls` table

2. **Test Status Tracking:**
   - Poll status endpoint every 10 seconds
   - Verify status transitions: STARTING → IN_PROGRESS → COMPLETE

3. **Test Chat:**
   - Wait for status = COMPLETE
   - Ask questions about the website content
   - Verify answers include source citations

## Configuration

All configuration is in the `env` file:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Bedrock Configuration
BEDROCK_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKnowledgeBaseRole

# Crawling Configuration
MAX_CRAWL_PAGES_DEFAULT=100
MAX_CRAWL_PAGES_LIMIT=25000
CRAWL_SCOPE_DEFAULT=HOST
RETRIEVE_NUM_RESULTS=12
```

## Key Features

✅ **Fully Managed:** AWS handles all crawling, chunking, and embedding
✅ **Scalable:** Up to 25,000 pages per website
✅ **Multi-Tenant:** Isolated collections per tenant
✅ **Asynchronous:** Non-blocking API responses
✅ **Status Tracking:** Real-time progress monitoring
✅ **Semantic Search:** HYBRID search (semantic + keyword)
✅ **Source Citations:** Every answer includes source URLs
✅ **Error Handling:** Graceful failures with detailed error messages

## Limitations & Future Enhancements

### Current Limitations:
- OpenSearch collections are PUBLIC (no encryption/network policies)
- No automated tests (manual testing only)
- No comprehensive error logging/monitoring
- No re-crawl support yet
- No conversation history logging

### Future Enhancements:
1. Add encryption and network policies for OpenSearch
2. Implement automated test suite
3. Add CloudWatch alarms and monitoring
4. Support re-crawling with incremental updates
5. Add conversation history logging
6. Implement rate limiting per tenant
7. Add cost tracking and quotas

## Troubleshooting

### Error: "AccessDeniedException"
- Check AWS credentials in `env` file
- Verify IAM permissions (see `AWS_SETUP_GUIDE.md`)
- Ensure Bedrock is enabled in your region

### Error: "Collection creation failed"
- Check OpenSearch Serverless quotas
- Verify IAM role has correct permissions
- Check CloudWatch logs for details

### Error: "Website not ready for querying"
- Wait for crawl to complete (check status endpoint)
- Verify status is "COMPLETE" before querying

### Crawl takes too long
- Reduce `max_pages` for testing
- Use smaller websites for initial tests
- Check robots.txt isn't blocking the crawler

## Files Modified/Created

### New Files:
- `rag_model/rag_website.py` - AWS integration layer
- `test_website_crawling.py` - Manual test script
- `test_aws_permissions.py` - AWS permissions test
- `AWS_SETUP_GUIDE.md` - Setup instructions
- `WEBSITE_CRAWLING_IMPLEMENTATION.md` - This file

### Modified Files:
- `models.py` - Added WebsiteCrawl and TenantCollection models
- `schemas.py` - Added website crawling schemas
- `main.py` - Added 3 new API endpoints
- `env` - Added AWS credentials and configuration

## Success Criteria ✅

All implementation tasks completed:
- ✅ Database models and schemas
- ✅ AWS integration functions
- ✅ API endpoints
- ✅ Configuration setup
- ✅ Test scripts

The feature is ready for manual testing and can be deployed to production after validation!

## Next Steps

1. **Test the implementation:**
   ```bash
   python test_website_crawling.py
   ```

2. **Try with your own website:**
   - Start with a small website (< 10 pages)
   - Monitor the crawl status
   - Ask questions once complete

3. **Integrate with frontend:**
   - Add UI for crawl initiation
   - Add status polling with progress bar
   - Add chat interface for website Q&A

4. **Production readiness:**
   - Add encryption policies for OpenSearch
   - Implement comprehensive error logging
   - Add monitoring and alerts
   - Write automated tests

## Support

For issues or questions:
1. Check CloudWatch logs for detailed error messages
2. Review AWS Bedrock console for knowledge base status
3. Check database records in `website_crawls` table
4. Refer to `AWS_SETUP_GUIDE.md` for setup issues
