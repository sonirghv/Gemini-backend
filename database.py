"""
Database Configuration - SQLAlchemy setup for PostgreSQL
Handles database connection, session management, and base model
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Database session dependency for FastAPI
    Ensures proper session cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database initialization
def init_db():
    """
    Initialize database tables
    Creates all tables defined in models
    """
    Base.metadata.create_all(bind=engine) 