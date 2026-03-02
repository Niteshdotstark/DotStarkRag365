from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from fastapi import UploadFile
import re

class UserBase(BaseModel):
    email: str = Field(..., description="User email") # Use EmailStr for email validation
    username: Optional[str] # Username is now a required field for UserBase
    phone_number: Optional[str] = None # Optional phone number
    address: Optional[str] = None # Optional address
    is_active: Optional[bool] = True # Include is_active for consistency, default to True

class UserCreate(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8)
    username: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r"^[\w\.\-]*@[\w\.\-]+\.\w+$", v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain at least one number')
        return v

class UserResponse(UserBase):
    id: int
    tenant_id: Optional[int] = None
    class Config:
        from_attributes = True

class TenantBase(BaseModel):
    id: int
    name: str
    created_at: datetime
    fb_url: Optional[str]
    insta_url: Optional[str]
    fb_verify_token: Optional[str] = None
    fb_access_token: Optional[str] = None
    insta_access_token: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    class Config:
        from_attributes = True

class TenantUpdate(BaseModel):
    name: Optional[str] = None  # Make name optional for updates
    fb_url: Optional[str] = None
    insta_url: Optional[str] = None
    fb_verify_token: Optional[str] = None
    fb_access_token: Optional[str] = None
    insta_access_token: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

class TenantCreate(BaseModel):
    name: str
    fb_url: Optional[str]
    insta_url: Optional[str]
    fb_verify_token: Optional[str] = None
    fb_access_token: Optional[str] = None
    insta_access_token: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class KnowledgeBaseFileCreate(BaseModel):
    pass

class KnowledgeBaseFileResponse(BaseModel):
    id: str
    filename: Optional[str]
    stored_filename: Optional[str]
    file_path: Optional[str]
    file_type: str
    url: Optional[str]
    tenant_id: int
    uploaded_by: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

class DatabaseBase(BaseModel):
    name: str
    description: Optional[str] = None

class TopQuestionAnalysis(BaseModel):
    count: int
    cleaned_question: str
    example_original_question: str

class DatabaseCreate(DatabaseBase):
    pass

class DatabaseResponse(DatabaseBase):
    id: int
    tenant_id: int
    created_at: datetime
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    response_mode: Optional[str] = Field(default="detailed", description="Response mode: 'detailed', 'summary', or 'both'")

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = Field(default_factory=list)
    response_type: Optional[str] = Field(default="detailed", description="Type of response: 'detailed', 'summary', or 'both'")

class DualChatResponse(BaseModel):
    detailed_response: Optional[str] = None
    summary_response: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    response_type: str = Field(description="Type of response: 'detailed', 'summary', or 'both'")
    summary_metadata: Optional[dict] = None

class TenantValuesUpdate(BaseModel):
    tenant_id: int

class ConversationCountResponse(BaseModel):
    count: int

class TenantResponse(TenantBase):
    id: int
    created_at: datetime
    knowledge_item_count: int
    conversation_count: int

    class Config:
        from_attributes = True

class ActivityLogResponse(BaseModel):
    id: str  # A unique ID for the key prop in React
    title: str
    subtitle: str
    created_at: datetime
    type: str  # 'info', 'success', or 'warning'

    class Config:
        from_attributes = True


# Website Crawling Schemas

class WebsiteCrawlCreate(BaseModel):
    """Request schema for initiating website crawl"""
    url: str = Field(..., description="Website URL to crawl", max_length=2048)
    max_pages: int = Field(default=100, ge=1, le=25000, description="Maximum pages to crawl")
    crawl_scope: str = Field(default="HOST_ONLY", description="Crawl scope: DEFAULT, HOST_ONLY, or SUBDOMAINS")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('crawl_scope')
    def validate_crawl_scope(cls, v):
        if v not in ['DEFAULT', 'HOST_ONLY', 'SUBDOMAINS']:
            raise ValueError('crawl_scope must be DEFAULT, HOST_ONLY, or SUBDOMAINS')
        return v


class WebsiteCrawlResponse(BaseModel):
    """Response schema for crawl initiation"""
    website_id: str
    knowledge_base_id: str
    status: str
    estimated_completion_time: Optional[datetime]
    message: str
    
    class Config:
        from_attributes = True


class WebsiteCrawlStatus(BaseModel):
    """Response schema for status queries"""
    website_id: str
    website_url: str
    knowledge_base_id: Optional[str]
    status: str
    pages_crawled: int
    max_pages: int
    start_time: Optional[datetime]
    completion_time: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class WebsiteChatRequest(BaseModel):
    """Request schema for website chat"""
    website_url: str = Field(..., description="Website URL to query", max_length=2048)
    question: str = Field(..., description="User's question", min_length=1, max_length=2000)
    
    @validator('website_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SourceCitation(BaseModel):
    """Source citation with URL"""
    url: str
    title: Optional[str]
    snippet: Optional[str]


class WebsiteChatResponse(BaseModel):
    """Response schema for website chat"""
    answer: str
    source_citations: List[SourceCitation]
    website_status: str
    retrieved_chunks: int
    session_id: Optional[str]
