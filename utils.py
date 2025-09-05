"""
Utility functions for Vehicle Maintenance Tracker
This module contains common operations used across multiple routes
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from sqlmodel import Session
from database import SessionLocal

def get_db_session() -> Session:
    """Get a database session with proper error handling"""
    try:
        return SessionLocal()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def safe_commit(session: Session, error_message: str = "Database operation failed") -> None:
    """Safely commit a database session with error handling"""
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )

def format_error_response(error: str, status_code: int = 500) -> Dict[str, Any]:
    """Format a standardized error response"""
    return {
        "success": False,
        "error": error,
        "status_code": status_code
    }

def format_success_response(data: Any = None, message: str = "Operation completed successfully") -> Dict[str, Any]:
    """Format a standardized success response"""
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return response

def parse_date_safe(date_string: str) -> Optional[str]:
    """Safely parse date string, returning None if invalid"""
    if not date_string:
        return None
    
    try:
        from datetime import datetime
        # Try MM/DD/YYYY format first
        datetime.strptime(date_string, "%m/%d/%Y")
        return date_string
    except ValueError:
        try:
            # Try YYYY-MM-DD format
            datetime.strptime(date_string, "%Y-%m-%d")
            return date_string
        except ValueError:
            return None

def validate_file_upload(file, max_size_mb: int = 10, allowed_types: list = None) -> Dict[str, Any]:
    """Validate file upload with size and type checks"""
    if not file:
        return format_error_response("No file provided")
    
    # Check file size
    if file.size > max_size_mb * 1024 * 1024:
        return format_error_response(f"File size must be less than {max_size_mb}MB")
    
    # Check file type if specified
    if allowed_types and file.content_type not in allowed_types:
        return format_error_response(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    return format_success_response()

def log_operation(operation: str, details: str = "", level: str = "INFO") -> None:
    """Log operations with consistent formatting"""
    import logging
    logger = logging.getLogger(__name__)
    
    message = f"[{level}] {operation}"
    if details:
        message += f" - {details}"
    
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)
