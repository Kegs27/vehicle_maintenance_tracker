from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
def get_database_url():
    """Get database URL from environment or use default SQLite"""
    # Check if we're in production (cloud) or development (local)
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # We're in production with a cloud database
        return database_url
    else:
        # We're in development, use local SQLite
        DB_PATH = "vehicle_maintenance.db"
        return f"sqlite:///{DB_PATH}"

# Get the database URL
DATABASE_URL = get_database_url()

# Create engine with appropriate configuration
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL (cloud) configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False
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
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
