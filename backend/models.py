from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) # Make email non-nullable
    hashed_password = Column(String, nullable=False) # Make password non-nullable
    # New fields
    username = Column(String, unique=True, index=True, nullable=False) # Username should typically be unique and required
    phone_number = Column(String, unique=True, index=True, nullable=True) # Phone number can be optional and unique
    address = Column(String, nullable=True) # Address can be optional
    # Add is_active if you want to manage user activation status
    is_active = Column(Boolean, default=True)

    created_tenants = relationship("Tenant", back_populates="creator")


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    fb_url = Column(String(500), nullable=True)
    insta_url = Column(String(500), nullable=True)
    fb_verify_token = Column(String(255), nullable=True)
    fb_access_token = Column(String(500), nullable=True)
    insta_access_token = Column(String(500), nullable=True)
    telegram_bot_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="created_tenants")
    files = relationship("KnowledgeBaseFile", back_populates="tenant")
    
    # New relationships for website crawling
    website_crawls = relationship("WebsiteCrawl", back_populates="tenant", cascade="all, delete-orphan")
    opensearch_collection = relationship("TenantCollection", back_populates="tenant", uselist=False, cascade="all, delete-orphan")

class KnowledgeBaseFile(Base):
    __tablename__ = "knowledge_base_files"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, index=True, nullable=True)
    stored_filename = Column(String, index=True, nullable=True)
    file_path = Column(String, nullable=True)
    file_type = Column(String)  # MIME type or "url"
    category = Column(String)  # "file", "url", "database"
    url = Column(String, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant", back_populates="files")

class TenantValues(Base):
    __tablename__ = "tenant_values"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1)


# Website Crawling Models

class Agent(Base):
    """Stores agent information for website crawling - independent of tenants"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    website_crawls = relationship("WebsiteCrawl", back_populates="agent", cascade="all, delete-orphan")
    opensearch_collection = relationship("AgentCollection", back_populates="agent", uselist=False, cascade="all, delete-orphan")


class AgentCollection(Base):
    """Stores OpenSearch Serverless collection information per agent for reuse"""
    __tablename__ = "agent_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    collection_id = Column(String(255), nullable=False)
    collection_arn = Column(String(512), nullable=False)
    collection_name = Column(String(255), nullable=False)
    collection_endpoint = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    agent = relationship("Agent", back_populates="opensearch_collection")


class TenantCollection(Base):
    """Stores OpenSearch Serverless collection information per tenant for reuse"""
    __tablename__ = "tenant_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    collection_id = Column(String(255), nullable=False)
    collection_arn = Column(String(512), nullable=False)
    collection_name = Column(String(255), nullable=False)
    collection_endpoint = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    tenant = relationship("Tenant", back_populates="opensearch_collection")


class WebsiteCrawl(Base):
    """Stores metadata for website crawling operations and Bedrock resources"""
    __tablename__ = "website_crawls"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)  # Keep for backward compatibility
    website_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    website_url = Column(String(2048), nullable=False)
    knowledge_base_id = Column(String(255))
    data_source_id = Column(String(255))
    ingestion_job_id = Column(String(255))
    status = Column(String(50), nullable=False, default="pending")
    pages_crawled = Column(Integer, default=0)
    max_pages = Column(Integer, nullable=False, default=100)
    crawl_scope = Column(String(50), default="HOST_ONLY")
    error_message = Column(Text)
    failure_reasons = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    agent = relationship("Agent", back_populates="website_crawls")
    tenant = relationship("Tenant", back_populates="website_crawls")
    
    # Create composite index for fast lookups
    __table_args__ = (
        {'extend_existing': True}
    )
