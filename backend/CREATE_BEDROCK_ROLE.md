# Create Bedrock Knowledge Base IAM Role

## Overview

The website crawling feature requires an IAM role that Bedrock Knowledge Bases can assume to access OpenSearch Serverless collections. This guide shows you how to create this role.

## Error You're Seeing

```
ValidationException - Bedrock Knowledge Base was unable to assume the given role. 
Provide the proper permissions and retry the request.
```

This means the IAM role `BedrockKnowledgeBaseRole` either doesn't exist or doesn't have the correct trust policy.

## Option 1: Create Role via AWS Console (Recommended)

### Step 1: Go to IAM Console
1. Open AWS Console: https://console.aws.amazon.com/iam/
2. Click "Roles" in the left sidebar
3. Click "Create role"

### Step 2: Configure Trust Relationship
1. Select "Custom trust policy"
2. Paste this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "705406524080"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:ap-south-1:705406524080:knowledge-base/*"
        }
      }
    }
  ]
}
```

3. Click "Next"

### Step 3: Attach Permissions
1. Click "Create policy" (opens in new tab)
2. Select "JSON" tab
3. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OpenSearchServerlessAccess",
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:ap-south-1:705406524080:collection/*"
    },
    {
      "Sid": "BedrockModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    }
  ]
}
```

4. Click "Next"
5. Name the policy: `BedrockKnowledgeBasePolicy`
6. Click "Create policy"
7. Go back to the role creation tab
8. Click refresh button
9. Search for `BedrockKnowledgeBasePolicy`
10. Check the box next to it
11. Click "Next"

### Step 4: Name the Role
1. Role name: `BedrockKnowledgeBaseRole`
2. Description: `Role for Bedrock Knowledge Bases to access OpenSearch Serverless`
3. Click "Create role"

### Step 5: Verify
The role ARN should be:
```
arn:aws:iam::705406524080:role/BedrockKnowledgeBaseRole
```

This matches what's in your `env` file, so no changes needed there!

## Option 2: Create Role via AWS CLI

If you have AWS CLI installed and configured:

```bash
# Create the trust policy file
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "705406524080"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:ap-south-1:705406524080:knowledge-base/*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name BedrockKnowledgeBaseRole \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for Bedrock Knowledge Bases to access OpenSearch Serverless"

# Create the permissions policy file
cat > permissions-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OpenSearchServerlessAccess",
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:ap-south-1:705406524080:collection/*"
    },
    {
      "Sid": "BedrockModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    }
  ]
}
EOF

# Create the policy
aws iam create-policy \
  --policy-name BedrockKnowledgeBasePolicy \
  --policy-document file://permissions-policy.json

# Attach the policy to the role
aws iam attach-role-policy \
  --role-name BedrockKnowledgeBaseRole \
  --policy-arn arn:aws:iam::705406524080:policy/BedrockKnowledgeBasePolicy

# Verify the role was created
aws iam get-role --role-name BedrockKnowledgeBaseRole
```

## After Creating the Role

1. Wait 1-2 minutes for AWS to propagate the role
2. Restart your FastAPI server
3. Run the test again:
   ```bash
   python test_website_crawling.py
   ```

## Troubleshooting

### Error: "Role already exists"
If the role already exists but has wrong permissions:

1. Go to IAM Console → Roles
2. Search for `BedrockKnowledgeBaseRole`
3. Click on it
4. Go to "Trust relationships" tab
5. Click "Edit trust policy"
6. Replace with the trust policy above
7. Go to "Permissions" tab
8. Attach the `BedrockKnowledgeBasePolicy` if not already attached

### Error: "Access Denied"
Make sure your AWS credentials have permission to create IAM roles:
- `iam:CreateRole`
- `iam:CreatePolicy`
- `iam:AttachRolePolicy`

## Next Steps

After creating the role, the website crawling feature will work! You can then:

1. Test crawling: `POST /tenants/{tenant_id}/websites/crawl`
2. Check status: `GET /tenants/{tenant_id}/websites/crawl/{website_id}/status`
3. Ask questions: `POST /tenants/{tenant_id}/websites/chat`
