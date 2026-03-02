import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')

# Get current caller identity
sts = boto3.client('sts', region_name=os.getenv('AWS_REGION'))
identity = sts.get_caller_identity()

print('Current AWS Identity:')
print(f'  Account: {identity["Account"]}')
print(f'  User ARN: {identity["Arn"]}')
print(f'  User ID: {identity["UserId"]}')
print()
print('Bedrock Role ARN:')
print(f'  {os.getenv("BEDROCK_ROLE_ARN")}')
