"""
Main FastAPI Application - Production-ready Gemini Clone Backend
Comprehensive backend with authentication, chat, admin, file upload, and monitoring
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import uuid
import shutil
import time
from datetime import datetime, timedelta
import math

# Local imports
from utils.env_utils import (
    get_env_str, get_env_int, get_env_bool, get_env_list,
    is_production, is_development, is_debug
)
from database.database import get_db, init_db, health_check as db_health_check, DatabaseManager
from utils.models import User, Chat, Message, FileUpload
from database.schemas import *
from database.auth import AuthManager, get_current_user, get_current_active_user, get_current_admin_user
from utils.gemini_service import gemini_service
from utils.otp_service import otp_service
from utils.email_service import email_service
from utils.logging_config import get_logger, log_request, log_response, log_error, log_security_event
from utils.rate_limit_service import rate_limit_service, cache_service

# Initialize logger
logger = get_logger(__name__)

# Environment variables
APP_NAME = get_env_str("APP_NAME", "Gemini Clone API")
VERSION = get_env_str("VERSION", "1.0.0")
ENVIRONMENT = get_env_str("ENVIRONMENT", "development")
ADMIN_EMAIL = get_env_str("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = get_env_str("ADMIN_PASSWORD", "change-in-production")
ALLOWED_ORIGINS = get_env_list("ALLOWED_ORIGINS", ["http://localhost:3000", "http://localhost:5173"])
UPLOAD_DIR = get_env_str("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = get_env_int("MAX_FILE_SIZE", 10485760)
RATE_LIMIT_REQUESTS = get_env_int("RATE_LIMIT_REQUESTS", 100)
RATE_LIMIT_WINDOW = get_env_int("RATE_LIMIT_WINDOW", 3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with comprehensive startup and shutdown"""
    try:
        logger.info(f"Starting {APP_NAME} v{VERSION} in {ENVIRONMENT} mode")
        
        # Initialize database
        init_db()
        db = next(get_db())
        
        # Create admin user if not exists
        admin_user_by_email = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        admin_user_by_username = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user_by_email and not admin_user_by_username:
            AuthManager.create_user(
                db=db,
                email=ADMIN_EMAIL,
                username="admin",
                password=ADMIN_PASSWORD,
                full_name="System Administrator",
                is_admin=True,
                is_email_verified=True
            )
            logger.info(f"Admin user created: {ADMIN_EMAIL}")
        elif admin_user_by_email:
            logger.info(f"Admin user already exists with email: {ADMIN_EMAIL}")
        elif admin_user_by_username:
            logger.info(f"Admin user already exists with username: admin")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f'Error during startup: {e}')
        raise RuntimeError('Failed to initialize application')
    
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")

# Initialize FastAPI app with production settings
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Production-ready backend API for Gemini Clone with authentication, chat, and monitoring",
    lifespan=lifespan,
    docs_url="/docs" if is_debug() else None,
    redoc_url="/redoc" if is_debug() else None,
    openapi_url="/openapi.json" if is_debug() else None,
)

