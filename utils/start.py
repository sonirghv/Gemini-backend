#!/usr/bin/env python3
"""
Application Startup Script - Development server launcher
Handles application startup with proper initialization and configuration
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.env_utils import get_env_str, get_env_int, get_env_bool, is_development
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Main startup function"""
    try:
        # Environment variables
        host = get_env_str("HOST", "0.0.0.0")
        port = get_env_int("PORT", 8000)
        reload = get_env_bool("RELOAD", is_development())
        log_level = get_env_str("LOG_LEVEL", "info").lower()
        app_name = get_env_str("APP_NAME", "Gemini Clone API")
        
        logger.info(f"Starting {app_name}")
        logger.info(f"Environment: {get_env_str('ENVIRONMENT', 'development')}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Reload: {reload}")
        
        # Start the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
            reload_dirs=[str(project_root)] if reload else None,
            reload_includes=["*.py", "*.env"] if reload else None,
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 