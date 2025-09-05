# Standard library imports
import os
from pathlib import Path

# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
def get_database_url():
    """Get database URL from environment or use default SQLite"""
    # Check if we're in production (cloud) or development (local)
    database_url = os.getenv("DATABASE_URL")
    # Debug logging
    print(f"Environment check - DATABASE_URL: {'SET' if database_url else 'NOT SET'}")
    if database_url:
        print(f"Using PostgreSQL: {database_url[:20]}...")  # Show first 20 chars for security
    else:
        print("Using SQLite fallback")
    
    if database_url:
        # We're in production with a cloud database
        return database_url
    else:
        # We're in development, use local SQLite
        # Get the current working directory and create a proper path
        current_dir = Path.cwd()
        if current_dir.name == "app":
            # If we're in the app directory, go up one level
            db_path = current_dir.parent / "vehicle_maintenance.db"
        else:
            # If we're in the root directory
            db_path = current_dir / "vehicle_maintenance.db"
        
        return f"sqlite:///{db_path}"

# Get the database URL
DATABASE_URL = get_database_url()

# Create engine with appropriate configuration
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL (cloud) configuration - convert to asyncpg format
    # Replace postgresql:// with postgresql+asyncpg:// for asyncpg compatibility
    asyncpg_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_engine(
        asyncpg_url,
        echo=False,
        pool_pre_ping=True,  # Better connection handling
        pool_recycle=300      # Recycle connections every 5 minutes
    )
else:
    # SQLite (local) configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables"""
    try:
        SQLModel.metadata.create_all(engine)
        print(f"Database initialized successfully: {DATABASE_URL}")
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Don't crash the app if database init fails
        # This allows the app to start even if there are DB issues

def get_session():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
