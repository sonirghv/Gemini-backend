#!/usr/bin/env python3
"""
Startup Script - Initialize database and run FastAPI server
Handles database creation, admin user setup, and server startup
"""

import uvicorn
import asyncio
from database import get_db
from models import User
from auth import AuthManager
from config import settings
from init_db import main as init_database

def setup_admin_user():
    """Create admin user if not exists"""
    print("👤 Setting up admin user...")
    db = next(get_db())
    try:
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
            print(f"✅ Admin user created: {settings.admin_email}")
        else:
            print(f"✅ Admin user already exists: {settings.admin_email}")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
    finally:
        db.close()

def main():
    """Main startup function"""
    print("🚀 Starting Gemini Clone Backend...")
    print(f"📊 App: {settings.app_name} v{settings.version}")
    print(f"🔗 Database: {settings.database_url}")
    print(f"🔑 Admin Email: {settings.admin_email}")
    
    # Step 1: Initialize database (create database and tables)
    try:
        init_database()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Step 2: Setup admin user
    setup_admin_user()
    
    print("🌐 Starting FastAPI server...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🎯 Frontend URL: http://localhost:5173")
    print("\n" + "="*50)
    print("🎉 Server is ready! You can now:")
    print("1. Visit http://localhost:5173 for the frontend")
    print("2. Login with admin@geminiclone.com / admin123")
    print("3. Check API docs at http://localhost:8000/docs")
    print("="*50 + "\n")
    
    # Start server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )

if __name__ == "__main__":
    main() 