# Create OpenSearch Index Manually via AWS Console

## Why Manual Creation?

AWS OpenSearch Serverless permissions can take hours to propagate. The fastest way to create the index today is through the AWS Console, which has immediate access.

## Step-by-Step Instructions

### 1. Go to OpenSearch Serverless Console

1. Open AWS Console: https://console.aws.amazon.com/
2. Navigate to: **Amazon OpenSearch Service** → **Serverless** → **Collections**
3. Find and click on collection: **kb-collection-3421**
   - Collection ID: `r0fqf4rli0n632ypd4la`

### 2. Open OpenSearch Dashboards

1. On the collection details page, find the **OpenSearch Dashboards URL**
2. Click on it to open OpenSearch Dashboards
   - URL will be like: `https://r0fqf4rli0n632ypd4la.ap-south-1.aoss.amazonaws.com/_dashboards`

### 3. Open Dev Tools

1. In OpenSearch Dashboards, click the menu icon (☰) in the top left
2. Navigate to: **Management** → **Dev Tools**
3. This opens a console where you can run commands

### 4. Create the Index

Copy and paste this command into the Dev Tools console:

```json
PUT /bedrock-knowledge-base-default-index
{
  "settings": {
    "index.knn": true,
    "index.knn.algo_param.ef_search": 512
  },
  "mappings": {
    "properties": {
      "bedrock-knowledge-base-default-vector": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "engine": "faiss",
          "name": "hnsw",
          "space_type": "l2",
          "parameters": {
            "ef_construction": 512,
            "m": 16
          }
        }
      },
      "AMAZON_BEDROCK_TEXT_CHUNK": {
        "type": "text",
        "index": true
      },
      "AMAZON_BEDROCK_METADATA": {
        "type": "text",
        "index": false
      }
    }
  }
}
```

5. Click the **Play** button (▶) or press **Ctrl+Enter** to execute
6. You should see a success response:

```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "index": "bedrock-knowledge-base-default-index"
}
```

### 5. Verify the Index

Run this command to verify the index was created:

```json
GET /bedrock-knowledge-base-default-index
```

You should see the index settings and mappings.

### 6. Test the Crawl

Go back to your server terminal and run:

```bash
sudo docker exec -it fastapi-backend python test_new_crawl.py
```

The crawl should now work!

## Troubleshooting

### If you get "403 Forbidden" in OpenSearch Dashboards:

This means you don't have access through the console either. Options:

1. **Wait**: Permissions are still propagating (can take hours)
2. **Add your user to the data access policy**:
   - Go to: OpenSearch Service → Serverless → Data access policies
   - Find policy: `kb-policy-3421`
   - Add your IAM user ARN to the principals list
   - Wait 5-10 minutes for propagation

### If you can't find the OpenSearch Dashboards URL:

1. Go to the collection details page
2. Look for "OpenSearch Dashboards URL" section
3. If not visible, the collection might not be ACTIVE yet

### If the index creation fails:

Check the error message:
- **"resource_already_exists_exception"**: Index already exists (good!)
- **"security_exception"**: Permissions issue, wait longer
- **"invalid_index_name_exception"**: Copy the command exactly as shown

## Alternative: Use AWS CLI

If you have AWS CLI configured locally with full permissions:

```bash
# Create a JSON file with the index definition
cat > index.json << 'EOF'
{
  "settings": {
    "index.knn": true
  },
  "mappings": {
    "properties": {
      "bedrock-knowledge-base-default-vector": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "engine": "faiss",
          "name": "hnsw"
        }
      },
      "AMAZON_BEDROCK_TEXT_CHUNK": {
        "type": "text"
      },
      "AMAZON_BEDROCK_METADATA": {
        "type": "text"
      }
    }
  }
}
EOF

# Create the index using curl with AWS SigV4
aws opensearchserverless create-index \
  --collection-id r0fqf4rli0n632ypd4la \
  --index-name bedrock-knowledge-base-default-index \
  --index-definition file://index.json
```

## What Happens After Index Creation?

Once the index is created:
1. Bedrock can create knowledge bases successfully
2. Website crawls will work
3. The system is ready for production use
4. No more manual intervention needed

## Expected Timeline

- **Manual creation via Console**: 2-5 minutes
- **Waiting for permissions to propagate**: 2-24 hours

Choose manual creation for immediate results!
