"""
AWS Bedrock Knowledge Bases integration for website crawling.

This module provides functions to:
1. Create/manage OpenSearch Serverless collections
2. Create Bedrock Knowledge Bases
3. Configure Web Crawler data sources
4. Check ingestion job status
5. Query knowledge bases using RetrieveAndGenerate API
"""

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("..").resolve() / "env"
load_dotenv(dotenv_path=env_path)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_ROLE_ARN = os.getenv('BEDROCK_ROLE_ARN')


def validate_aws_configuration():
    """
    Validates that AWS credentials and configuration are properly set.
    
    Raises:
        ValueError: If configuration is missing or invalid
    """
    if not AWS_ACCOUNT_ID:
        raise ValueError("AWS_ACCOUNT_ID is not set in environment variables")
    
    if not BEDROCK_ROLE_ARN:
        raise ValueError("BEDROCK_ROLE_ARN is not set in environment variables")
    
    try:
        # Test AWS credentials
        sts_client = boto3.client('sts', region_name=AWS_REGION)
        identity = sts_client.get_caller_identity()
        print(f"✅ AWS credentials valid - Account: {identity['Account']}, User: {identity['Arn']}")
        return True
    except Exception as e:
        raise ValueError(f"AWS credentials are invalid or not configured: {str(e)}")


