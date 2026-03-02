# Current Multi-Agent Website Crawler Architecture

## 🏗️ High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER / CLIENT                                   │
│                         (Web Browser / API Client)                           │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTP/HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EC2 INSTANCE                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        FastAPI Backend                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  POST /tenants/{agent_id}/websites/crawl                        │ │ │
│  │  │  GET  /tenants/{agent_id}/websites/{website_id}/status          │ │ │
│  │  │  POST /tenants/{agent_id}/websites/{website_id}/chat            │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                              │                                         │ │
│  │                              ▼                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    PostgreSQL Database                           │ │ │
│  │  │  • agents table                                                  │ │ │
│  │  │  • agent_collections table                                       │ │ │
│  │  │  • website_crawls table                                          │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 │ AWS SDK (boto3)
                                 ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS SERVICES                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    AWS IAM (Identity & Access)                          │ │
│  │  • BedrockExecutionRole (arn:aws:iam::xxx:role/BedrockRole)           │ │
│  │  • Permissions: Bedrock, OpenSearch, S3 access                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                           │
│                                  ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │              AMAZON OPENSEARCH SERVERLESS                               │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Collection: kb-collection-{agent_id}                             │ │ │
│  │  │  • Encryption Policy: kb-encryption-{agent_id}                    │ │ │
│  │  │  • Network Policy: kb-network-{agent_id} (PUBLIC)                 │ │ │
│  │  │  • Data Access Policy: kb-policy-{agent_id}                       │ │ │
│  │  │  • Vector Index: bedrock-knowledge-base-default-index             │ │ │
│  │  │    - Engine: FAISS                                                │ │ │
│  │  │    - Dimension: 1024                                              │ │ │
│  │  │    - Fields: vector, text_chunk, metadata                         │ │ │
│  │  │  💰 Cost: $700/month per collection                               │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                           │
│                                  ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    AMAZON BEDROCK                                       │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Knowledge Base: kb-agent-{agent_id}                              │ │ │
│  │  │  • Storage: OpenSearch Serverless                                 │ │ │
│  │  │  • Embedding Model: amazon.titan-embed-text-v2:0                  │ │ │
│  │  │  • Status: ACTIVE                                                 │ │ │
│  │  │  💰 Cost: ~$1/month per KB                                        │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Data Source: web-crawler-{uuid}                                  │ │ │
│  │  │  • Type: WEB                                                      │ │ │
│  │  │  • Seed URL: https://example.com                                  │ │ │
│  │  │  • Crawl Scope: HOST_ONLY                                         │ │ │
│  │  │  • Max Pages: 1-25000                                             │ │ │
│  │  │  • Rate Limit: 300 pages/min                                      │ │ │
│  │  │  • Chunking: Fixed Size (300 tokens, 20% overlap)                │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Ingestion Job: {ingestion_job_id}                                │ │ │
│  │  │  • Status: STARTING → IN_PROGRESS → COMPLETE                      │ │ │
│  │  │  • Statistics: pages scanned, indexed, failed                     │ │ │
│  │  │  ⚠️ Limit: 1 concurrent job per Knowledge Base                    │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Foundation Models                                                │ │ │
│  │  │  • Embeddings: amazon.titan-embed-text-v2:0                       │ │ │
│  │  │  • Chat: anthropic.claude-3-sonnet-20240229-v1:0                 │ │ │
│  │  │  💰 Cost: Pay-per-use (~$0.003/1K tokens)                         │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                  │                                           │
│                                  ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         AMAZON S3                                       │ │
│  │  • Bucket: rag-chat-uploads                                            │ │
│  │  • Prefix: knowledge_base/{agent_id}/                                  │ │
│  │  • Storage: Documents, URLs, backups                                   │ │
│  │  💰 Cost: $0.023/GB-month + requests                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Multi-Agent Flow Diagram

### Agent 1 (Concurrent)
```
User → POST /tenants/100/websites/crawl
         │
         ├─→ Create Agent 100 (if not exists)
         ├─→ Create OpenSearch Collection: kb-collection-100
         ├─→ Create Knowledge Base: kb-agent-100
         ├─→ Create Data Source + Start Crawl
         └─→ Return 202 (crawling in background)
```

