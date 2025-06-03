#!/usr/bin/env python3
"""
Database Connection Test Script
Simple script to test database connectivity and identify issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.env_utils import get_database_url, get_env_str
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection"""
    try:
        # Get database URL
        database_url = get_database_url()
        logger.info(f"Testing connection to: {database_url.split('@')[-1] if '@' in database_url else 'hidden'}")
        
        # Create engine with minimal configuration
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=True
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            logger.info(f"Connection successful! Test query result: {row}")
            
            # Test database info
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            logger.info(f"Database version: {version[0] if version else 'Unknown'}")
            
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    logger.info("Starting database connection test...")
    
    # Print environment info
    logger.info(f"Environment: {get_env_str('ENVIRONMENT', 'development')}")
    
    # Test connection
    success = test_database_connection()
    
    if success:
        logger.info("Database connection test PASSED")
        sys.exit(0)
    else:
        logger.error("Database connection test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main() 