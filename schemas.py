"""
Pydantic Schemas - Request and response models for API validation
Defines data structures for authentication, chat, messages, and admin operations
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base schemas
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Chat schemas
class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

# Message schemas
class MessageBase(BaseModel):
    content: str
    role: str  # 'user' or 'assistant'

class MessageCreate(MessageBase):
    chat_id: Optional[int] = None
    image_url: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    user_id: int
    created_at: datetime
    image_url: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Chat with messages
class ChatWithMessages(ChatResponse):
    messages: List[MessageResponse] = []

# File upload schemas
class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime
    url: str
    
    class Config:
        from_attributes = True

# Gemini API schemas
class GeminiRequest(BaseModel):
    message: str
    image_data: Optional[str] = None  # Base64 encoded image
    chat_id: Optional[int] = None

class GeminiResponse(BaseModel):
    response: str
    message_id: int
    chat_id: int

# Admin schemas
class AdminUserResponse(UserResponse):
    total_chats: int
    total_messages: int
    last_activity: Optional[datetime] = None

class AdminStats(BaseModel):
    total_users: int
    total_chats: int
    total_messages: int
    active_users_today: int
    new_users_this_week: int
    
class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    full_name: Optional[str] = None

# Search and pagination schemas
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be greater than 0')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int

# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None 