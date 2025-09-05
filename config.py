"""
Configuration settings for Vehicle Maintenance Tracker
"""

import os
from typing import Optional

class Config:
    """Application configuration"""
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    SQLITE_DB_PATH: str = "vehicle_maintenance.db"
    
    # File upload settings
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: list = ["application/pdf", "image/jpeg", "image/png"]
    UPLOAD_DIR: str = "uploads"
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Date formats
    DATE_FORMAT_DISPLAY: str = "%m/%d/%Y"
    DATE_FORMAT_DATABASE: str = "%Y-%m-%d"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Maintenance intervals (in miles)
    DEFAULT_OIL_CHANGE_INTERVAL: int = 5000
    DEFAULT_TIRE_ROTATION_INTERVAL: int = 10000
    DEFAULT_BRAKE_INSPECTION_INTERVAL: int = 15000
    
    # Reminder settings
    DEFAULT_MILEAGE_REMINDER: int = 500
    DEFAULT_DATE_REMINDER: int = 30
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with fallback to SQLite"""
        return cls.DATABASE_URL or f"sqlite:///{cls.SQLITE_DB_PATH}"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return not cls.DEBUG
    
    @classmethod
    def get_upload_path(cls) -> str:
        """Get upload directory path"""
        return os.path.join(os.getcwd(), cls.UPLOAD_DIR)
    
    @classmethod
    def ensure_upload_dir(cls) -> None:
        """Ensure upload directory exists"""
        upload_path = cls.get_upload_path()
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
