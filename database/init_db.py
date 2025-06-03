#!/usr/bin/env python3
"""
Database Initialization Script - Initialize database with admin user
Creates database tables and sets up initial admin user for the application
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from utils.env_utils import get_env_str
from database.database import init_db, get_db
from database.auth import AuthManager
from utils.models import User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create admin user if it doesn't exist"""
    try:
        # Environment variables
        admin_email = get_env_str("ADMIN_EMAIL", "admin@example.com")
        admin_password = get_env_str("ADMIN_PASSWORD", "change-in-production")
        
        # Initialize database
        init_db()
        
        # Get database session
        db = next(get_db())
        
        # Check if admin user exists
        admin_user = db.query(User).filter(
            (User.email == admin_email) | (User.username == "admin")
        ).first()
        
        if admin_user:
            logger.info(f"Admin user already exists: {admin_user.email}")
            return
        
        # Create admin user
        admin_user = AuthManager.create_user(
            db=db,
            email=admin_email,
            username="admin",
            password=admin_password,
            full_name="System Administrator",
            is_admin=True,
            is_email_verified=True
        )
        
        logger.info(f"Admin user created successfully: {admin_user.email}")
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise
    finally:
        db.close()

def main():
    """Main initialization function"""
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database tables
        init_db()
        logger.info("Database tables initialized successfully")
        
        # Create admin user
        create_admin_user()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 