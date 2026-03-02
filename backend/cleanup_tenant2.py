import boto3
import os
from dotenv import load_dotenv
from database import SessionLocal
from models import TenantCollection

load_dotenv('env')

# Clean database
db = SessionLocal()
tc = db.query(TenantCollection).filter_by(tenant_id=2).first()
if tc:
    db.delete(tc)
    db.commit()
    print('✅ Cleaned database')
db.close()

# Clean AWS
aoss = boto3.client('opensearchserverless', region_name=os.getenv('AWS_REGION'))

# List and delete collections
collections = aoss.list_collections()
for col in collections.get('collectionSummaries', []):
    if 'kb-collection-2' in col['name']:
        print(f'Deleting collection: {col["name"]}')
        try:
            aoss.delete_collection(id=col['id'])
            print('✅ Deleted collection')
        except Exception as e:
            print(f'Error: {e}')

# Delete policies
for name, ptype in [('kb-policy-2', 'data'), ('kb-encryption-2', 'encryption'), ('kb-network-2', 'network')]:
    try:
        if ptype == 'data':
            aoss.delete_access_policy(name=name, type=ptype)
        else:
            aoss.delete_security_policy(name=name, type=ptype)
        print(f'✅ Deleted {name}')
    except: pass

print('\n✅ Cleanup complete - ready to test')
