"""
Main FastAPI Application - Gemini Clone Backend
Comprehensive backend with authentication, chat, admin, and file upload functionality
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime, timedelta
import math

# Local imports
from config import settings
from database import get_db, init_db
from models import User, Chat, Message, FileUpload
from schemas import *
from auth import AuthManager, get_current_user, get_current_active_user, get_current_admin_user
from gemini_service import gemini_service

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend API for Gemini Clone with authentication and chat functionality"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create admin user if not exists"""
    init_db()
    
    # Create admin user if not exists
    db = next(get_db())
    admin_user = db.query(User).filter(User.email == settings.admin_email).first()
    if not admin_user:
        AuthManager.create_user(
            db=db,
            email=settings.admin_email,
            username="admin",
            password=settings.admin_password,
            full_name="System Administrator",
            is_admin=True
        )
        print(f"Admin user created: {settings.admin_email}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ==================== AUTHENTICATION ROUTES ====================

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Create user
        user = AuthManager.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        # Create access token
        access_token = AuthManager.create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = AuthManager.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token = AuthManager.create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.put("/auth/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = user_update.username
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(current_user)
    return current_user

# ==================== CHAT ROUTES ====================

@app.get("/chats", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chats for current user"""
    chats = db.query(Chat).filter(
        Chat.user_id == current_user.id,
        Chat.is_active == True
    ).order_by(desc(Chat.updated_at)).all()
    
    # Add message count to each chat
    for chat in chats:
        chat.message_count = db.query(Message).filter(Message.chat_id == chat.id).count()
    
    return chats

@app.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new chat"""
    chat = Chat(
        title=chat_data.title,
        user_id=current_user.id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    chat.message_count = 0
    return chat

@app.get("/chats/{chat_id}", response_model=ChatWithMessages)
async def get_chat_with_messages(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat with all messages"""
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at).all()
    
    chat.messages = messages
    return chat

@app.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update chat"""
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if chat_update.title is not None:
        chat.title = chat_update.title
    if chat_update.is_active is not None:
        chat.is_active = chat_update.is_active
    
    db.commit()
    db.refresh(chat)
    return chat

@app.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete chat"""
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Soft delete
    chat.is_active = False
    db.commit()
    
    return {"message": "Chat deleted successfully"}

# ==================== MESSAGE & GEMINI ROUTES ====================

@app.post("/chat", response_model=GeminiResponse)
async def send_message(
    request: GeminiRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send message to Gemini AI"""
    try:
        # Get or create chat
        if request.chat_id:
            chat = db.query(Chat).filter(
                Chat.id == request.chat_id,
                Chat.user_id == current_user.id
            ).first()
            if not chat:
                raise HTTPException(status_code=404, detail="Chat not found")
        else:
            # Create new chat with first message as title
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            chat = Chat(title=title, user_id=current_user.id)
            db.add(chat)
            db.commit()
            db.refresh(chat)
        
        # Validate image if provided
        if request.image_data and not gemini_service.validate_image(request.image_data):
            raise HTTPException(status_code=400, detail="Invalid image format or size")
        
        # Save user message
        user_message = Message(
            content=request.message,
            role="user",
            chat_id=chat.id,
            user_id=current_user.id,
            image_url=request.image_data if request.image_data else None
        )
        db.add(user_message)
        db.commit()
        
        # Get conversation context
        recent_messages = db.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(desc(Message.created_at)).limit(5).all()
        
        context_messages = [{"role": msg.role, "content": msg.content} for msg in reversed(recent_messages[1:])]
        context = gemini_service.get_conversation_context(context_messages)
        
        # Generate AI response
        ai_response = await gemini_service.generate_response(
            message=request.message,
            image_data=request.image_data,
            context=context
        )
        
        # Save AI message
        ai_message = Message(
            content=ai_response,
            role="assistant",
            chat_id=chat.id,
            user_id=current_user.id
        )
        db.add(ai_message)
        
        # Update chat timestamp
        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_message)
        
        return {
            "response": ai_response,
            "message_id": ai_message.id,
            "chat_id": chat.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# ==================== FILE UPLOAD ROUTES ====================

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload file"""
    # Validate file size
    if file.size > settings.max_file_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save to database
    file_upload = FileUpload(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size,
        content_type=file.content_type,
        user_id=current_user.id
    )
    db.add(file_upload)
    db.commit()
    db.refresh(file_upload)
    
    # Add URL to response
    file_upload.url = f"/uploads/{unique_filename}"
    
    return file_upload

# ==================== ADMIN ROUTES ====================

@app.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    stats = {
        "total_users": db.query(User).count(),
        "total_chats": db.query(Chat).count(),
        "total_messages": db.query(Message).count(),
        "active_users_today": db.query(User).filter(
            func.date(User.last_login) == today
        ).count(),
        "new_users_this_week": db.query(User).filter(
            User.created_at >= week_ago
        ).count()
    }
    
    return stats

@app.get("/admin/users", response_model=PaginatedResponse)
async def get_all_users(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users with pagination"""
    offset = (page - 1) * limit
    
    # Get total count
    total = db.query(User).count()
    
    # Get users with stats
    users = db.query(User).offset(offset).limit(limit).all()
    
    # Add stats to each user
    user_responses = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "total_chats": db.query(Chat).filter(Chat.user_id == user.id).count(),
            "total_messages": db.query(Message).filter(Message.user_id == user.id).count(),
            "last_activity": db.query(Message).filter(
                Message.user_id == user.id
            ).order_by(desc(Message.created_at)).first()
        }
        if user_dict["last_activity"]:
            user_dict["last_activity"] = user_dict["last_activity"].created_at
        user_responses.append(user_dict)
    
    return {
        "items": user_responses,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit)
    }

@app.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user_admin(
    user_id: int,
    user_update: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/admin/users/{user_id}")
async def delete_user_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 