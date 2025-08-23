"""
Centralized data operations for Vehicle Maintenance Tracker
This module contains all database operations to ensure consistency across pages
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from models import Vehicle, MaintenanceRecord
from importer import import_csv, ImportResult
from database import SessionLocal
import csv
from io import StringIO
from datetime import datetime

# ============================================================================
# VEHICLE OPERATIONS
# ============================================================================

def get_all_vehicles() -> List[Vehicle]:
    """Get all vehicles ordered by name with maintenance records eagerly loaded"""
    session = SessionLocal()
    try:
        # Use selectinload to eagerly load the maintenance_records relationship
        from sqlalchemy.orm import selectinload
        vehicles = session.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.maintenance_records))
            .order_by(Vehicle.name)
        ).scalars().all()
        return vehicles
    except Exception as e:
        print(f"Error getting vehicles: {e}")
        return []
    finally:
        session.close()

def get_vehicle_by_id(vehicle_id: int) -> Optional[Vehicle]:
    """Get a specific vehicle by ID"""
    session = SessionLocal()
    try:
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        return vehicle
    except Exception as e:
        print(f"Error getting vehicle {vehicle_id}: {e}")
        return None
    finally:
        session.close()

def create_vehicle(name: str, make: str, model: str, year: int, vin: str) -> Dict[str, Any]:
    """Create a new vehicle with duplicate checking"""
    session = SessionLocal()
    try:
        # Check for duplicate name
        existing_name = session.execute(
            select(Vehicle).where(Vehicle.name == name)
        ).scalar_one_or_none()
        if existing_name:
            return {"success": False, "error": "A vehicle with this name already exists"}
        
        # Check for duplicate VIN
        if vin:
            existing_vin = session.execute(
                select(Vehicle).where(Vehicle.vin == vin)
            ).scalar_one_or_none()
            if existing_vin:
                return {"success": False, "error": "A vehicle with this VIN already exists"}
        
        # Create new vehicle
        vehicle = Vehicle(name=name, make=make, model=model, year=year, vin=vin)
        session.add(vehicle)
        session.commit()
        session.refresh(vehicle)
        
        return {"success": True, "vehicle": vehicle}
    except Exception as e:
        session.rollback()
        print(f"Error creating vehicle: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def update_vehicle(vehicle_id: int, name: str, make: str, model: str, year: int, vin: str) -> Dict[str, Any]:
    """Update an existing vehicle with duplicate checking"""
    session = SessionLocal()
    try:
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Check for duplicate name (excluding current vehicle)
        existing_name = session.execute(
            select(Vehicle).where(Vehicle.name == name, Vehicle.id != vehicle_id)
        ).scalar_one_or_none()
        if existing_name:
            return {"success": False, "error": "A vehicle with this name already exists"}
        
        # Check for duplicate VIN (excluding current vehicle)
        if vin:
            existing_vin = session.execute(
                select(Vehicle).where(Vehicle.vin == vin, Vehicle.id != vehicle_id)
            ).scalar_one_or_none()
            if existing_vin:
                return {"success": False, "error": "A vehicle with this VIN already exists"}
        
        # Update vehicle
        vehicle.name = name
        vehicle.make = make
        vehicle.model = model
        vehicle.year = year
        vehicle.vin = vin
        
        session.commit()
        session.refresh(vehicle)
        
        return {"success": True, "vehicle": vehicle}
    except Exception as e:
        session.rollback()
        print(f"Error updating vehicle: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def delete_vehicle(vehicle_id: int) -> Dict[str, Any]:
    """Delete a vehicle and all its maintenance records"""
    session = SessionLocal()
    try:
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Delete all maintenance records for this vehicle
        session.execute(delete(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id))
        
        # Delete the vehicle
        session.delete(vehicle)
        session.commit()
        
        return {"success": True}
    except Exception as e:
        session.rollback()
        print(f"Error deleting vehicle: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# ============================================================================
# MAINTENANCE OPERATIONS
# ============================================================================

def get_all_maintenance_records() -> List[MaintenanceRecord]:
    """Get all maintenance records with vehicle information"""
    session = SessionLocal()
    try:
        # Use selectinload to eagerly load the vehicle relationship
        from sqlalchemy.orm import selectinload
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .order_by(MaintenanceRecord.date.desc())
        ).scalars().all()
        return records
    except Exception as e:
        print(f"Error getting maintenance records: {e}")
        return []
    finally:
        session.close()

def get_maintenance_records_by_vehicle(vehicle_id: int) -> List[MaintenanceRecord]:
    """Get maintenance records for a specific vehicle ordered by date (newest first) with vehicle eagerly loaded"""
    session = SessionLocal()
    try:
        # Use selectinload to eagerly load the vehicle relationship
        from sqlalchemy.orm import selectinload
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .where(MaintenanceRecord.vehicle_id == vehicle_id)
            .order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.mileage.desc())
        ).scalars().all()
        return records
    except Exception as e:
        print(f"Error getting maintenance records for vehicle {vehicle_id}: {e}")
        return []
    finally:
        session.close()

def get_maintenance_by_id(record_id: int) -> Optional[MaintenanceRecord]:
    """Get a specific maintenance record by ID with vehicle eagerly loaded"""
    session = SessionLocal()
    try:
        # Use selectinload to eagerly load the vehicle relationship
        from sqlalchemy.orm import selectinload
        record = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .where(MaintenanceRecord.id == record_id)
        ).scalar_one_or_none()
        return record
    except Exception as e:
        print(f"Error getting maintenance record {record_id}: {e}")
        return None
    finally:
        session.close()

def create_maintenance_record(vehicle_id: int, date: str, description: str, cost: float, mileage: int, oil_change_interval: Optional[int] = None) -> Dict[str, Any]:
    """Create a new maintenance record"""
    session = SessionLocal()
    try:
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Parse date
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}
        
        # Create maintenance record
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=parsed_date,
            description=description,
            cost=cost,
            mileage=mileage,
            oil_change_interval=oil_change_interval
        )
        
        session.add(record)
        session.commit()
        session.refresh(record)
        
        return {"success": True, "record": record}
    except Exception as e:
        session.rollback()
        print(f"Error creating maintenance record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def update_maintenance_record(record_id: int, vehicle_id: int, date: str, description: str, cost: float, mileage: int, oil_change_interval: Optional[int] = None) -> Dict[str, Any]:
    """Update an existing maintenance record"""
    session = SessionLocal()
    try:
        record = session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.id == record_id)
        ).scalar_one_or_none()
        if not record:
            return {"success": False, "error": "Maintenance record not found"}
        
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Parse date
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}
        
        # Update record
        record.vehicle_id = vehicle_id
        record.date = parsed_date
        record.description = description
        record.cost = cost
        record.mileage = mileage
        record.oil_change_interval = oil_change_interval
        
        session.commit()
        session.refresh(record)
        
        return {"success": True, "record": record}
    except Exception as e:
        session.rollback()
        print(f"Error updating maintenance record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def delete_maintenance_record(record_id: int) -> Dict[str, Any]:
    """Delete a maintenance record"""
    session = SessionLocal()
    try:
        record = session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.id == record_id)
        ).scalar_one_or_none()
        if not record:
            return {"success": False, "error": "Maintenance record not found"}
        
        session.delete(record)
        session.commit()
        
        return {"success": True}
    except Exception as e:
        session.rollback()
        print(f"Error deleting maintenance record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

# ============================================================================
# IMPORT/EXPORT OPERATIONS
# ============================================================================

def import_csv_data(file_content: str, vehicle_id: int = None) -> ImportResult:
    """Import CSV data with centralized logic - now uses improved importer.py functions"""
    session = SessionLocal()
    try:
        if vehicle_id is None:
            return ImportResult(
                success=False,
                message="Vehicle ID is required for import",
                vehicles_imported=0,
                maintenance_imported=0,
                errors=[]
            )
        
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return ImportResult(
                success=False,
                message="Selected vehicle not found",
                vehicles_imported=0,
                maintenance_imported=0,
                errors=[]
            )
        
        # Use the improved importer.py functions instead of basic parsing
        from importer import import_csv
        print(f"DEBUG: Calling importer.import_csv with file_content length: {len(file_content)}")
        print(f"DEBUG: First 100 chars of file_content: {file_content[:100]}")
        result = import_csv(file_content.encode('utf-8'), vehicle_id, session, "skip")
        print(f"DEBUG: Import result: {result}")
        return result
        
    except Exception as e:
        session.rollback()
        print(f"Error importing CSV: {e}")
        return ImportResult(
            success=False,
            message=f"Import failed: {str(e)}",
            vehicles_imported=0,
            maintenance_imported=0,
            errors=[]
        )
    finally:
        session.close()

def export_vehicles_csv() -> str:
    """Export vehicles to CSV format"""
    try:
        vehicles = get_all_vehicles()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Make', 'Model', 'Year', 'VIN'])
        
        # Write data
        for vehicle in vehicles:
            writer.writerow([
                vehicle.name,
                vehicle.make,
                vehicle.model,
                vehicle.year,
                vehicle.vin or ''
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting vehicles: {e}")
        return ""

def export_maintenance_csv() -> str:
    """Export maintenance records to CSV format"""
    session = SessionLocal()
    try:
        # Get records with vehicle info while session is active
        from sqlalchemy.orm import selectinload
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .order_by(MaintenanceRecord.date.desc())
        ).scalars().all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Vehicle Name', 'Date', 'Description', 'Cost', 'Mileage'])
        
        # Write data while session is still active
        for record in records:
            vehicle_name = record.vehicle.name if record.vehicle else "Unknown"
            writer.writerow([
                vehicle_name,
                record.date.strftime("%Y-%m-%d"),
                record.description,
                f"${record.cost:.2f}" if record.cost else "$0.00",
                record.mileage
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting maintenance: {e}")
        return ""
    finally:
        session.close()

# ============================================================================
# UTILITY OPERATIONS
# ============================================================================

def get_vehicle_names() -> List[Dict[str, Any]]:
    """Get list of vehicle names and IDs for dropdowns"""
    try:
        vehicles = get_all_vehicles()
        return [{"id": v.id, "name": v.name} for v in vehicles]
    except Exception as e:
        print(f"Error getting vehicle names: {e}")
        return []

def get_maintenance_summary() -> Dict[str, Any]:
    """Get summary statistics for maintenance page"""
    try:
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        total_vehicles = len(vehicles)
        total_records = len(records)
        total_cost = sum(record.cost or 0 for record in records)
        
        return {
            "total_vehicles": total_vehicles,
            "total_records": total_records,
            "total_cost": total_cost,
            "average_cost_per_record": total_cost / total_records if total_records > 0 else 0
        }
    except Exception as e:
        print(f"Error getting maintenance summary: {e}")
        return {
            "total_vehicles": 0,
            "total_records": 0,
            "total_cost": 0,
            "average_cost_per_record": 0
        }

def get_current_mileage_from_all_sources(vehicle_id: int) -> int:
    """Get current mileage from all sources (maintenance, oil change, fuel) - use highest/most recent"""
    try:
        # Get all records for this vehicle
        records = get_all_maintenance_records()
        vehicle_records = [record for record in records if record.vehicle_id == vehicle_id]
        
        # Get fuel entries for this vehicle
        from database import SessionLocal
        session = SessionLocal()
        try:
            from models import FuelEntry
            fuel_entries = session.execute(
                select(FuelEntry).where(FuelEntry.vehicle_id == vehicle_id)
            ).scalars().all()
        finally:
            session.close()
        
        # Collect all mileage data with dates
        mileage_data = []
        
        # Add maintenance records
        for record in vehicle_records:
            mileage_data.append({
                'mileage': record.mileage,
                'date': record.date,
                'source': 'maintenance',
                'description': record.description
            })
        
        # Add fuel entries
        for fuel in fuel_entries:
            mileage_data.append({
                'mileage': fuel.mileage,
                'date': fuel.date,
                'source': 'fuel',
                'description': f'Fuel fill-up'
            })
        
        if not mileage_data:
            return 0
        
        # Sort by date (most recent first) and mileage (highest first)
        mileage_data.sort(key=lambda x: (x['date'], x['mileage']), reverse=True)
        
        # Get the highest mileage from the most recent date
        latest_date = mileage_data[0]['date']
        latest_mileages = [m for m in mileage_data if m['date'] == latest_date]
        current_mileage = max(m['mileage'] for m in latest_mileages)
        
        print(f"Vehicle {vehicle_id} current mileage: {current_mileage:,} from {latest_mileages[0]['source']} on {latest_date}")
        return current_mileage
        
    except Exception as e:
        print(f"Error getting current mileage for vehicle {vehicle_id}: {e}")
        return 0

def get_oil_change_interval_from_record(record: MaintenanceRecord) -> int:
    """Get oil change interval from the record, with fallback to default"""
    if record.oil_change_interval and record.oil_change_interval > 0:
        return record.oil_change_interval
    
    # Fallback to default intervals based on vehicle type/age
    # This could be enhanced with vehicle-specific logic
    return 3000  # Default 3,000 miles

def get_home_dashboard_summary() -> Dict[str, Any]:
    """Get enhanced summary statistics for home page dashboard"""
    try:
        # Get basic data
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        # Calculate date range for last 30 days
        from datetime import datetime, timedelta
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Get recent activity (last 30 days)
        recent_records = [
            record for record in records 
            if record.date and record.date >= thirty_days_ago
        ]
        
        # Calculate collective miles this year
        current_year = today.year
        year_records = [
            record for record in records 
            if record.date and record.date.year == current_year
        ]
        
        # Calculate total miles driven this year using enhanced mileage tracking
        total_miles_this_year = 0
        if year_records:
            # Group records by vehicle to calculate miles per vehicle
            vehicle_miles = {}
            for record in year_records:
                if record.vehicle_id not in vehicle_miles:
                    vehicle_miles[record.vehicle_id] = []
                vehicle_miles[record.vehicle_id].append(record)
            
            # Calculate miles for each vehicle this year
            for vehicle_id, vehicle_records in vehicle_miles.items():
                if len(vehicle_records) >= 2:
                    # Sort by date to get chronological order
                    vehicle_records.sort(key=lambda x: x.date)
                    
                    # Calculate miles driven for this vehicle
                    first_mileage = vehicle_records[0].mileage or 0
                    last_mileage = vehicle_records[-1].mileage or 0
                    vehicle_miles_driven = last_mileage - first_mileage
                    
                    # Only add positive miles (handle odometer resets/errors)
                    if vehicle_miles_driven > 0:
                        total_miles_this_year += vehicle_miles_driven
        
        # Enhanced oil change reminders with dynamic intervals
        oil_change_reminders = []
        for vehicle in vehicles:
            # Get current mileage from ALL sources (maintenance, fuel, etc.)
            current_mileage = get_current_mileage_from_all_sources(vehicle.id)
            
            if current_mileage > 0:
                # Find last oil change for this vehicle
                oil_changes = [
                    record for record in records 
                    if record.vehicle_id == vehicle.id and 'oil' in record.description.lower()
                ]
                
                if oil_changes:
                    # Get most recent oil change
                    last_oil_change = max(oil_changes, key=lambda x: x.date)
                    
                    # Get the oil change interval from the record
                    oil_change_interval = get_oil_change_interval_from_record(last_oil_change)
                    
                    miles_since_oil_change = current_mileage - last_oil_change.mileage
                    miles_until_next = oil_change_interval - miles_since_oil_change
                    
                    # Show reminder if due within 500 miles OR overdue
                    if miles_until_next <= 500:
                        oil_change_reminders.append({
                            "vehicle_name": vehicle.name,
                            "miles_until_due": miles_until_next,
                            "current_mileage": current_mileage,
                            "last_oil_change_mileage": last_oil_change.mileage,
                            "oil_change_interval": oil_change_interval,
                            "status": "overdue" if miles_until_next < 0 else "due_soon"
                        })
                else:
                    # No oil change records, estimate based on current mileage
                    # Use default interval for estimation
                    default_interval = 3000
                    miles_until_next = default_interval - current_mileage % default_interval
                    if miles_until_next <= 500:
                        oil_change_reminders.append({
                            "vehicle_name": vehicle.name,
                            "miles_until_due": miles_until_next,
                            "current_mileage": current_mileage,
                            "last_oil_change_mileage": None,
                            "oil_change_interval": default_interval,
                            "status": "due_soon"
                        })
        
        return {
            "recent_activity_count": len(recent_records),
            "recent_records": recent_records,
            "total_miles_this_year": total_miles_this_year,
            "oil_change_reminders": oil_change_reminders,
            "total_vehicles": len(vehicles)
        }
    except Exception as e:
        print(f"Error getting home dashboard summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "recent_activity_count": 0,
            "recent_records": [],
            "total_miles_this_year": 0,
            "oil_change_reminders": [],
            "total_vehicles": 0
        }
