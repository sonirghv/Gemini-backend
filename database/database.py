"""
Database Configuration - Production-ready SQLAlchemy setup for PostgreSQL
Handles database connection, session management, connection pooling, and base model
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from utils.env_utils import (
    get_database_url, get_env_int, get_env_str, 
    is_production, is_development, is_debug
)
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
DB_POOL_SIZE = get_env_int("DB_POOL_SIZE", 20)
DB_MAX_OVERFLOW = get_env_int("DB_MAX_OVERFLOW", 30)
DB_POOL_TIMEOUT = get_env_int("DB_POOL_TIMEOUT", 30)
DB_POOL_RECYCLE = get_env_int("DB_POOL_RECYCLE", 3600)
APP_NAME = get_env_str("APP_NAME", "Gemini Clone API")
ENVIRONMENT = get_env_str("ENVIRONMENT", "development")

# Database engine configuration with production-ready settings
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": DB_POOL_RECYCLE,
    "echo": is_debug(),
    "poolclass": QueuePool,
    "pool_size": DB_POOL_SIZE,
    "max_overflow": DB_MAX_OVERFLOW,
    "pool_timeout": DB_POOL_TIMEOUT,
    "connect_args": {
        "connect_timeout": 10,
        "application_name": APP_NAME,
    }
}

# Create database engine
try:
    engine = create_engine(get_database_url(), **engine_kwargs)
    logger.info(f"Database engine created successfully for {ENVIRONMENT} environment")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Add connection event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set PostgreSQL connection parameters"""
    database_url = get_database_url()
    if "postgresql" in database_url:
        with dbapi_connection.cursor() as cursor:
            # Set timezone to UTC
            cursor.execute("SET timezone TO 'UTC'")
            # Set statement timeout (30 seconds)
            cursor.execute("SET statement_timeout = '30s'")
            # Set lock timeout (10 seconds)
            cursor.execute("SET lock_timeout = '10s'")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout for monitoring"""
    if is_debug():
        logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin for monitoring"""
    if is_debug():
        logger.debug("Connection checked in to pool")

# Create session factory with proper configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Create base class for models
Base = declarative_base()

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def get_db_session() -> Session:
        """Get a new database session"""
        return SessionLocal()
    
    @staticmethod
    def check_connection() -> bool:
        """Check database connection health"""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    @staticmethod
    def get_connection_info() -> dict:
        """Get database connection information"""
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

# Dependency to get database session with proper error handling
def get_db():
    """
    Database session dependency for FastAPI
    Ensures proper session cleanup and error handling
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Database initialization with retry logic
def init_db(max_retries: int = 3, retry_delay: int = 5):
    """
    Initialize database tables with retry logic
    Creates all tables defined in models
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing database (attempt {attempt + 1}/{max_retries})")
            
            # Check connection first
            if not DatabaseManager.check_connection():
                raise Exception("Database connection failed")
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All database initialization attempts failed")
                raise Exception(f"Failed to initialize database after {max_retries} attempts: {e}")

# Database health check
def health_check() -> dict:
    """
    Comprehensive database health check
    Returns status and connection information
    """
    try:
        start_time = time.time()
        is_healthy = DatabaseManager.check_connection()
        response_time = time.time() - start_time
        
        connection_info = DatabaseManager.get_connection_info()
        
        database_url = get_database_url()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time_ms": round(response_time * 1000, 2),
            "connection_pool": connection_info,
            "database_url": database_url.split("@")[-1] if "@" in database_url else "hidden",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Transaction context manager
class DatabaseTransaction:
    """Context manager for database transactions"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.should_close = db is None
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.db.commit()
            else:
                self.db.rollback()
                logger.error(f"Transaction rolled back due to: {exc_val}")
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            self.db.rollback()
        finally:
            if self.should_close:
                self.db.close() 