### Agent 2 (Concurrent)
```
User → POST /tenants/200/websites/crawl
         │
         ├─→ Create Agent 200 (if not exists)
         ├─→ Create OpenSearch Collection: kb-collection-200
         ├─→ Create Knowledge Base: kb-agent-200
         ├─→ Create Data Source + Start Crawl
         └─→ Return 202 (crawling in background)
```

### Agent 3 (Concurrent)
```
User → POST /tenants/300/websites/crawl
         │
         ├─→ Create Agent 300 (if not exists)
         ├─→ Create OpenSearch Collection: kb-collection-300
         ├─→ Create Knowledge Base: kb-agent-300
         ├─→ Create Data Source + Start Crawl
         └─→ Return 202 (crawling in background)
```

✅ All 3 agents crawl simultaneously without conflicts!


## 🔄 Detailed Request Flow

### 1. Crawl Initiation Flow
```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /tenants/456/websites/crawl
     │ Body: {"url": "https://example.com", "max_pages": 100, "crawl_scope": "HOST_ONLY"}
     ▼
┌─────────────────────────────────────────────────────────────┐
│  EC2: FastAPI Backend                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Validate AWS configuration                          │ │
│  │ 2. Create/Get Agent record (agent_id=456)              │ │
│  │ 3. Create WebsiteCrawl record (status="pending")       │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS: OpenSearch Serverless                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. Check if collection exists for agent 456            │ │
│  │    • Query AgentCollection table                       │ │
│  │    • If exists: Reuse collection                       │ │
│  │    • If not: Create new collection                     │ │
│  │      - Create encryption policy                        │ │
│  │      - Create network policy                           │ │
│  │      - Create data access policy                       │ │
│  │      - Create collection (kb-collection-456)           │ │
│  │      - Wait for ACTIVE status (up to 5 min)            │ │
│  │      - Wait 90s for permissions to propagate           │ │
│  │      - Create vector index (FAISS, 1024 dim)           │ │
│  │      - Save to database                                │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS: Bedrock Knowledge Base                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 5. Check if Knowledge Base exists for agent 456        │ │
│  │    • Query WebsiteCrawl for existing KB                │ │
│  │    • If exists: Reuse KB                               │ │
│  │    • If not: Create new KB                             │ │
│  │      - Name: kb-agent-456                              │ │
│  │      - Embedding: amazon.titan-embed-text-v2:0         │ │
│  │      - Storage: OpenSearch collection ARN              │ │
│  │      - Wait for ACTIVE status (up to 2 min)            │ │
│  │      - Save KB ID to database                          │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS: Bedrock Data Source                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 6. Create Web Crawler Data Source                      │ │
│  │    • Name: web-crawler-{uuid}                          │ │
│  │    • Seed URL: https://example.com                     │ │
│  │    • Crawl scope: HOST_ONLY                            │ │
│  │    • Rate limit: 300 pages/min                         │ │
│  │    • Chunking: 300 tokens, 20% overlap                 │ │
│  │    • Save data_source_id to database                   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 7. Start Ingestion Job                                 │ │
│  │    • Bedrock starts crawling asynchronously            │ │
│  │    • Status: STARTING                                  │ │
│  │    • Save ingestion_job_id to database                 │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌──────────┐
│  Client  │ ← 202 Accepted
└──────────┘   {
                 "website_id": "uuid",
                 "knowledge_base_id": "KB123",
                 "status": "STARTING",
                 "message": "Check status at /tenants/456/websites/{uuid}/status"
               }
```

