# Fix 403 Forbidden Error - OpenSearch Serverless

## Problem

You're getting this error when crawling:
```
Request failed: [security_exception] 403 Forbidden
```

## Root Cause

According to [AWS OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-data-access.html):

> **"Being granted permissions within a data access policy is not sufficient to access data in your OpenSearch Serverless collection. An associated principal must also be granted access to the IAM permissions `aoss:APIAccessAll` and `aoss:DashboardsAccessAll`. Both permissions grant full access to collection resources... If a principal doesn't have both of these IAM permissions, they will receive 403 errors when attempting to send requests to the collection."**

You have TWO types of permissions needed:

1. **Data Access Policy** ✅ (You have this)
   - Controls what operations you can do (CreateIndex, WriteDocument, etc.)
   - Configured via OpenSearch Serverless data access policies

2. **IAM Permissions** ❌ (You're missing this)
   - Controls whether you can access the OpenSearch API at all
   - Must be attached to the IAM role/user
   - Required permissions: `aoss:APIAccessAll` and `aoss:DashboardsAccessAll`

## Solution

### Step 1: Check Current Permissions

```bash
cd ~/DotStarkRag365/backend
sudo docker exec -it fastapi-backend python check_bedrock_iam_permissions.py
```

This will show you what IAM permissions your Bedrock role currently has.

### Step 2: Add Missing IAM Permissions

```bash
sudo docker exec -it fastapi-backend python fix_bedrock_iam_permissions.py
```

This script will add an inline IAM policy to your Bedrock role with:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll",
        "aoss:DashboardsAccessAll"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Wait for Propagation

Wait 10-30 seconds for IAM changes to propagate across AWS.

### Step 4: Test Again

```bash
sudo docker exec -it fastapi-backend python test_new_crawl.py
```

The 403 errors should now be resolved!

## Why This Happens

AWS has a two-layer security model for OpenSearch Serverless:

1. **IAM Layer** (Identity & Access Management)
   - "Can this principal access OpenSearch APIs at all?"
   - Controlled by IAM policies on the role/user
   - Required: `aoss:APIAccessAll`

2. **Data Access Layer** (OpenSearch Serverless)
   - "What can this principal do with the data?"
   - Controlled by data access policies
   - Permissions: `aoss:CreateIndex`, `aoss:WriteDocument`, etc.

Both layers must allow the action, or you get 403 Forbidden.

## Manual Fix (Alternative)

If you prefer to add the permissions manually:

1. Go to AWS IAM Console
2. Find your Bedrock role (check BEDROCK_ROLE_ARN in your .env)
3. Add an inline policy with:
   - Action: `aoss:APIAccessAll`
   - Action: `aoss:DashboardsAccessAll`
   - Resource: `*`

## Verification

After fixing, you should see:
- ✅ Collection created successfully
- ✅ Index created automatically by Bedrock
- ✅ Crawl status: ACTIVE or COMPLETED
- ❌ No more 403 Forbidden errors

## References

- [AWS OpenSearch Serverless Data Access Control](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-data-access.html)
- [IAM Permissions for OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/security-iam-serverless.html)
