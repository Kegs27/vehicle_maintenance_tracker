"""
Database utilities for consistent session management and error handling.
"""
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from contextlib import contextmanager
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from models import Vehicle, MaintenanceRecord, FutureMaintenance

T = TypeVar('T')

@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to automatically manage database sessions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_session() as session:
            return func(session, *args, **kwargs)
    return wrapper

def with_db_session_manual(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for functions that need manual session control."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    return wrapper

def handle_db_errors(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    """Decorator for consistent error handling in database operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            print(f"Database error in {func.__name__}: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error in {func.__name__}: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    return wrapper

# Common query patterns
def get_vehicle_by_id(session: Session, vehicle_id: int) -> Optional[Vehicle]:
    """Get a vehicle by ID with eager loading."""
    return session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id)
    ).scalar_one_or_none()

def get_maintenance_by_id(session: Session, record_id: int) -> Optional[MaintenanceRecord]:
    """Get a maintenance record by ID with eager loading."""
    return session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.id == record_id)
    ).scalar_one_or_none()

def get_future_maintenance_by_id(session: Session, future_maintenance_id: int) -> Optional[FutureMaintenance]:
    """Get a future maintenance record by ID."""
    return session.execute(
        select(FutureMaintenance).where(FutureMaintenance.id == future_maintenance_id)
    ).scalar_one_or_none()

def verify_vehicle_exists(session: Session, vehicle_id: int) -> bool:
    """Verify that a vehicle exists."""
    return get_vehicle_by_id(session, vehicle_id) is not None

def verify_maintenance_exists(session: Session, record_id: int) -> bool:
    """Verify that a maintenance record exists."""
    return get_maintenance_by_id(session, record_id) is not None