def create_or_get_opensearch_collection(tenant_id: int, db: Session) -> dict:
    """
    Creates or retrieves an OpenSearch Serverless collection for a tenant/agent.
    
    Note: tenant_id is actually used as agent_id in the new system.
    
    Args:
        tenant_id: Tenant/Agent identifier
        db: Database session
        
    Returns:
        dict: {
            'collection_id': str,
            'collection_arn': str,
            'collection_name': str,
            'collection_endpoint': str
        }
        
    Raises:
        ClientError: AWS API errors
    """
    from models import TenantCollection, AgentCollection, Agent
    
    agent_id = tenant_id  # Use as agent_id
    
    # Check if agent collection already exists in database
    existing_collection = db.query(AgentCollection).filter_by(agent_id=agent_id).first()
    if existing_collection:
        print(f"✅ Reusing existing OpenSearch collection for agent {agent_id}")
        return {
            'collection_id': existing_collection.collection_id,
            'collection_arn': existing_collection.collection_arn,
            'collection_name': existing_collection.collection_name,
            'collection_endpoint': existing_collection.collection_endpoint
        }
    
    # Also check old tenant collections for backward compatibility
    existing_tenant_collection = db.query(TenantCollection).filter_by(tenant_id=tenant_id).first()
    if existing_tenant_collection:
        print(f"✅ Reusing existing OpenSearch collection from tenant {tenant_id}")
        return {
            'collection_id': existing_tenant_collection.collection_id,
            'collection_arn': existing_tenant_collection.collection_arn,
            'collection_name': existing_tenant_collection.collection_name,
            'collection_endpoint': existing_tenant_collection.collection_endpoint
        }
    
    # Create new collection
    print(f"📦 Creating new OpenSearch Serverless collection for agent {agent_id}")
    aoss_client = boto3.client('opensearchserverless', region_name=AWS_REGION)
    
    collection_name = f"kb-collection-{tenant_id}"
    
    try:
        # Create encryption policy (required for collection creation)
        encryption_policy_name = f"kb-encryption-{tenant_id}"
        try:
            aoss_client.create_security_policy(
                name=encryption_policy_name,
                type='encryption',
                policy=f'''{{"Rules":[{{"ResourceType":"collection","Resource":["collection/{collection_name}"]}}],"AWSOwnedKey":true}}'''
            )
            print(f"   ✅ Created encryption policy: {encryption_policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConflictException':
                raise
            print(f"   ℹ️  Encryption policy already exists: {encryption_policy_name}")
        
        # Create network policy (PUBLIC access for MVP)
        network_policy_name = f"kb-network-{tenant_id}"
        try:
            aoss_client.create_security_policy(
                name=network_policy_name,
                type='network',
                policy=f'''[{{"Rules":[{{"ResourceType":"collection","Resource":["collection/{collection_name}"]}}],"AllowFromPublic":true}}]'''
            )
            print(f"   ✅ Created network policy: {network_policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConflictException':
                raise
            print(f"   ℹ️  Network policy already exists: {network_policy_name}")
        
        # Create data access policy for Bedrock role
        policy_name = f"kb-policy-{tenant_id}"
        
        # Get current user ARN to include in policy
        sts_client = boto3.client('sts', region_name=AWS_REGION)
        current_user_arn = sts_client.get_caller_identity()['Arn']
        
        try:
            aoss_client.create_access_policy(
                name=policy_name,
                type='data',
                policy=f'''[{{
                    "Rules": [
                        {{
                            "ResourceType": "collection",
                            "Resource": ["collection/{collection_name}"],
                            "Permission": ["aoss:*"]
                        }},
                        {{
                            "ResourceType": "index",
                            "Resource": ["index/{collection_name}/*"],
                            "Permission": ["aoss:*"]
                        }}
                    ],
                    "Principal": ["{BEDROCK_ROLE_ARN}", "{current_user_arn}"]
                }}]'''
            )
            print(f"   ✅ Created data access policy: {policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConflictException':
                raise
            print(f"   ℹ️  Data access policy already exists: {policy_name}")
        
        # Create collection
        collection_created_now = False
        try:
            response = aoss_client.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description=f'Knowledge base collection for tenant {tenant_id}'
            )
            
            collection_id = response['createCollectionDetail']['id']
            collection_arn = response['createCollectionDetail']['arn']
            collection_created_now = True
            
            print(f"   ⏳ Waiting for collection to become ACTIVE...")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # Collection already exists in AWS, fetch its details
                print(f"   ℹ️  Collection already exists in AWS, fetching details...")
                
                # List collections to find the existing one
                list_response = aoss_client.list_collections(
                    collectionFilters={'name': collection_name}
                )
                
                if not list_response.get('collectionSummaries'):
                    raise Exception(f"Collection {collection_name} exists but couldn't be found")
                
                collection_id = list_response['collectionSummaries'][0]['id']
                collection_arn = list_response['collectionSummaries'][0]['arn']
                
                print(f"   ✅ Found existing collection: {collection_id}")
                print(f"   ⏳ Waiting for collection to become ACTIVE...")
            else:
                raise
        
        # Wait for collection to become ACTIVE (max 10 minutes)
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        poll_interval = 30  # Check every 10 seconds
        
        while time.time() - start_time < max_wait_time:
            collection_response = aoss_client.batch_get_collection(ids=[collection_id])
            if collection_response['collectionDetails']:
                collection_status = collection_response['collectionDetails'][0]['status']
                elapsed = int(time.time() - start_time)
                
                if collection_status == 'ACTIVE':
                    collection_endpoint = collection_response['collectionDetails'][0].get('collectionEndpoint')
                    print(f"   ✅ Collection is ACTIVE (took {elapsed} seconds)")
                    print(f"   📍 Endpoint: {collection_endpoint}")
                    
                    # Wait for permissions to propagate only if collection was just created
                    if collection_created_now:
                        print(f"   ⏳ Waiting for permissions to propagate (90 seconds)...")
                        time.sleep(90)  # Wait 90 seconds for AWS to propagate permissions
                        print(f"   ✅ Permissions should be ready")
                    else:
                        print(f"   ℹ️  Using existing collection, skipping permission wait")
                    
                    # Create the vector index in OpenSearch (required for Bedrock)
                    print(f"   📊 Creating vector index in OpenSearch...")
                    try:
                        from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
                        
                        # Get AWS credentials for signing requests
                        credentials = boto3.Session().get_credentials()
                        auth = AWSV4SignerAuth(credentials, AWS_REGION, 'aoss')
                        
                        # Connect to OpenSearch Serverless
                        host = collection_endpoint.replace('https://', '').replace('/', '')
                        client = OpenSearch(
                            hosts=[{'host': host, 'port': 443}],
                            http_auth=auth,
                            use_ssl=True,
                            verify_certs=True,
                            connection_class=RequestsHttpConnection,
                            timeout=300
                        )
                        
                        # Create the vector index that Bedrock will use
                        index_name = 'bedrock-knowledge-base-default-index'
                        
                        if not client.indices.exists(index=index_name):
                            # Create index with vector search configuration
                            index_body = {
                                "settings": {
                                    "index.knn": True
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
                            
                            client.indices.create(index=index_name, body=index_body)
                            print(f"   ✅ Created vector index: {index_name}")
                        else:
                            print(f"   ℹ️  Vector index already exists: {index_name}")
                            
                    except Exception as e:
                        print(f"   ❌ Error creating vector index: {e}")
                        raise Exception(f"Failed to create OpenSearch index: {e}")
                    
                    break
                elif collection_status == 'FAILED':
                    raise Exception(f"Collection creation failed")
            time.sleep(poll_interval)
        else:
            raise Exception(f"Collection did not become ACTIVE within {max_wait_time} seconds (10 minutes). It may still be creating - try again in a few minutes.")
        
        # Store collection details in database (use AgentCollection)
        from models import AgentCollection
        
        agent_collection = AgentCollection(
            agent_id=agent_id,
            collection_id=collection_id,
            collection_arn=collection_arn,
            collection_name=collection_name,
            collection_endpoint=collection_endpoint
        )
        db.add(agent_collection)
        db.commit()
        db.refresh(agent_collection)
        
        print(f"   ✅ Collection details saved to database (agent_id: {agent_id})")
        
        return {
            'collection_id': collection_id,
            'collection_arn': collection_arn,
            'collection_name': collection_name,
            'collection_endpoint': collection_endpoint
        }
        
    except ClientError as e:
        print(f"   ❌ Error creating collection: {e}")
        raise


def create_or_get_knowledge_base(agent_id: int, collection_arn: str, db: Session) -> dict:
    """
    Creates or retrieves a Bedrock Knowledge Base for an agent.
    Reuses existing knowledge base if one exists for the agent.
    
    Args:
        agent_id: Agent identifier
        collection_arn: ARN of the OpenSearch Serverless collection
        db: Database session
        
    Returns:
        dict: {
            'knowledge_base_id': str,
            'knowledge_base_arn': str,
            'name': str
        }
        
    Raises:
        ClientError: AWS API errors
        ValueError: Invalid parameters
    """
    from models import WebsiteCrawl
    
    # Check if agent already has a knowledge base
    existing_crawl = db.query(WebsiteCrawl).filter(
        WebsiteCrawl.agent_id == agent_id,
        WebsiteCrawl.knowledge_base_id.isnot(None)
    ).first()
    
    if existing_crawl and existing_crawl.knowledge_base_id:
        print(f"✅ Reusing existing Knowledge Base: {existing_crawl.knowledge_base_id}")
        
        # Verify the knowledge base still exists in AWS
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        try:
            response = bedrock_agent.get_knowledge_base(
                knowledgeBaseId=existing_crawl.knowledge_base_id
            )
            return {
                'knowledge_base_id': response['knowledgeBase']['knowledgeBaseId'],
                'knowledge_base_arn': response['knowledgeBase']['knowledgeBaseArn'],
                'name': response['knowledgeBase']['name']
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"   ⚠️  Knowledge base not found in AWS, creating new one")
            else:
                raise
    
    # Create new knowledge base
    print(f"🧠 Creating new Bedrock Knowledge Base for agent {agent_id}")
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    kb_name = f"kb-agent-{agent_id}"
    
    try:
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description=f"Knowledge base for agent {agent_id}",
            roleArn=BEDROCK_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': f'bedrock-knowledge-base-default-index',
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        
        knowledge_base_id = response['knowledgeBase']['knowledgeBaseId']
        knowledge_base_arn = response['knowledgeBase']['knowledgeBaseArn']
        
        print(f"   ✅ Knowledge Base created: {knowledge_base_id}")
        
        # Wait for knowledge base to become ACTIVE
        print(f"   ⏳ Waiting for knowledge base to become ACTIVE...")
        max_wait = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=knowledge_base_id)
            kb_status = kb_response['knowledgeBase']['status']
            
            if kb_status == 'ACTIVE':
                print(f"   ✅ Knowledge Base is ACTIVE")
                break
            elif kb_status == 'FAILED':
                raise Exception(f"Knowledge Base creation failed")
            
            time.sleep(5)
        else:
            print(f"   ⚠️  Knowledge Base not ACTIVE yet, but continuing...")
        
        return {
            'knowledge_base_id': knowledge_base_id,
            'knowledge_base_arn': knowledge_base_arn,
            'name': kb_name
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Error creating knowledge base: {error_code} - {error_message}")
        raise


def create_knowledge_base(tenant_id: int, website_id: str, collection_arn: str, db: Session) -> dict:
    """
    DEPRECATED: Use create_or_get_knowledge_base instead.
    Creates a Bedrock Knowledge Base for a tenant's website.
    
    Args:
        tenant_id: Tenant identifier
        website_id: Unique website identifier (UUID)
        collection_arn: ARN of the OpenSearch Serverless collection
        db: Database session
        
    Returns:
        dict: {
            'knowledge_base_id': str,
            'knowledge_base_arn': str,
            'name': str
        }
        
    Raises:
        ClientError: AWS API errors
        ValueError: Invalid parameters
    """
    print(f"🧠 Creating Bedrock Knowledge Base for tenant {tenant_id}, website {website_id}")
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    kb_name = f"kb-{tenant_id}-{website_id}"
    
    try:
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description=f"Knowledge base for tenant {tenant_id} website {website_id}",
            roleArn=BEDROCK_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': f'bedrock-knowledge-base-default-index',
                    'fieldMapping': {
                        'vectorField': 'bedrock-knowledge-base-default-vector',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        
        knowledge_base_id = response['knowledgeBase']['knowledgeBaseId']
        knowledge_base_arn = response['knowledgeBase']['knowledgeBaseArn']
        
        print(f"   ✅ Knowledge Base created: {knowledge_base_id}")
        
        return {
            'knowledge_base_id': knowledge_base_id,
            'knowledge_base_arn': knowledge_base_arn,
            'name': kb_name
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Error creating knowledge base: {error_code} - {error_message}")
        raise


def create_data_source_and_start_crawl(
    knowledge_base_id: str,
    website_url: str,
    max_pages: int = 100,
    crawl_scope: str = "HOST",
    db: Session = None
) -> dict:
    """
    Creates a Web Crawler data source and starts ingestion.
    
    Args:
        knowledge_base_id: Bedrock Knowledge Base ID
        website_url: Seed URL to crawl
        max_pages: Maximum pages to crawl (1-25000)
        crawl_scope: Crawl scope (DEFAULT, HOST, SUBDOMAINS)
        db: Database session
        
    Returns:
        dict: {
            'data_source_id': str,
            'ingestion_job_id': str,
            'status': str
        }
        
    Raises:
        ClientError: AWS API errors
        ValueError: Invalid parameters
    """
    print(f"🕷️  Creating Web Crawler data source for {website_url}")
    
    # Validate URL format
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(website_url):
        raise ValueError(f"Invalid URL format: {website_url}. URL must start with http:// or https://")
    
    # Validate crawl scope
    valid_scopes = ['DEFAULT', 'HOST_ONLY', 'SUBDOMAINS']
    if crawl_scope not in valid_scopes:
        raise ValueError(f"Invalid crawl_scope: {crawl_scope}. Must be one of {valid_scopes}")
    
    # Validate max_pages
    if not 1 <= max_pages <= 25000:
        raise ValueError(f"Invalid max_pages: {max_pages}. Must be between 1 and 25000")
    
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    import uuid as uuid_lib
    data_source_name = f"web-crawler-{str(uuid_lib.uuid4())[:8]}"
    
    try:
        # Create data source
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name=data_source_name,
            description=f"Web crawler for {website_url}",
            dataSourceConfiguration={
                'type': 'WEB',
                'webConfiguration': {
                    'sourceConfiguration': {
                        'urlConfiguration': {
                            'seedUrls': [
                                {'url': website_url}
                            ]
                        }
                    },
                    'crawlerConfiguration': {
                        'crawlerLimits': {
                            'rateLimit': 300
                        },
                        'scope': crawl_scope
                    }
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 300,
                        'overlapPercentage': 20
                    }
                }
            }
        )
        
        data_source_id = response['dataSource']['dataSourceId']
        print(f"   ✅ Data source created: {data_source_id}")
        
        # Start ingestion job
        print(f"   🚀 Starting ingestion job...")
        ingestion_response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
        status = ingestion_response['ingestionJob']['status']
        
        print(f"   ✅ Ingestion job started: {ingestion_job_id}")
        print(f"   📊 Status: {status}")
        
        return {
            'data_source_id': data_source_id,
            'ingestion_job_id': ingestion_job_id,
            'status': status
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Error: {error_code} - {error_message}")
        raise


def check_ingestion_status(
    knowledge_base_id: str,
    data_source_id: str,
    ingestion_job_id: str,
    db: Session
) -> dict:
    """
    Checks the status of a Bedrock ingestion job.
    
    Args:
        knowledge_base_id: Bedrock Knowledge Base ID
        data_source_id: Data source ID
        ingestion_job_id: Ingestion job ID
        db: Database session
        
    Returns:
        dict: {
            'status': str,  # STARTING, IN_PROGRESS, COMPLETE, FAILED
            'pages_crawled': int,
            'start_time': datetime,
            'completion_time': datetime or None,
            'failure_reasons': list or None,
            'statistics': dict
        }
        
    Raises:
        ClientError: AWS API errors
    """
    bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    try:
        response = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            ingestionJobId=ingestion_job_id
        )
        
        job = response['ingestionJob']
        status = job['status']
        statistics = job.get('statistics', {})
        
        pages_crawled = statistics.get('numberOfDocumentsScanned', 0)
        start_time = job.get('startedAt')
        completion_time = job.get('updatedAt') if status in ['COMPLETE', 'FAILED'] else None
        failure_reasons = job.get('failureReasons', [])
        
        return {
            'status': status,
            'pages_crawled': pages_crawled,
            'start_time': start_time,
            'completion_time': completion_time,
            'failure_reasons': failure_reasons,
            'statistics': statistics
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Error checking status: {error_code} - {error_message}")
        raise


def query_website_knowledge_base(
    knowledge_base_id: str,
    question: str,
    num_results: int = 12
) -> dict:
    """
    Queries a website knowledge base using RetrieveAndGenerate API.
    
    Args:
        knowledge_base_id: Bedrock Knowledge Base ID
        question: User's question
        num_results: Number of chunks to retrieve (default: 12)
        
    Returns:
        dict: {
            'answer': str,
            'citations': list[dict],  # [{url, title, snippet}]
            'session_id': str,
            'retrieved_chunks': int
        }
        
    Raises:
        ClientError: AWS API errors
    """
    print(f"💬 Querying knowledge base {knowledge_base_id}")
    print(f"   ❓ Question: {question}")
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
    
    try:
        response = bedrock_runtime.retrieve_and_generate(
            input={
                'text': question
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': num_results,
                            'overrideSearchType': 'HYBRID'
                        }
                    },
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': '''You are a knowledgeable and friendly assistant. Answer questions naturally and conversationally based on the provided information.

INSTRUCTIONS:
- Provide direct, clear answers without phrases like "Based on the context" or "According to the information"
- Be comprehensive and include all relevant details from the context
- Use bullet points or numbered lists for multiple items or steps
- If the context doesn't contain the answer, say "I don't have that information in my knowledge base"
- Speak naturally, as if having a conversation
- Include specific examples, numbers, or details when available

Question: $query$

Context: $search_results$

Answer:'''
                        },
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'temperature': 0.7,
                                'maxTokens': 2048
                            }
                        }
                    }
                }
            }
        )
        
        answer = response['output']['text']
        session_id = response.get('sessionId')
        
        # Extract citations
        citations = []
        if 'citations' in response:
            for citation in response['citations']:
                for reference in citation.get('retrievedReferences', []):
                    location = reference.get('location', {})
                    s3_location = location.get('s3Location', {})
                    uri = s3_location.get('uri', '')
                    
                    # Extract URL from metadata if available
                    metadata = reference.get('metadata', {})
                    source_url = metadata.get('x-amz-bedrock-kb-source-uri', uri)
                    
                    citations.append({
                        'url': source_url,
                        'title': metadata.get('title'),
                        'snippet': reference.get('content', {}).get('text', '')[:200]
                    })
        
        print(f"   ✅ Answer generated")
        print(f"   📚 Citations: {len(citations)}")
        
        return {
            'answer': answer,
            'citations': citations,
            'session_id': session_id,
            'retrieved_chunks': len(citations)
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ Error querying knowledge base: {error_code} - {error_message}")
        raise
