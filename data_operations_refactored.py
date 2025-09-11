"""
Refactored data operations with improved session management and error handling.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlmodel import select, delete
from sqlalchemy.orm import selectinload

from database_utils import (
    with_db_session, with_db_session_manual, handle_db_errors,
    get_vehicle_by_id, get_maintenance_by_id, get_future_maintenance_by_id,
    verify_vehicle_exists, verify_maintenance_exists
)
from models import Vehicle, MaintenanceRecord, FutureMaintenance
from importer import import_csv, ImportResult
import csv
from io import StringIO

# ============================================================================
# VEHICLE OPERATIONS
# ============================================================================

@with_db_session
@handle_db_errors
def get_all_vehicles(session) -> Dict[str, Any]:
    """Get all vehicles ordered by name with maintenance records eagerly loaded."""
    try:
        vehicles = session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.maintenance_records))
            .order_by(Vehicle.name)
        ).scalars().all()
        return {"success": True, "vehicles": list(vehicles)}
    except Exception as e:
        return {"success": False, "error": str(e), "vehicles": []}

@with_db_session
@handle_db_errors
def get_vehicle_by_id_safe(session, vehicle_id: int) -> Dict[str, Any]:
    """Get a specific vehicle by ID."""
    try:
        vehicle = get_vehicle_by_id(session, vehicle_id)
        if vehicle:
            return {"success": True, "vehicle": vehicle}
        else:
            return {"success": False, "error": "Vehicle not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@with_db_session_manual
@handle_db_errors
def create_vehicle(session, name: str, make: str, model: str, year: int, vin: str) -> Dict[str, Any]:
    """Create a new vehicle with duplicate checking."""
    # Check for duplicate name
    existing = session.execute(
        select(Vehicle).where(Vehicle.name == name)
    ).scalar_one_or_none()
    
    if existing:
        return {"success": False, "error": f"Vehicle with name '{name}' already exists"}
    
    # Check for duplicate VIN if provided
    if vin and vin.strip():
        existing_vin = session.execute(
            select(Vehicle).where(Vehicle.vin == vin)
        ).scalar_one_or_none()
        
        if existing_vin:
            return {"success": False, "error": f"Vehicle with VIN '{vin}' already exists"}
    
    vehicle = Vehicle(name=name, make=make, model=model, year=year, vin=vin)
    session.add(vehicle)
    session.refresh(vehicle)
    
    return {"success": True, "vehicle": vehicle}

@with_db_session_manual
@handle_db_errors
def update_vehicle(session, vehicle_id: int, name: str, make: str, model: str, year: int, vin: str) -> Dict[str, Any]:
    """Update an existing vehicle with duplicate checking."""
    vehicle = get_vehicle_by_id(session, vehicle_id)
    if not vehicle:
        return {"success": False, "error": "Vehicle not found"}
    
    # Check for duplicate name (excluding current vehicle)
    existing = session.execute(
        select(Vehicle).where(Vehicle.name == name, Vehicle.id != vehicle_id)
    ).scalar_one_or_none()
    
    if existing:
        return {"success": False, "error": f"Vehicle with name '{name}' already exists"}
    
    # Check for duplicate VIN if provided (excluding current vehicle)
    if vin and vin.strip():
        existing_vin = session.execute(
            select(Vehicle).where(Vehicle.vin == vin, Vehicle.id != vehicle_id)
        ).scalar_one_or_none()
        
        if existing_vin:
            return {"success": False, "error": f"Vehicle with VIN '{vin}' already exists"}
    
    # Update vehicle
    vehicle.name = name
    vehicle.make = make
    vehicle.model = model
    vehicle.year = year
    vehicle.vin = vin
    
    session.refresh(vehicle)
    return {"success": True, "vehicle": vehicle}

@with_db_session_manual
@handle_db_errors
def delete_vehicle(session, vehicle_id: int) -> Dict[str, Any]:
    """Delete a vehicle and all its maintenance records."""
    vehicle = get_vehicle_by_id(session, vehicle_id)
    if not vehicle:
        return {"success": False, "error": "Vehicle not found"}
    
    # Delete all maintenance records for this vehicle
    session.execute(delete(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id))
    
    # Delete the vehicle
    session.delete(vehicle)
    
    return {"success": True}

# ============================================================================
# MAINTENANCE OPERATIONS
# ============================================================================

@with_db_session
@handle_db_errors
def get_all_maintenance_records(session) -> Dict[str, Any]:
    """Get all maintenance records with vehicle information."""
    try:
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .order_by(MaintenanceRecord.date.desc())
        ).scalars().all()
        return {"success": True, "records": list(records)}
    except Exception as e:
        return {"success": False, "error": str(e), "records": []}

@with_db_session
@handle_db_errors
def get_maintenance_records_by_vehicle(session, vehicle_id: int) -> Dict[str, Any]:
    """Get maintenance records for a specific vehicle ordered by date (newest first)."""
    try:
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .where(MaintenanceRecord.vehicle_id == vehicle_id)
            .order_by(MaintenanceRecord.date.desc())
        ).scalars().all()
        return {"success": True, "records": list(records)}
    except Exception as e:
        return {"success": False, "error": str(e), "records": []}

@with_db_session
@handle_db_errors
def get_maintenance_by_id_safe(session, record_id: int) -> Dict[str, Any]:
    """Get a specific maintenance record by ID."""
    try:
        record = get_maintenance_by_id(session, record_id)
        if record:
            return {"success": True, "record": record}
        else:
            return {"success": False, "error": "Maintenance record not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@with_db_session_manual
@handle_db_errors
def create_maintenance_record(session, vehicle_id: int, date_str: str, description: Optional[str], 
                            cost: Optional[float], mileage: Optional[int], 
                            oil_change_interval: Optional[int] = None,
                            is_oil_change: Optional[bool] = None,
                            oil_type: Optional[str] = None,
                            oil_brand: Optional[str] = None,
                            oil_filter_brand: Optional[str] = None,
                            oil_filter_part_number: Optional[str] = None,
                            oil_cost: Optional[float] = None,
                            filter_cost: Optional[float] = None,
                            labor_cost: Optional[float] = None,
                            photo_path: Optional[str] = None,
                            photo_description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new maintenance record."""
    # Verify vehicle exists
    if not verify_vehicle_exists(session, vehicle_id):
        return {"success": False, "error": "Vehicle not found"}
    
    # Parse date
    try:
        if "/" in date_str:
            month, day, year = date_str.split("/")
            maintenance_date = date(int(year), int(month), int(day))
        else:
            maintenance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"success": False, "error": "Invalid date format"}
    
    # Create maintenance record
    # Ensure description is never None for database compatibility
    safe_description = description if description and description.strip() else "N/A"
    
    record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        date=maintenance_date,
        description=safe_description,
        cost=cost,
        mileage=mileage,
        oil_change_interval=oil_change_interval,
        is_oil_change=is_oil_change,
        oil_type=oil_type,
        oil_brand=oil_brand,
        oil_filter_brand=oil_filter_brand,
        oil_filter_part_number=oil_filter_part_number,
        oil_cost=oil_cost,
        filter_cost=filter_cost,
        labor_cost=labor_cost,
        photo_path=photo_path,
        photo_description=photo_description
    )
    
    session.add(record)
    session.refresh(record)
    
    return {"success": True, "record": record}

