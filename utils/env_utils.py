"""
Environment Utilities - Direct environment variable access
Simple utilities to read from .env file without complex configuration classes
"""

import os
import json
from typing import List, Union, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_str(key: str, default: str = "") -> str:
    """Get string environment variable"""
    return os.getenv(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """Get list environment variable (JSON format)"""
    if default is None:
        default = []
    
    try:
        value = os.getenv(key)
        if value:
            return json.loads(value)
        return default
    except (json.JSONDecodeError, TypeError):
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float environment variable"""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default

# Database settings
def get_database_url() -> str:
    """Get database URL, build from components if not provided"""
    database_url = get_env_str("DATABASE_URL")
    if database_url:
        return database_url
    
    # Build from components
    user = get_env_str("POSTGRES_USER", "postgres")
    password = get_env_str("POSTGRES_PASSWORD", "")
    host = get_env_str("POSTGRES_HOST", "localhost")
    port = get_env_int("POSTGRES_PORT", 5432)
    db = get_env_str("POSTGRES_DB", "gemini_clone_db")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Environment checks
def is_production() -> bool:
    """Check if running in production environment"""
    return get_env_str("ENVIRONMENT", "development").lower() == "production"

def is_development() -> bool:
    """Check if running in development environment"""
    return get_env_str("ENVIRONMENT", "development").lower() == "development"

def is_debug() -> bool:
    """Check if debug mode is enabled"""
    return get_env_bool("DEBUG", not is_production())

# Validation for production
def validate_production_env():
    """Validate critical environment variables in production"""
    if not is_production():
        return
    
    critical_vars = [
        ("SECRET_KEY", "your-super-secret-key-change-in-production"),
        ("ADMIN_PASSWORD", "change-in-production"),
        ("GOOGLE_API_KEY", ""),
        ("POSTGRES_PASSWORD", ""),
    ]
    
    for var_name, default_value in critical_vars:
        value = get_env_str(var_name)
        if not value or value == default_value:
            raise ValueError(f"{var_name} must be set in production environment")

# Initialize validation
validate_production_env() 