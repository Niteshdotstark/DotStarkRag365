# AWS Services & Cost Analysis

## 📋 Complete List of AWS Services Used

### 1. **Amazon Bedrock** 🤖
**Purpose**: AI/ML foundation models for embeddings and chat
- **Components**:
  - Knowledge Bases (for RAG)
  - Agents (for orchestration)
  - Foundation Models:
    - `amazon.titan-embed-text-v2:0` (embeddings)
    - `anthropic.claude-3-sonnet-20240229-v1:0` (chat/generation)
    - `meta.llama3-8b-instruct-v1:0` (alternative LLM)

**Pricing Model**: ⚠️ **PAY PER USE + STORAGE**
- ✅ **On-Demand Charges**:
  - Embedding API calls: ~$0.0001 per 1K tokens
  - Claude 3 Sonnet: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
  - Llama 3: ~$0.0003 per 1K tokens
- ⚠️ **Storage Charges**:
  - Knowledge Base storage: ~$0.024 per GB-month
  - Vector embeddings stored in OpenSearch
- ⚠️ **Idle Costs**: Knowledge Bases incur storage costs even when not actively querying

**Estimated Monthly Cost**:
- 10 agents, 100 pages each: ~$5-10/month (embeddings + storage)
- 1000 chat queries/month: ~$15-30/month
- **Total**: ~$20-40/month for light usage

---

### 2. **Amazon OpenSearch Serverless** 🔍
**Purpose**: Vector database for storing and searching embeddings

**Pricing Model**: ⚠️ **ALWAYS RUNNING - HOURLY CHARGES**
- ⚠️ **OCU (OpenSearch Compute Units)**: $0.24 per OCU-hour
  - Minimum: 2 OCUs for indexing + 2 OCUs for search = 4 OCUs minimum
  - **Base cost**: 4 OCUs × $0.24 × 730 hours = **~$700/month minimum**
- ⚠️ **Storage**: $0.024 per GB-month
  - 10 GB of vectors: ~$0.24/month
  - 100 GB of vectors: ~$2.40/month

**Idle Costs**: ⚠️ **YES - ALWAYS RUNNING**
- Collections remain active 24/7
- You pay for OCUs even with zero queries
- **This is your biggest cost driver**

**Cost Optimization**:
- Use 1 collection per agent (current design) ✅
- Consider deleting unused collections
- Monitor OCU usage and scale down if possible

**Estimated Monthly Cost**:
- 1 collection: ~$700/month (minimum)
- 5 collections: ~$3,500/month
- 10 collections: ~$7,000/month

---

### 3. **Amazon S3** 📦
**Purpose**: File storage for knowledge base documents and conversation history

**Buckets Used**:
- `rag-chat-uploads` (knowledge base files)
- `rag-vectordb-bucket` (vector indexes - if used)

**Pricing Model**: ✅ **PAY PER USE**
- ✅ **Storage**: $0.023 per GB-month (first 50 TB)
- ✅ **PUT requests**: $0.005 per 1,000 requests
- ✅ **GET requests**: $0.0004 per 1,000 requests
- ✅ **Data transfer**: Free within same region, $0.09/GB outbound

**Idle Costs**: ⚠️ **YES - STORAGE ONLY**
- You pay for stored files even if not accessed
- Minimal cost for small files

**Estimated Monthly Cost**:
- 10 GB storage: ~$0.23/month
- 100 GB storage: ~$2.30/month
- 10,000 requests: ~$0.05/month
- **Total**: ~$1-5/month for typical usage

---

### 4. **Amazon SQS** 📨
**Purpose**: Message queue for triggering Lambda indexing jobs

**Queue**: `RagLambdaIndexing.fifo` (FIFO queue)

**Pricing Model**: ✅ **PAY PER USE**
- ✅ **FIFO requests**: $0.50 per million requests
- ✅ **First 1 million requests/month**: FREE

**Idle Costs**: ❌ **NO**
- Zero cost when not sending messages

**Estimated Monthly Cost**:
- 10,000 messages: FREE
- 100,000 messages: FREE
- 2 million messages: ~$0.50/month
- **Total**: ~$0-1/month

---

### 5. **AWS Lambda** ⚡
**Purpose**: Serverless function for indexing documents (implied by SQS queue)

**Pricing Model**: ✅ **PAY PER USE**
- ✅ **Requests**: $0.20 per 1 million requests
- ✅ **Duration**: $0.0000166667 per GB-second
- ✅ **First 1 million requests/month**: FREE
- ✅ **First 400,000 GB-seconds/month**: FREE

**Idle Costs**: ❌ **NO**
- Zero cost when not invoked

**Estimated Monthly Cost**:
- 10,000 invocations (1 GB, 10s each): FREE
- 100,000 invocations: ~$0.20/month
- **Total**: ~$0-2/month

---

### 6. **AWS IAM** 🔐
**Purpose**: Identity and access management, roles, policies

**Pricing Model**: ✅ **FREE**
- No charges for IAM users, roles, or policies

**Idle Costs**: ❌ **NO**

---

### 7. **AWS STS** 🎫
**Purpose**: Security Token Service for temporary credentials

**Pricing Model**: ✅ **FREE**
- No charges for STS API calls

**Idle Costs**: ❌ **NO**

---

## 💰 Total Cost Breakdown

### Scenario 1: Single Agent (Minimal Usage)
| Service | Monthly Cost | Idle Cost? |
|---------|-------------|------------|
| OpenSearch Serverless (1 collection) | $700 | ⚠️ YES |
| Bedrock (100 pages, 100 queries) | $10 | ⚠️ Storage only |
| S3 (10 GB) | $1 | ⚠️ Storage only |
| SQS | $0 | ❌ NO |
| Lambda | $0 | ❌ NO |
| **TOTAL** | **~$711/month** | **~$700/month idle** |

