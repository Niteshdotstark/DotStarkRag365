import boto3
import os
from dotenv import load_dotenv

load_dotenv('env')
aoss = boto3.client('opensearchserverless', region_name=os.getenv('AWS_REGION'))

# List all collections
collections = aoss.list_collections()
for coll in collections['collectionSummaries']:
    if coll['name'] == 'kb-collection-2':
        coll_id = coll['id']
        print(f'Deleting collection: {coll_id}')
        aoss.delete_collection(id=coll_id)
        print('✅ Collection deleted')
        break
else:
    print('No collection found with name kb-collection-2')