# Security middleware
if is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domains in production
    )

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests and responses"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Get client IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Log request
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        ip_address=client_ip
    )
    
    # Add request ID to request state
    request.state.request_id = request_id
    request.state.start_time = start_time
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        log_response(
            request_id=request_id,
            status_code=response.status_code,
            response_time=process_time
        )
        
        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        log_error(e, {"request_id": request_id, "path": request.url.path})
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id}
        )

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware using in-memory storage"""
    # Get client identifier
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Check rate limit
    identifier = f"ip:{client_ip}"
    if rate_limit_service.is_rate_limited(
        identifier, 
        RATE_LIMIT_REQUESTS, 
        RATE_LIMIT_WINDOW
    ):
        log_security_event(
            "rate_limit_exceeded",
            ip_address=client_ip,
            details={"path": request.url.path}
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    return await call_next(request)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": VERSION,
        "environment": ENVIRONMENT,
        "services": {}
    }
    
    # Database health
    db_health = db_health_check()
    health_status["services"]["database"] = db_health
    
    # Rate limiting service health
    rate_limit_stats = rate_limit_service.get_stats()
    health_status["services"]["rate_limiting"] = {
        "status": "healthy",
        "stats": rate_limit_stats
    }
    
    # Cache service health
    cache_stats = cache_service.get_stats()
    health_status["services"]["cache"] = {
        "status": "healthy",
        "stats": cache_stats
    }
    
    # Overall status
    if db_health["status"] != "healthy":
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/health/database")
async def database_health():
    """Database-specific health check"""
    return db_health_check()

# Metrics endpoint (for monitoring)
@app.get("/metrics")
async def metrics():
    """Application metrics endpoint"""
    if not is_debug():
        raise HTTPException(status_code=404, detail="Not found")
    
    db_info = DatabaseManager.get_connection_info()
    rate_limit_stats = rate_limit_service.get_stats()
    cache_stats = cache_service.get_stats()
    
    return {
        "database": db_info,
        "rate_limiting": rate_limit_stats,
        "cache": cache_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== AUTHENTICATION ROUTES ====================

@app.post("/auth/send-otp", response_model=OTPResponse)
async def send_otp_for_registration(otp_request: OTPRequest, request: Request, db: Session = Depends(get_db)):
    """Send OTP for email verification during registration"""
    try:
        # Check if email is already registered
        existing_user = db.query(User).filter(User.email == otp_request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create and send OTP
        otp_code, email_sent = otp_service.create_otp_verification(
            db=db, 
            email=otp_request.email, 
            purpose=otp_request.purpose
        )
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        
        # Cache OTP attempt for rate limiting
        cache_service.increment(f"otp_attempts:{otp_request.email}")
        
        return OTPResponse(
            success=True,
            message="OTP sent successfully to your email address",
            remaining_seconds=600
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle rate limiting and validation errors
        error_message = str(e)
        if "wait" in error_message.lower() and "seconds" in error_message.lower():
            # This is a rate limiting error
            raise HTTPException(status_code=429, detail=error_message)
        else:
            # Other validation errors
            raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        log_error(e, {"email": otp_request.email, "request_id": getattr(request.state, "request_id", None)})
        raise HTTPException(status_code=500, detail=f'Failed to send OTP: {str(e)}')

@app.post("/auth/verify-otp", response_model=OTPResponse)
async def verify_otp_code(otp_verification: OTPVerification, request: Request, db: Session = Depends(get_db)):
    """Verify OTP code"""
    try:
        is_valid, message, otp_record = otp_service.verify_otp(
            db=db,
            email=otp_verification.email,
            otp_code=otp_verification.otp_code,
            purpose=otp_verification.purpose
        )
        
        if not is_valid:
            remaining_attempts = 0
            if otp_record:
                remaining_attempts = max(0, otp_record.max_attempts - otp_record.attempts)
            
            # Log security event for failed OTP
            log_security_event(
                "otp_verification_failed",
                details={
                    "email": otp_verification.email,
                    "remaining_attempts": remaining_attempts
                }
            )
            
            return OTPResponse(
                success=False,
                message=message,
                remaining_attempts=remaining_attempts
            )
        
        return OTPResponse(
            success=True,
            message=message
        )
        
    except Exception as e:
        log_error(e, {"email": otp_verification.email, "request_id": getattr(request.state, "request_id", None)})
        raise HTTPException(status_code=500, detail=f'OTP verification failed: {str(e)}')

@app.post("/auth/resend-otp", response_model=OTPResponse)
async def resend_otp_code(resend_request: ResendOTPRequest, request: Request, db: Session = Depends(get_db)):
    """Resend OTP code with rate limiting"""
    try:
        # Check rate limiting for OTP resend
        attempts = cache_service.get(f"otp_resend:{resend_request.email}", 0)
        if attempts >= 3:  # Max 3 resends per hour
            raise HTTPException(status_code=429, detail="Too many OTP resend attempts")
        
        success, message = otp_service.resend_otp(
            db=db,
            email=resend_request.email,
            purpose=resend_request.purpose
        )
        
        if success:
            cache_service.set(f"otp_resend:{resend_request.email}", attempts + 1, expire=3600)
        
        return OTPResponse(
            success=success,
            message=message,
            remaining_seconds=600 if success else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"email": resend_request.email, "request_id": getattr(request.state, "request_id", None)})
        raise HTTPException(status_code=500, detail=f'Failed to resend OTP: {str(e)}')

@app.get("/auth/otp-status/{email}", response_model=OTPStatusResponse)
async def get_otp_status(email: str, purpose: str = "email_verification", db: Session = Depends(get_db)):
    """Get OTP status for an email"""
    try:
        status_info = otp_service.get_otp_status(db=db, email=email, purpose=purpose)
        return OTPStatusResponse(**status_info)
        
    except Exception as e:
        log_error(e, {"email": email})
        raise HTTPException(status_code=500, detail=f'Failed to get OTP status: {str(e)}')

@app.post("/auth/register", response_model=Token)
async def register_with_otp(registration_data: CompleteRegistration, request: Request, db: Session = Depends(get_db)):
    """Complete user registration after OTP verification"""
    try:
        # Verify OTP first
        is_valid, message, otp_record = otp_service.verify_otp(
            db=db,
            email=registration_data.email,
            otp_code=registration_data.otp_code,
            purpose="email_verification"
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Check if email matches user data
        if registration_data.email != registration_data.user_data.email:
            raise HTTPException(status_code=400, detail="Email mismatch in registration data")
        
        # Create user with verified email
        user = AuthManager.create_user(
            db=db,
            email=registration_data.user_data.email,
            username=registration_data.user_data.username,
            password=registration_data.user_data.password,
            full_name=registration_data.user_data.full_name,
            is_email_verified=True
        )
        
        # Create access token
        access_token = AuthManager.create_access_token(data={"sub": user.email})
        
        # Cache user session
        cache_service.set(f"session:user:{user.id}", {
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin
        }, expire=3600)
        
        logger.info(f"New user registered: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {"email": registration_data.email, "request_id": getattr(request.state, "request_id", None)})
        raise HTTPException(status_code=500, detail=f'Registration failed: {str(e)}')

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
    
    # Check if email is verified
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email address before logging in"
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
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Validate file type
    allowed_types = get_env_list("ALLOWED_FILE_TYPES", ["image/jpeg", "image/png", "image/gif", "image/webp"])
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
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