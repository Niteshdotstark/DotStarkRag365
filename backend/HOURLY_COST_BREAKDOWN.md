# Hourly Cost Breakdown for Demo/Testing

## ✅ YES - OpenSearch Serverless is Charged by the Hour

### OpenSearch Serverless Pricing
- **Rate**: $0.24 per OCU-hour
- **Minimum**: 4 OCUs (2 for indexing + 2 for search)
- **Hourly cost**: 4 OCUs × $0.24 = **$0.96/hour**

### Cost for Different Demo Durations

| Duration | Cost Calculation | Total Cost |
|----------|------------------|------------|
| 1 hour | 4 OCUs × $0.24 × 1 hour | **$0.96** |
| 2 hours | 4 OCUs × $0.24 × 2 hours | **$1.92** |
| 3 hours | 4 OCUs × $0.24 × 3 hours | **$2.88** |
| 4 hours | 4 OCUs × $0.24 × 4 hours | **$3.84** |
| 8 hours | 4 OCUs × $0.24 × 8 hours | **$7.68** |
| 24 hours | 4 OCUs × $0.24 × 24 hours | **$23.04** |
| 1 month | 4 OCUs × $0.24 × 730 hours | **$700.80** |

### Other AWS Services (Also Hourly/Usage-Based)

#### Bedrock API Calls (Pay-per-use)
- **Embeddings**: ~$0.0001 per 1K tokens
- **Claude 3 Sonnet**: ~$0.003 per 1K input tokens
- **Demo cost**: ~$0.10-0.50 for a few hours of testing

#### S3 Storage (Pay-per-use)
- **Storage**: $0.023 per GB-month (prorated hourly)
- **Requests**: $0.005 per 1,000 PUT requests
- **Demo cost**: ~$0.01-0.05 for a few hours

#### EC2 Instance (Hourly)
- **t3.medium**: ~$0.0416/hour (~$30/month)
- **t3.large**: ~$0.0832/hour (~$60/month)
- **t3.xlarge**: ~$0.1664/hour (~$120/month)

## 💰 Total Demo Cost Estimate

### Scenario: 3-Hour Demo/Test Session

| Service | Cost |
|---------|------|
| OpenSearch Serverless (3 hours) | $2.88 |
| Bedrock API calls | $0.20 |
| S3 storage/requests | $0.02 |
| EC2 t3.medium (3 hours) | $0.12 |
| **TOTAL** | **~$3.22** |

### Scenario: 8-Hour Work Day

| Service | Cost |
|---------|------|
| OpenSearch Serverless (8 hours) | $7.68 |
| Bedrock API calls | $0.50 |
| S3 storage/requests | $0.05 |
| EC2 t3.medium (8 hours) | $0.33 |
| **TOTAL** | **~$8.56** |

## 🎯 Cost Optimization Strategy for Demo

### Before Demo:
```bash
# 1. Ensure all resources are deleted
python cleanup_all_aws_resources.py --list

# 2. Deploy backend to EC2
# (EC2 will start charging hourly)
```

### During Demo:
```bash
# 3. Start crawl (creates OpenSearch collection)
curl -X POST http://your-ec2-ip:8000/tenants/999/websites/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 10, "crawl_scope": "HOST_ONLY"}'

# OpenSearch starts charging from this moment
```

### After Demo (CRITICAL - Do this immediately!):
```bash
# 4. Delete all resources to stop charges
python cleanup_all_aws_resources.py

# 5. Stop EC2 instance (or terminate if not needed)
aws ec2 stop-instances --instance-ids i-xxxxx
```

## ⚠️ CRITICAL: Cleanup After Demo

**If you forget to delete resources:**
- OpenSearch continues charging $0.96/hour = $23/day = $700/month
- EC2 continues charging (if running)

**Set a reminder:**
- Delete resources immediately after demo
- Or set up AWS Budget Alert at $10 threshold

## 📊 Cost Comparison: Demo vs Production

| Scenario | Duration | OpenSearch Cost | Total Cost |
|----------|----------|-----------------|------------|
| Quick demo | 2 hours | $1.92 | ~$2.50 |
| Half-day test | 4 hours | $3.84 | ~$4.50 |
| Full-day test | 8 hours | $7.68 | ~$8.50 |
| Weekend (forgot to delete) | 48 hours | $46.08 | ~$47 |
| 1 week (forgot to delete) | 168 hours | $161.28 | ~$162 |
| 1 month (production) | 730 hours | $700.80 | ~$710 |

## 🚀 Recommended Demo Workflow

### Step 1: Deploy to EC2 (Start EC2 charges)
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone repo and setup
git clone your-repo
cd ChatBotBE/backend
pip install -r requirements.txt

# Start FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 2: Run Demo (Start OpenSearch charges)
```bash
# From your local machine
curl -X POST http://your-ec2-ip:8000/tenants/999/websites/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://planethomelending.com", "max_pages": 5, "crawl_scope": "HOST_ONLY"}'
```

### Step 3: Test Chat
```bash
# Wait for crawl to complete, then test
curl -X POST http://your-ec2-ip:8000/tenants/999/websites/{website_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this website about?"}'
```

### Step 4: Cleanup (Stop all charges)
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run cleanup script
cd ChatBotBE/backend
python cleanup_all_aws_resources.py

# Exit and stop EC2
exit
aws ec2 stop-instances --instance-ids i-xxxxx
```

## 💡 Pro Tips

1. **Set AWS Budget Alert**
   ```bash
   # Alert when cost exceeds $10
   aws budgets create-budget --account-id YOUR_ACCOUNT_ID \
     --budget file://budget.json
   ```

2. **Use CloudWatch Alarm**
   - Alert when OpenSearch collection exists for > 4 hours
   - Automatic email notification

3. **Automate Cleanup**
   - Set up Lambda function to auto-delete after 6 hours
   - Or use cron job on EC2

4. **Cost Tracking**
   - Check AWS Cost Explorer after demo
   - Verify all resources are deleted

## 📞 Emergency Cleanup

If you forget to delete and see unexpected charges:

```bash
# Quick cleanup from anywhere
aws opensearchserverless list-collections --region us-east-1
aws opensearchserverless delete-collection --id COLLECTION_ID --region us-east-1

aws bedrock-agent list-knowledge-bases --region us-east-1
aws bedrock-agent delete-knowledge-base --knowledge-base-id KB_ID --region us-east-1
```

## ✅ Summary

**Question**: If we use OpenSearch for few hours, cost is based on hours only?

**Answer**: ✅ **YES!** 
- OpenSearch Serverless charges **$0.96/hour**
- 3-hour demo = **$2.88**
- 8-hour test = **$7.68**
- **Just remember to delete resources after demo!**

**Total demo cost (3 hours)**: ~$3-4 including EC2, Bedrock, and S3.

**Key takeaway**: The hourly model is perfect for demos and testing, just don't forget to cleanup! 🎯
