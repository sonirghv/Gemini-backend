#!/usr/bin/env python3
"""
Database Initialization Script - Creates database and tables automatically
Handles both SQLite and PostgreSQL database creation and table schema setup
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from config import settings
from database import Base
import sys
import os

def create_postgresql_database():
    """Create PostgreSQL database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database="postgres"  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.postgres_db}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📦 Creating PostgreSQL database: {settings.postgres_db}")
            cursor.execute(f'CREATE DATABASE "{settings.postgres_db}"')
            print(f"✅ Database {settings.postgres_db} created successfully")
        else:
            print(f"✅ PostgreSQL database {settings.postgres_db} already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error with PostgreSQL: {e}")
        print("💡 Tip: Make sure PostgreSQL is running and credentials are correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_sqlite_database():
    """Create SQLite database (file will be created automatically)"""
    try:
        db_path = settings.database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"📁 Created directory: {db_dir}")
        
        print(f"📦 Using SQLite database: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up SQLite: {e}")
        return False

def create_database_if_not_exists():
    """Create database based on configuration"""
    if settings.use_sqlite:
        return create_sqlite_database()
    else:
        return create_postgresql_database()

def create_tables():
    """Create all database tables"""
    try:
        print("🔧 Creating database tables...")
        print(f"📊 Using database: {settings.database_url}")
        
        # Create engine and tables
        engine = create_engine(settings.database_url, echo=False)
        Base.metadata.create_all(bind=engine)
        
        # List created tables
        inspector = engine.dialect.get_table_names(engine.connect())
        print(f"✅ Created tables: {', '.join(['users', 'chats', 'messages', 'file_uploads', 'user_sessions'])}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing Gemini Clone Database...")
    
    db_type = "SQLite" if settings.use_sqlite else "PostgreSQL"
    print(f"🗄️  Database Type: {db_type}")
    
    # Step 1: Create database
    if not create_database_if_not_exists():
        if not settings.use_sqlite:
            print("\n💡 PostgreSQL setup failed. You can:")
            print("1. Install and start PostgreSQL")
            print("2. Or edit config.py and set use_sqlite=True for easier setup")
        print("❌ Failed to create database. Exiting...")
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables():
        print("❌ Failed to create tables. Exiting...")
        sys.exit(1)
    
    print("🎉 Database initialization completed successfully!")
    print(f"📊 Database URL: {settings.database_url}")

if __name__ == "__main__":
    main() 