### 2. Status Check Flow
```
┌──────────┐
│  Client  │
└────┬─────┘
     │ GET /tenants/456/websites/{website_id}/status
     ▼
┌─────────────────────────────────────────────────────────────┐
│  EC2: FastAPI Backend                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Query WebsiteCrawl by agent_id + website_id         │ │
│  │ 2. Check cached status (COMPLETE/FAILED)               │ │
│  │    • If cached: Return immediately                     │ │
│  │    • If not: Query AWS Bedrock                         │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS: Bedrock Agent                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. Get Ingestion Job Status                            │ │
│  │    • Status: STARTING / IN_PROGRESS / COMPLETE / FAILED│ │
│  │    • Statistics:                                       │ │
│  │      - numberOfDocumentsScanned                        │ │
│  │      - numberOfDocumentsIndexed                        │ │
│  │      - numberOfDocumentsFailed                         │ │
│  │    • Update database with latest status                │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌──────────┐
│  Client  │ ← 200 OK
└──────────┘   {
                 "status": "COMPLETE",
                 "pages_crawled": 246,
                 "start_time": "2026-03-01T10:00:00Z",
                 "completion_time": "2026-03-01T10:15:00Z"
               }
```

### 3. Chat Query Flow
```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /tenants/456/websites/{website_id}/chat
     │ Body: {"question": "What is this website about?"}
     ▼
┌─────────────────────────────────────────────────────────────┐
│  EC2: FastAPI Backend                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Query WebsiteCrawl by agent_id + website_id         │ │
│  │ 2. Verify crawl is COMPLETE                            │ │
│  │ 3. Get knowledge_base_id                               │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS: Bedrock Runtime (RetrieveAndGenerate API)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. Retrieve relevant chunks from OpenSearch            │ │
│  │    • Embedding: Convert question to vector             │ │
│  │    • Search: HYBRID (vector + keyword)                 │ │
│  │    • Results: Top 12 chunks                            │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 5. Generate answer with Claude 3 Sonnet                │ │
│  │    • Model: anthropic.claude-3-sonnet-20240229-v1:0    │ │
│  │    • Prompt: "Answer based on context..."              │ │
│  │    • Temperature: 0.7                                  │ │
│  │    • Max tokens: 2048                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌──────────┐
│  Client  │ ← 200 OK
└──────────┘   {
                 "answer": "This website is about...",
                 "citations": [
                   {"url": "https://example.com/page1", "snippet": "..."}
                 ]
               }
```


## 🗄️ Database Schema