### Scenario 2: 10 Agents (Moderate Usage)
| Service | Monthly Cost | Idle Cost? |
|---------|-------------|------------|
| OpenSearch Serverless (10 collections) | $7,000 | ⚠️ YES |
| Bedrock (1000 pages, 1000 queries) | $100 | ⚠️ Storage only |
| S3 (100 GB) | $5 | ⚠️ Storage only |
| SQS | $1 | ❌ NO |
| Lambda | $2 | ❌ NO |
| **TOTAL** | **~$7,108/month** | **~$7,000/month idle** |

### Scenario 3: 100 Agents (High Usage)
| Service | Monthly Cost | Idle Cost? |
|---------|-------------|------------|
| OpenSearch Serverless (100 collections) | $70,000 | ⚠️ YES |
| Bedrock (10,000 pages, 10,000 queries) | $1,000 | ⚠️ Storage only |
| S3 (1 TB) | $50 | ⚠️ Storage only |
| SQS | $10 | ❌ NO |
| Lambda | $20 | ❌ NO |
| **TOTAL** | **~$71,080/month** | **~$70,000/month idle** |

---

## ⚠️ CRITICAL COST WARNINGS

### 1. OpenSearch Serverless is ALWAYS RUNNING
- **Biggest cost**: ~$700/month per collection
- **Idle cost**: Same as active cost
- **Cannot be paused or stopped**
- **Recommendation**: Delete unused collections immediately

### 2. Bedrock Knowledge Bases Have Storage Costs
- Small but accumulates over time
- ~$0.024 per GB-month
- Delete unused knowledge bases to save costs

### 3. S3 Storage Accumulates
- Files remain until explicitly deleted
- Set lifecycle policies to auto-delete old files
- Monitor bucket size regularly

---

## 💡 Cost Optimization Strategies

### 1. **Share Collections Across Agents** (Current Design ✅)
- Use 1 OpenSearch collection per agent (not per website)
- Saves $700/month per website
- Current implementation already does this

### 2. **Delete Unused Resources**
```python
# Delete old knowledge bases
bedrock_agent.delete_knowledge_base(knowledgeBaseId='...')

# Delete old collections
aoss_client.delete_collection(id='...')

# Delete S3 files
s3_client.delete_object(Bucket='...', Key='...')
```

### 3. **Use S3 Lifecycle Policies**
```json
{
  "Rules": [{
    "Id": "DeleteOldFiles",
    "Status": "Enabled",
    "Expiration": { "Days": 90 }
  }]
}
```

### 4. **Monitor and Alert**
- Set up AWS Cost Explorer alerts
- Alert when monthly cost exceeds threshold
- Review AWS Cost & Usage Report weekly

### 5. **Consider Alternatives for Dev/Test**
- Use local vector DB (ChromaDB, FAISS) for development
- Only use OpenSearch Serverless in production
- Estimated savings: $700/month for dev environment

---

## 📊 Cost Comparison: Pay-Per-Use vs Always-On

| Component | Type | Idle Cost |
|-----------|------|-----------|
| Bedrock API calls | ✅ Pay-per-use | $0 |
| Bedrock storage | ⚠️ Storage-based | Small |
| OpenSearch Serverless | ⚠️ Always-on | **$700/month** |
| S3 storage | ⚠️ Storage-based | Small |
| S3 requests | ✅ Pay-per-use | $0 |
| SQS | ✅ Pay-per-use | $0 |
| Lambda | ✅ Pay-per-use | $0 |

**Key Insight**: OpenSearch Serverless is 98% of your idle costs.

---

## 🎯 Recommendations

### For Development:
1. Use 1 shared collection for all dev agents
2. Delete collections when not actively developing
3. Consider local vector DB alternatives

### For Production:
1. Monitor collection usage
2. Delete inactive agents' collections after 30 days
3. Set up cost alerts at $1000, $5000, $10000 thresholds
4. Review AWS bill weekly
5. Consider reserved capacity if usage is predictable

### Cost-Effective Architecture:
- ✅ Current design (1 KB per agent) is optimal
- ✅ Reusing collections is good
- ⚠️ Monitor and delete unused resources
- ⚠️ OpenSearch Serverless is expensive - consider alternatives for low-traffic scenarios

---

## 📞 AWS Support Resources

- **Cost Calculator**: https://calculator.aws/
- **Cost Explorer**: AWS Console → Billing → Cost Explorer
- **Pricing Pages**:
  - Bedrock: https://aws.amazon.com/bedrock/pricing/
  - OpenSearch Serverless: https://aws.amazon.com/opensearch-service/pricing/
  - S3: https://aws.amazon.com/s3/pricing/

---

## ✅ Summary: Are You Only Paying When Using?

| Service | Pay-per-use? | Idle Cost? | Answer |
|---------|--------------|------------|--------|
| Bedrock API | ✅ YES | ❌ NO | Only pay when calling APIs |
| Bedrock Storage | ⚠️ PARTIAL | ⚠️ YES | Pay for stored embeddings |
| OpenSearch | ❌ NO | ⚠️ YES | **Always running, always paying** |
| S3 | ⚠️ PARTIAL | ⚠️ YES | Pay for storage, not access |
| SQS | ✅ YES | ❌ NO | Only pay when sending messages |
| Lambda | ✅ YES | ❌ NO | Only pay when invoked |

**Bottom Line**: 
- ✅ Most services are pay-per-use
- ⚠️ **OpenSearch Serverless is always-on and expensive (~$700/month per collection)**
- ⚠️ Storage costs (S3, Bedrock) accumulate but are minimal
- 💡 Delete unused collections to avoid idle costs