@with_db_session_manual
@handle_db_errors
def update_maintenance_record(session, record_id: int, vehicle_id: int, date_str: str, 
                            description: Optional[str], cost: Optional[float], mileage: Optional[int],
                            oil_change_interval: Optional[int] = None,
                            is_oil_change: Optional[bool] = None,
                            oil_type: Optional[str] = None,
                            oil_brand: Optional[str] = None,
                            oil_filter_brand: Optional[str] = None,
                            oil_filter_part_number: Optional[str] = None,
                            oil_cost: Optional[float] = None,
                            filter_cost: Optional[float] = None,
                            labor_cost: Optional[float] = None,
                            photo_path: Optional[str] = None,
                            photo_description: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing maintenance record."""
    record = get_maintenance_by_id(session, record_id)
    if not record:
        return {"success": False, "error": "Maintenance record not found"}
    
    # Verify vehicle exists
    if not verify_vehicle_exists(session, vehicle_id):
        return {"success": False, "error": "Vehicle not found"}
    
    # Parse date
    try:
        if "/" in date_str:
            month, day, year = date_str.split("/")
            maintenance_date = date(int(year), int(month), int(day))
        else:
            maintenance_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"success": False, "error": "Invalid date format"}
    
    # Update record
    # Ensure description is never None for database compatibility
    safe_description = description if description and description.strip() else "N/A"
    
    record.vehicle_id = vehicle_id
    record.date = maintenance_date
    record.description = safe_description
    record.cost = cost
    record.mileage = mileage
    record.oil_change_interval = oil_change_interval
    record.is_oil_change = is_oil_change
    record.oil_type = oil_type
    record.oil_brand = oil_brand
    record.oil_filter_brand = oil_filter_brand
    record.oil_filter_part_number = oil_filter_part_number
    record.oil_cost = oil_cost
    record.filter_cost = filter_cost
    record.labor_cost = labor_cost
    record.photo_path = photo_path
    record.photo_description = photo_description
    
    session.refresh(record)
    return {"success": True, "record": record}

@with_db_session_manual
@handle_db_errors
def delete_maintenance_record(session, record_id: int) -> Dict[str, Any]:
    """Delete a maintenance record."""
    record = get_maintenance_by_id(session, record_id)
    if not record:
        return {"success": False, "error": "Maintenance record not found"}
    
    session.delete(record)
    return {"success": True}

# ============================================================================
# FUTURE MAINTENANCE OPERATIONS
# ============================================================================

@with_db_session
@handle_db_errors
def get_all_future_maintenance(session) -> Dict[str, Any]:
    """Get all future maintenance reminders with vehicle information."""
    try:
        future_maintenance = session.execute(
            select(FutureMaintenance, Vehicle)
            .join(Vehicle, FutureMaintenance.vehicle_id == Vehicle.id)
            .where(FutureMaintenance.is_active == True)
            .order_by(FutureMaintenance.target_date)
        ).all()
        
        result = []
        for fm, vehicle in future_maintenance:
            result.append({
                'id': fm.id,
                'vehicle_id': fm.vehicle_id,
                'vehicle_name': vehicle.name,
                'vehicle_year': vehicle.year,
                'vehicle_make': vehicle.make,
                'vehicle_model': vehicle.model,
                'maintenance_type': fm.maintenance_type,
                'target_mileage': fm.target_mileage,
                'target_date': fm.target_date,
                'mileage_reminder': fm.mileage_reminder,
                'date_reminder': fm.date_reminder,
                'estimated_cost': fm.estimated_cost,
                'notes': fm.notes,
                'is_recurring': fm.is_recurring,
                'recurrence_interval_miles': fm.recurrence_interval_miles,
                'recurrence_interval_months': fm.recurrence_interval_months,
                'parts_link': fm.parts_link,
                'created_at': fm.created_at,
                'updated_at': fm.updated_at
            })
        
        return {"success": True, "future_maintenance": result}
    except Exception as e:
        return {"success": False, "error": str(e), "future_maintenance": []}

@with_db_session
@handle_db_errors
def get_future_maintenance_by_id_safe(session, future_maintenance_id: int) -> Dict[str, Any]:
    """Get a specific future maintenance record by ID."""
    try:
        future_maintenance = get_future_maintenance_by_id(session, future_maintenance_id)
        if future_maintenance:
            return {"success": True, "future_maintenance": future_maintenance}
        else:
            return {"success": False, "error": "Future maintenance record not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@with_db_session_manual
@handle_db_errors
def mark_future_maintenance_completed(session, future_maintenance_id: int) -> Dict[str, Any]:
    """Mark a future maintenance record as completed (inactive)."""
    future_maintenance = get_future_maintenance_by_id(session, future_maintenance_id)
    if not future_maintenance:
        return {"success": False, "error": "Future maintenance record not found"}
    
    # Mark as inactive (completed)
    future_maintenance.is_active = False
    
    return {"success": True, "message": "Future maintenance record marked as completed"}

# ============================================================================
# SUMMARY AND STATISTICS
# ============================================================================

@with_db_session
@handle_db_errors
def get_maintenance_summary(session) -> Dict[str, Any]:
    """Get maintenance summary statistics."""
    try:
        # Get total vehicles
        total_vehicles = session.execute(select(Vehicle)).scalars().all()
        total_vehicles_count = len(total_vehicles)
        
        # Get total maintenance records
        total_records = session.execute(select(MaintenanceRecord)).scalars().all()
        total_records_count = len(total_records)
        
        # Calculate total cost
        total_cost = sum(record.cost for record in total_records if record.cost)
        
        # Calculate average cost
        avg_cost = total_cost / total_records_count if total_records_count > 0 else 0
        
        return {
            "success": True,
            "summary": {
                "total_vehicles": total_vehicles_count,
                "total_records": total_records_count,
                "total_cost": total_cost,
                "avg_cost": avg_cost
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "summary": {}}

# ============================================================================
# IMPORT/EXPORT OPERATIONS
# ============================================================================

@with_db_session_manual
@handle_db_errors
def import_csv_data(session, file_content: str, vehicle_id: int = None) -> Dict[str, Any]:
    """Import CSV data with centralized logic."""
    try:
        if vehicle_id is None:
            return {"success": False, "error": "Vehicle ID is required for import"}
        
        # Verify vehicle exists
        if not verify_vehicle_exists(session, vehicle_id):
            return {"success": False, "error": "Selected vehicle not found"}
        
        # Use the importer module
        result = import_csv(file_content, vehicle_id)
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@with_db_session
@handle_db_errors
def export_vehicles_csv(session, vehicle_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Export vehicles to CSV format."""
    try:
        if vehicle_ids:
            vehicles = session.execute(
                select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
            ).scalars().all()
        else:
            vehicles = session.execute(select(Vehicle)).scalars().all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['id', 'name', 'year', 'make', 'model', 'vin'])
        
        # Write data
        for vehicle in vehicles:
            writer.writerow([
                vehicle.id,
                vehicle.name,
                vehicle.year,
                vehicle.make,
                vehicle.model,
                vehicle.vin or ''
            ])
        
        return {"success": True, "csv_content": output.getvalue()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@with_db_session
@handle_db_errors
def export_maintenance_csv(session, vehicle_id: Optional[int] = None) -> Dict[str, Any]:
    """Export maintenance records to CSV format."""
    try:
        if vehicle_id:
            records = session.execute(
                select(MaintenanceRecord)
                .options(selectinload(MaintenanceRecord.vehicle))
                .where(MaintenanceRecord.vehicle_id == vehicle_id)
            ).scalars().all()
        else:
            records = session.execute(
                select(MaintenanceRecord)
                .options(selectinload(MaintenanceRecord.vehicle))
            ).scalars().all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'id', 'vehicle_name', 'date', 'mileage', 'description', 'cost',
            'oil_change_interval', 'is_oil_change', 'oil_type', 'oil_brand',
            'oil_filter_brand', 'oil_filter_part_number', 'oil_cost',
            'filter_cost', 'labor_cost', 'photo_path', 'photo_description'
        ])
        
        # Write data
        for record in records:
            writer.writerow([
                record.id,
                record.vehicle.name if record.vehicle else '',
                record.date.strftime('%Y-%m-%d') if record.date else '',
                record.mileage or '',
                record.description or '',
                record.cost or '',
                record.oil_change_interval or '',
                record.is_oil_change or False,
                record.oil_type or '',
                record.oil_brand or '',
                record.oil_filter_brand or '',
                record.oil_filter_part_number or '',
                record.oil_cost or '',
                record.filter_cost or '',
                record.labor_cost or '',
                record.photo_path or '',
                record.photo_description or ''
            ])
        
        return {"success": True, "csv_content": output.getvalue()}
    except Exception as e:
        return {"success": False, "error": str(e)}
