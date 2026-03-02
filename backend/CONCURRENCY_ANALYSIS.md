# Multi-Agent Concurrency Analysis

## Current Architecture Assessment

### ✅ What WORKS for Concurrent Agents

1. **Different Agent IDs = Independent Resources**
   - Each agent gets its own OpenSearch collection: `kb-collection-{agent_id}`
   - Each agent gets its own Knowledge Base: `kb-agent-{agent_id}`
   - Collections and KBs are isolated per agent
   - **Result**: Agent 1 and Agent 2 can crawl simultaneously without conflicts

2. **AWS Bedrock Handles Async Processing**
   - Crawling happens asynchronously in AWS
   - Your API returns immediately (202 status)
   - AWS manages the actual crawling in the background
   - **Result**: Multiple agents can have active crawls at the same time

3. **Database Isolation**
   - Each crawl gets a unique `website_id` (UUID)
   - Records are stored separately in `website_crawls` table
   - **Result**: No database conflicts between agents

### ⚠️ Current LIMITATIONS

1. **One Ingestion Job Per Knowledge Base**
   - AWS Bedrock limit: 1 concurrent ingestion job per knowledge base
   - **Impact**: If Agent 456 tries to crawl 2 websites simultaneously, the 2nd will fail
   - **Error**: "You have reached the maximum number of concurrent ingestion jobs per knowledge base: 1"

2. **Same Agent, Multiple Websites = Sequential Processing**
   - Current design: 1 Knowledge Base per agent (reused for all websites)
   - **Problem**: Agent 456 cannot crawl website A and website B at the same time
   - **Workaround**: Must wait for first crawl to complete

### 🎯 Concurrency Scenarios

#### ✅ SCENARIO 1: Different Agents, Different Websites (WORKS)
```
Agent 100 → https://example.com     ✅ Crawls in parallel
Agent 200 → https://another.com     ✅ Crawls in parallel
Agent 300 → https://third.com       ✅ Crawls in parallel
Agent 400 → https://fourth.com      ✅ Crawls in parallel
Agent 500 → https://fifth.com       ✅ Crawls in parallel
```
**Result**: All 5 crawl simultaneously without issues

#### ❌ SCENARIO 2: Same Agent, Multiple Websites (FAILS)
```
Agent 456 → https://site1.com       ✅ Starts crawling
Agent 456 → https://site2.com       ❌ Error: "max concurrent jobs reached"
```
**Result**: 2nd request fails until 1st completes

#### ✅ SCENARIO 3: Different Agents, Same Website (WORKS)
```
Agent 100 → https://example.com     ✅ Crawls in parallel
Agent 200 → https://example.com     ✅ Crawls in parallel
```
**Result**: Both agents can crawl the same website independently

## Recommendations

### Option 1: Keep Current Design (Recommended for MVP)
**Pros:**
- Simple architecture
- One KB per agent = easier management
- Cost-effective (fewer resources)

**Cons:**
- Same agent cannot crawl multiple sites simultaneously
- Must implement queue system if needed

**Best For:**
- Most use cases where agents crawl one site at a time
- Cost-conscious deployments

### Option 2: One Knowledge Base Per Website
**Change Required:**
```python
# Instead of: kb_name = f"kb-agent-{agent_id}"
# Use: kb_name = f"kb-agent-{agent_id}-{website_id}"
```

**Pros:**
- Same agent can crawl multiple websites simultaneously
- Each website is completely isolated

**Cons:**
- More AWS resources = higher costs
- More complex cleanup/management
- Potential AWS quota limits (default: 10 KBs per account)

**Best For:**
- High-volume scenarios
- Agents that need to crawl many sites concurrently

### Option 3: Implement Queue System
**Add a job queue for same-agent requests:**
```python
# Check if agent has active ingestion job
# If yes, queue the request
# Process queue when job completes
```

**Pros:**
- Handles concurrent requests gracefully
- No resource waste
- Better user experience (no errors)

**Cons:**
- More complex implementation
- Requires background worker or scheduler

## Current Answer to Your Question

**For your form with 5-6 API hits:**

✅ **If using DIFFERENT agent_ids:**
```
POST /tenants/100/websites/crawl → ✅ Works
POST /tenants/200/websites/crawl → ✅ Works
POST /tenants/300/websites/crawl → ✅ Works
POST /tenants/400/websites/crawl → ✅ Works
POST /tenants/500/websites/crawl → ✅ Works
POST /tenants/600/websites/crawl → ✅ Works
```
**All 6 will process concurrently without issues.**

❌ **If using SAME agent_id:**
```
POST /tenants/456/websites/crawl (site1) → ✅ Works
POST /tenants/456/websites/crawl (site2) → ❌ Error
POST /tenants/456/websites/crawl (site3) → ❌ Error
POST /tenants/456/websites/crawl (site4) → ❌ Error
POST /tenants/456/websites/crawl (site5) → ❌ Error
POST /tenants/456/websites/crawl (site6) → ❌ Error
```
**Only the first will succeed. Others will fail with "max concurrent jobs" error.**

## Immediate Action Items

1. **Document the limitation** in API docs
2. **Add better error handling** for concurrent job conflicts
3. **Consider implementing Option 3** (queue system) if needed
4. **Monitor AWS quotas** for Knowledge Base limits

## AWS Bedrock Quotas to Consider

- **Knowledge Bases per account**: 10 (default, can request increase)
- **Concurrent ingestion jobs per KB**: 1 (hard limit)
- **Data sources per KB**: 10
- **OpenSearch collections**: 50 per account

## Cost Implications

**Current Design (1 KB per agent):**
- 100 agents = 100 Knowledge Bases
- 100 OpenSearch collections
- Estimated cost: ~$500-1000/month (depending on usage)

**Alternative Design (1 KB per website):**
- 100 agents × 10 websites = 1000 Knowledge Bases
- Would exceed default quota (10 KBs)
- Would need quota increase request
- Estimated cost: ~$5000-10000/month

## Conclusion

Your current architecture **DOES handle multi-agent concurrency** well, as long as each API hit uses a **different agent_id**. 

If your form creates 5-6 requests with different agent_ids, all will process concurrently without errors.

If your form creates multiple requests with the same agent_id, only the first will succeed, and others will fail with a concurrency error.
