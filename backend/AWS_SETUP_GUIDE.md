# AWS Setup Guide for Website Crawling Feature

## Step 1: Add Your AWS Credentials

1. Open the `env` file in `ChatBotBE/backend/env`
2. Replace the placeholder values with your actual AWS credentials:

```bash
# Replace these values:
AWS_ACCESS_KEY_ID=your_access_key_here          # ← Paste your access key
AWS_SECRET_ACCESS_KEY=your_secret_key_here      # ← Paste your secret key
AWS_REGION=us-east-1                            # ← Change if using different region
AWS_ACCOUNT_ID=your_account_id_here             # ← Will be auto-detected by test script
```

## Step 2: Install Required Python Package

The test script requires `python-dotenv` to load environment variables:

```bash
cd ChatBotBE/backend
pip install python-dotenv
```

## Step 3: Run the Permission Test Script

```bash
cd ChatBotBE/backend
python test_aws_permissions.py
```

The script will test:
- ✅ AWS credentials are valid
- ✅ Bedrock Knowledge Bases access
- ✅ Bedrock Agent Runtime access
- ✅ OpenSearch Serverless access
- ✅ IAM access
- ✅ Bedrock foundation models (Titan Embeddings v2)

## Step 4: Review Test Results

### If All Tests Pass ✅
You're ready to start implementation! The script will show:
```
🎉 All tests passed! Your AWS account is ready for implementation.
```

### If Some Tests Fail ❌
The script will show which permissions are missing. Common issues:

#### Missing Bedrock Permissions
Add these IAM permissions to your AWS user/role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:ListKnowledgeBases",
        "bedrock:CreateKnowledgeBase",
        "bedrock:GetKnowledgeBase",
        "bedrock:DeleteKnowledgeBase",
        "bedrock:CreateDataSource",
        "bedrock:DeleteDataSource",
        "bedrock:StartIngestionJob",
        "bedrock:GetIngestionJob",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate",
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Missing OpenSearch Serverless Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "aoss:ListCollections",
    "aoss:CreateCollection",
    "aoss:DeleteCollection",
    "aoss:BatchGetCollection",
    "aoss:CreateAccessPolicy",
    "aoss:CreateSecurityPolicy",
    "aoss:APIAccessAll"
  ],
  "Resource": "*"
}
```

#### Missing IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "iam:ListRoles",
    "iam:GetRole",
    "iam:CreateRole",
    "iam:AttachRolePolicy",
    "iam:PassRole"
  ],
  "Resource": "arn:aws:iam::*:role/BedrockKnowledgeBaseRole*"
}
```

## Step 5: Create BedrockKnowledgeBaseRole (If Needed)

If the test script shows that `BedrockKnowledgeBaseRole` doesn't exist, you need to create it:

### Option A: Using AWS Console
1. Go to IAM → Roles → Create Role
2. Select "AWS Service" → "Bedrock"
3. Name: `BedrockKnowledgeBaseRole`
4. Attach these permissions:
   - Custom policy for OpenSearch Serverless access
   - Custom policy for Bedrock model access

### Option B: Using AWS CLI
```bash
# Create trust policy file
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name BedrockKnowledgeBaseRole \
  --assume-role-policy-document file://trust-policy.json

# Create permissions policy file
cat > permissions-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
    }
  ]
}
EOF

# Attach the policy
aws iam put-role-policy \
  --role-name BedrockKnowledgeBaseRole \
  --policy-name BedrockKnowledgeBasePolicy \
  --policy-document file://permissions-policy.json
```

## Step 6: Update env File with Role ARN

After the test script runs successfully, it will show you the correct `BEDROCK_ROLE_ARN`. Update your `env` file:

```bash
BEDROCK_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockKnowledgeBaseRole
```

## Troubleshooting

### Error: "No AWS credentials found"
- Make sure you've pasted your credentials in the `env` file
- Check that there are no extra spaces or quotes around the values

### Error: "AccessDeniedException"
- Your AWS user/role doesn't have the required permissions
- Contact your AWS administrator to add the permissions listed above

### Error: "Region not supported"
- Bedrock Knowledge Bases is not available in all regions
- Try changing `AWS_REGION` to `us-east-1` or `us-west-2`

### Error: "Titan Embeddings v2 not found"
- The model might not be enabled in your region
- Go to AWS Console → Bedrock → Model access → Enable Titan Embeddings v2

## Next Steps

Once all tests pass:
1. ✅ Your AWS account is configured correctly
2. ✅ Start implementing the tasks from `tasks.md`
3. ✅ Begin with database setup (Task 1.1)

## Support

If you encounter issues:
1. Check the test script output for specific error messages
2. Review AWS CloudTrail logs for detailed error information
3. Ensure your AWS account has Bedrock enabled in your region
