#!/usr/bin/env python3
"""
Environment Variables Test Script
Test script to verify environment variable loading and database URL construction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.env_utils import (
    get_env_str, get_env_int, get_env_bool, 
    get_database_url, is_production, is_development
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test environment variable loading"""
    logger.info("Testing environment variable loading...")
    
    # Test basic environment variables
    env_vars = [
        ("APP_NAME", get_env_str("APP_NAME", "default")),
        ("ENVIRONMENT", get_env_str("ENVIRONMENT", "default")),
        ("DEBUG", get_env_bool("DEBUG", False)),
        ("PORT", get_env_int("PORT", 8000)),
        ("DATABASE_URL", get_env_str("DATABASE_URL", "")),
        ("POSTGRES_USER", get_env_str("POSTGRES_USER", "")),
        ("POSTGRES_PASSWORD", get_env_str("POSTGRES_PASSWORD", "")),
        ("POSTGRES_HOST", get_env_str("POSTGRES_HOST", "")),
        ("POSTGRES_PORT", get_env_int("POSTGRES_PORT", 5432)),
        ("POSTGRES_DB", get_env_str("POSTGRES_DB", "")),
    ]
    
    for var_name, value in env_vars:
        if var_name in ["POSTGRES_PASSWORD", "DATABASE_URL"] and value:
            logger.info(f"{var_name}: {'*' * len(str(value))}")  # Hide sensitive values
        else:
            logger.info(f"{var_name}: {value}")
    
    # Test environment checks
    logger.info(f"is_production(): {is_production()}")
    logger.info(f"is_development(): {is_development()}")
    
    # Test database URL construction
    try:
        database_url = get_database_url()
        # Hide password in URL for logging
        if "@" in database_url:
            parts = database_url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split(":")
                if len(user_pass) >= 3:  # postgresql://user:pass
                    masked_url = f"{user_pass[0]}:{user_pass[1]}:***@{parts[1]}"
                else:
                    masked_url = f"{parts[0]}@{parts[1]}"
            else:
                masked_url = database_url
        else:
            masked_url = database_url
        
        logger.info(f"Constructed database URL: {masked_url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to construct database URL: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting environment variables test...")
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        logger.info(f".env file found at: {env_file}")
    else:
        logger.warning(f".env file not found at: {env_file}")
    
    # Test environment variables
    success = test_environment_variables()
    
    if success:
        logger.info("Environment variables test PASSED")
        sys.exit(0)
    else:
        logger.error("Environment variables test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main() 