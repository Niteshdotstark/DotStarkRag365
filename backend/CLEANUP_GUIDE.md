# AWS Resource Cleanup Guide

## Quick Cleanup - Delete All OpenSearch Collections

To delete all OpenSearch Serverless collections and Bedrock Knowledge Bases (saves ~$700/month per collection):

### Option 1: List Resources First (Recommended)
```bash
cd ~/DotStarkRag365/backend
python3 cleanup_all_aws_resources.py --list
```

This will show you:
- All Bedrock Knowledge Bases
- All OpenSearch Serverless collections
- Estimated monthly costs

### Option 2: Delete All Resources
```bash
cd ~/DotStarkRag365/backend
python3 cleanup_all_aws_resources.py
```

When prompted, type `DELETE ALL` to confirm.

This will delete:
- ✅ All Bedrock Knowledge Bases
- ✅ All OpenSearch Serverless collections
- ✅ All associated security policies (encryption, network, data access)

## What Gets Deleted

1. **Bedrock Knowledge Bases** - All knowledge bases created for website crawling
2. **OpenSearch Collections** - All vector databases storing crawled content
3. **Security Policies** - Encryption, network, and data access policies

## Cost Savings

Each OpenSearch Serverless collection costs approximately **$700/month**.

If you have 5 collections, deleting them saves: **$3,500/month**

## Important Notes

⚠️ **WARNING**: This deletes all crawled website data. You'll need to re-crawl websites after cleanup.

⏱️ **Deletion Time**: Collections take 5-10 minutes to fully delete.

🔄 **Re-crawling**: After cleanup, you can crawl websites again using:
```bash
curl -X POST "http://13.204.201.22/tenants/{tenant_id}/websites/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_pages": 10,
    "crawl_scope": "HOST_ONLY"
  }'
```

## Verify Deletion

Check AWS Console:
1. Go to AWS Console → OpenSearch Service → Serverless collections
2. Verify collections are deleted
3. Go to AWS Console → Bedrock → Knowledge bases
4. Verify knowledge bases are deleted

## Alternative: Delete Specific Collection

If you want to delete only specific collections, use the AWS CLI:

```bash
# List collections
aws opensearchserverless list-collections --region ap-south-1

# Delete specific collection
aws opensearchserverless delete-collection --id <collection-id> --region ap-south-1

# Delete specific knowledge base
aws bedrock-agent delete-knowledge-base --knowledge-base-id <kb-id> --region ap-south-1
```

## Database Cleanup

The cleanup script only deletes AWS resources. To also clean up database records:

```bash
# Connect to PostgreSQL
sudo docker exec -it postgres_db psql -U postgres -d multi_tenant_admin

# Delete website crawl records
DELETE FROM website_crawls;

# Exit
\q
```

## Support

If you encounter errors during cleanup:
1. Check AWS credentials are configured correctly
2. Verify IAM permissions for deleting resources
3. Check the error message in the script output
4. Collections in "DELETING" state will complete automatically