```sql
-- Agents Table
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    agent_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Collections Table (OpenSearch)
CREATE TABLE agent_collections (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    collection_id VARCHAR(255) UNIQUE,
    collection_arn VARCHAR(500),
    collection_name VARCHAR(255),
    collection_endpoint VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Website Crawls Table
CREATE TABLE website_crawls (
    website_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id INTEGER REFERENCES agents(id),
    tenant_id INTEGER NULL,  -- Legacy, nullable
    website_url VARCHAR(500),
    knowledge_base_id VARCHAR(255),
    data_source_id VARCHAR(255),
    ingestion_job_id VARCHAR(255),
    status VARCHAR(50),  -- pending, STARTING, IN_PROGRESS, COMPLETE, FAILED
    pages_crawled INTEGER DEFAULT 0,
    max_pages INTEGER,
    crawl_scope VARCHAR(50),  -- HOST_ONLY, SUBDOMAINS, DEFAULT
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔐 AWS IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:CreateKnowledgeBase",
        "bedrock:GetKnowledgeBase",
        "bedrock:DeleteKnowledgeBase",
        "bedrock:CreateDataSource",
        "bedrock:StartIngestionJob",
        "bedrock:GetIngestionJob",
        "bedrock:InvokeModel",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:CreateCollection",
        "aoss:DeleteCollection",
        "aoss:BatchGetCollection",
        "aoss:ListCollections",
        "aoss:CreateSecurityPolicy",
        "aoss:DeleteSecurityPolicy",
        "aoss:CreateAccessPolicy",
        "aoss:DeleteAccessPolicy",
        "aoss:APIAccessAll"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::rag-chat-uploads/*",
        "arn:aws:s3:::rag-chat-uploads"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## 💰 Cost Breakdown by Component

### Per Agent (Monthly):
```
┌─────────────────────────────────────────────────────────┐
│ Component                    │ Cost/Month               │
├─────────────────────────────────────────────────────────┤
│ OpenSearch Collection        │ $700.00                  │
│ Bedrock Knowledge Base       │ $1.00                    │
│ Bedrock Embeddings (100 pgs) │ $0.50                    │
│ Bedrock Chat (100 queries)   │ $3.00                    │
│ S3 Storage (1 GB)            │ $0.02                    │
├─────────────────────────────────────────────────────────┤
│ TOTAL PER AGENT              │ $704.52                  │
└─────────────────────────────────────────────────────────┘
```

### Shared Resources (Monthly):
```
┌─────────────────────────────────────────────────────────┐
│ Component                    │ Cost/Month               │
├─────────────────────────────────────────────────────────┤
│ EC2 t3.medium (FastAPI)      │ $30.00                   │
│ PostgreSQL RDS (if used)     │ $15.00 (or local)        │
│ Data Transfer                │ $2.00                    │
├─────────────────────────────────────────────────────────┤
│ TOTAL SHARED                 │ $47.00                   │
└─────────────────────────────────────────────────────────┘
```

### Total Cost Examples:
- **1 Agent**: $704 + $47 = **$751/month**
- **5 Agents**: ($704 × 5) + $47 = **$3,567/month**
- **10 Agents**: ($704 × 10) + $47 = **$7,087/month**

## ⚡ Performance Characteristics

### Crawling Performance:
- **Rate**: 300 pages/minute (AWS Bedrock limit)
- **100 pages**: ~20 seconds
- **1000 pages**: ~3-4 minutes
- **10,000 pages**: ~30-35 minutes

### Query Performance:
- **Embedding generation**: ~100ms
- **Vector search**: ~50-200ms
- **Answer generation**: ~2-5 seconds
- **Total response time**: ~3-6 seconds

### Concurrency:
- **Multiple agents**: ✅ Unlimited (each has own resources)
- **Same agent, multiple sites**: ❌ Sequential (1 ingestion job limit)
- **Chat queries**: ✅ Unlimited concurrent queries

## 🔄 Resource Lifecycle

### Creation:
```
1. Agent created → Auto-create on first crawl
2. OpenSearch Collection → Created once per agent, reused
3. Knowledge Base → Created once per agent, reused
4. Data Source → Created per website crawl
5. Ingestion Job → Created per crawl, runs once
```

### Reuse Strategy:
```
Agent 456 crawls site1.com:
  ✅ Create Collection (kb-collection-456)
  ✅ Create KB (kb-agent-456)
  ✅ Create Data Source (web-crawler-uuid1)
  ✅ Start Ingestion Job

Agent 456 crawls site2.com:
  ♻️  Reuse Collection (kb-collection-456)
  ♻️  Reuse KB (kb-agent-456)
  ✅ Create Data Source (web-crawler-uuid2)
  ✅ Start Ingestion Job (waits if job1 running)
```

### Cleanup:
```
Delete Agent 456:
  🗑️  Delete all Data Sources
  🗑️  Delete Knowledge Base
  🗑️  Delete OpenSearch Collection
  🗑️  Delete Security Policies
  💰 Save $704/month
```

## 🎯 Key Architectural Decisions

### ✅ What Works Well:
1. **Multi-agent isolation** - Each agent has independent resources
2. **Resource reuse** - Collection and KB shared across websites
3. **Async crawling** - Non-blocking API responses
4. **Managed services** - AWS handles scaling and maintenance

### ⚠️ Current Limitations:
1. **Cost** - $700/month per agent (OpenSearch Serverless)
2. **Sequential crawls** - Same agent can't crawl multiple sites simultaneously
3. **No pause/resume** - Collections always running, always charging
4. **Vendor lock-in** - Tightly coupled to AWS Bedrock

### 🔄 Optimization Opportunities:
1. **Replace OpenSearch** with ChromaDB/Qdrant (93% cost reduction)
2. **Custom crawler** instead of Bedrock Web Crawler
3. **Local embeddings** with Ollama (free)
4. **Spot instances** for EC2 (70% discount)

---

## 📝 Summary

This architecture provides a fully managed, scalable solution for multi-agent website crawling with RAG capabilities. The main trade-off is cost ($700/month per agent) for convenience and managed services. For production use, consider the cost optimization alternatives in `COST_OPTIMIZATION_ALTERNATIVES.md`.
