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

def create_maintenance_record(vehicle_id: int, date: str, description: str, cost: float, mileage: Optional[int], oil_change_interval: Optional[int] = None) -> Dict[str, Any]:
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
        
        # Handle missing mileage - use placeholder and mark date as estimated for sorting
        if mileage is None:
            mileage = 0  # Placeholder mileage
            date_estimated = True
        else:
            date_estimated = False
        
        # Create maintenance record
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=parsed_date,
            description=description,
            cost=cost,
            mileage=mileage,
            date_estimated=date_estimated,
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

def update_maintenance_record(record_id: int, vehicle_id: int, date: str, description: str, cost: float, mileage: Optional[int], oil_change_interval: Optional[int] = None) -> Dict[str, Any]:
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
        
        # Handle missing mileage - use placeholder and mark date as estimated for sorting
        if mileage is None:
            mileage = 0  # Placeholder mileage
            date_estimated = True
        else:
            date_estimated = False
        
        # Update record
        record.vehicle_id = vehicle_id
        record.date = parsed_date
        record.description = description
        record.cost = cost
        record.mileage = mileage
        record.date_estimated = date_estimated
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

# ============================================================================
# MILEAGE TRACKING OPERATIONS
# ============================================================================

def get_vehicle_current_mileage(vehicle_id: int) -> Dict[str, Any]:
    """
    Centralized function to get current mileage for any vehicle from all data sources.
    Returns comprehensive mileage information including source and confidence level.
    
    Args:
        vehicle_id: ID of the vehicle
        
    Returns:
        Dict containing:
        - current_mileage: int - The most accurate current mileage
        - source: str - Where the mileage came from ('maintenance', 'fuel', 'vehicle')
        - source_date: date - When this mileage was recorded
        - source_description: str - Description of the source record
        - confidence: str - How confident we are in this mileage ('high', 'medium', 'low')
        - all_sources: list - All mileage records found for this vehicle
    """
    try:
        session = SessionLocal()
        
        # Get all maintenance records for this vehicle
        maintenance_records = session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id)
        ).scalars().all()
        
        # Get all fuel entries for this vehicle
        from models import FuelEntry
        fuel_entries = session.execute(
            select(FuelEntry).where(FuelEntry.vehicle_id == vehicle_id)
        ).scalars().all()
        
        # Collect all mileage data with metadata
        mileage_data = []
        
        # Add maintenance records
        for record in maintenance_records:
            mileage_data.append({
                'mileage': record.mileage,
                'date': record.date,
                'source': 'maintenance',
                'description': record.description,
                'record_id': record.id,
                'type': 'maintenance'
            })
        
        # Add fuel entries
        for fuel in fuel_entries:
            mileage_data.append({
                'mileage': fuel.mileage,
                'date': fuel.date,
                'source': 'fuel',
                'description': f'Fuel fill-up ({fuel.fuel_amount} gal)',
                'record_id': fuel.id,
                'type': 'fuel'
            })
        
        if not mileage_data:
            return {
                'current_mileage': 0,
                'source': 'none',
                'source_date': None,
                'source_description': 'No mileage data found',
                'confidence': 'low',
                'all_sources': []
            }
        
        # Sort by date (most recent first) and then by mileage (highest first)
        mileage_data.sort(key=lambda x: (x['date'], x['mileage']), reverse=True)
        
        # Get the highest mileage from the most recent date
        latest_date = mileage_data[0]['date']
        latest_mileages = [m for m in mileage_data if m['date'] == latest_date]
        current_mileage = max(m['mileage'] for m in latest_mileages)
        
        # Find the record that provides this mileage
        current_record = next(m for m in latest_mileages if m['mileage'] == current_mileage)
        
        # Determine confidence level
        confidence = 'high'
        if len(latest_mileages) > 1:
            # Multiple sources on same date - check for consistency
            mileage_range = max(m['mileage'] for m in latest_mileages) - min(m['mileage'] for m in latest_mileages)
            if mileage_range > 1000:  # More than 1000 mile difference
                confidence = 'medium'
        elif len(mileage_data) == 1:
            confidence = 'medium'  # Only one data point
        
        # Calculate days since last update
        days_since_update = (datetime.now().date() - latest_date).days if latest_date else None
        
        result = {
            'current_mileage': current_mileage,
            'source': current_record['source'],
            'source_date': latest_date,
            'source_description': current_record['description'],
            'record_id': current_record['record_id'],
            'confidence': confidence,
            'days_since_update': days_since_update,
            'all_sources': mileage_data,
            'total_sources': len(mileage_data)
        }
        
        print(f"Vehicle {vehicle_id} current mileage: {current_mileage:,} from {current_record['source']} on {latest_date} (confidence: {confidence})")
        return result
        
    except Exception as e:
        print(f"Error getting current mileage for vehicle {vehicle_id}: {e}")
        return {
            'current_mileage': 0,
            'source': 'error',
            'source_date': None,
            'source_description': f'Error: {str(e)}',
            'confidence': 'low',
            'all_sources': [],
            'total_sources': 0
        }
    finally:
        session.close()

def get_all_vehicles_current_mileage() -> Dict[int, Dict[str, Any]]:
    """
    Get current mileage for all vehicles at once.
    Useful for bulk operations and dashboard displays.
    
    Returns:
        Dict mapping vehicle_id to mileage info from get_vehicle_current_mileage()
    """
    vehicles = get_all_vehicles()
    mileage_data = {}
    
    for vehicle in vehicles:
        mileage_data[vehicle.id] = get_vehicle_current_mileage(vehicle.id)
    
    return mileage_data

# ============================================================================
# LEGACY FUNCTIONS (keeping for backward compatibility)
# ============================================================================

def get_current_mileage_from_all_sources(vehicle_id: int) -> int:
    """
    Legacy function - use get_vehicle_current_mileage() instead.
    Returns just the mileage number for backward compatibility.
    """
    mileage_info = get_vehicle_current_mileage(vehicle_id)
    return mileage_info['current_mileage']

def get_oil_change_interval_from_record(record: MaintenanceRecord) -> int:
    """Get oil change interval from the record, with fallback to default"""
    if record.oil_change_interval and record.oil_change_interval > 0:
        return record.oil_change_interval
    
    # Fallback to default intervals based on vehicle type/age
    # This could be enhanced with vehicle-specific logic
    return 5000  # Default 5,000 miles

def get_home_dashboard_summary() -> Dict[str, Any]:
    """Get enhanced summary statistics for home page dashboard using centralized mileage tracking"""
    try:
        # Get basic data
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        # Get current mileage for all vehicles using centralized function
        vehicles_current_mileage = get_all_vehicles_current_mileage()
        
        # Calculate date range for last 30 days
        from datetime import datetime, timedelta
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Get recent activity (last 30 days)
        recent_records = [
            record for record in records 
            if record.date and record.date >= thirty_days_ago
        ]
        
        # Enhanced Miles This Year calculation using centralized mileage data
        current_year = today.year
        year_records = [
            record for record in records 
            if record.date and record.date.year == current_year
        ]
        
        # Calculate miles this year with detailed breakdown
        total_miles_this_year = 0
        vehicle_miles_breakdown = []
        
        for vehicle in vehicles:
            vehicle_id = vehicle.id
            current_mileage_info = vehicles_current_mileage.get(vehicle_id, {})
            current_mileage = current_mileage_info.get('current_mileage', 0)
            
            if current_mileage > 0:
                # Get all records for this vehicle this year
                vehicle_year_records = [
                    record for record in year_records 
                    if record.vehicle_id == vehicle_id
                ]
                
                # Get fuel entries for this vehicle this year
                from models import FuelEntry
                session = SessionLocal()
                try:
                    vehicle_fuel_entries = session.execute(
                        select(FuelEntry).where(
                            FuelEntry.vehicle_id == vehicle_id,
                            FuelEntry.date >= datetime(current_year, 1, 1).date()
                        ).order_by(FuelEntry.date)
                    ).scalars().all()
                finally:
                    session.close()
                
                # Combine maintenance and fuel records for this vehicle
                all_vehicle_records = []
                
                # Add maintenance records
                for record in vehicle_year_records:
                    all_vehicle_records.append({
                        'date': record.date,
                        'mileage': record.mileage,
                        'source': 'maintenance',
                        'description': record.description
                    })
                
                # Add fuel entries
                for fuel in vehicle_fuel_entries:
                    all_vehicle_records.append({
                        'date': fuel.date,
                        'mileage': fuel.mileage,
                        'source': 'fuel',
                        'description': f'Fuel fill-up ({fuel.fuel_amount} gal)'
                    })
                
                # Sort by date to get chronological order
                all_vehicle_records.sort(key=lambda x: x['date'])
                
                if len(all_vehicle_records) >= 2:
                    # Calculate miles driven for this vehicle this year
                    first_mileage = all_vehicle_records[0]['mileage']
                    last_mileage = all_vehicle_records[-1]['mileage']
                    vehicle_miles_driven = last_mileage - first_mileage
                    
                    # Only add positive miles (handle odometer resets/errors)
                    if vehicle_miles_driven > 0:
                        total_miles_this_year += vehicle_miles_driven
                        
                        # Add to breakdown
                        vehicle_miles_breakdown.append({
                            'vehicle_name': vehicle.name,
                            'vehicle_id': vehicle.id,
                            'miles_driven': vehicle_miles_driven,
                            'first_mileage': first_mileage,
                            'last_mileage': last_mileage,
                            'first_date': all_vehicle_records[0]['date'],
                            'last_date': all_vehicle_records[-1]['date'],
                            'record_count': len(all_vehicle_records),
                            'current_mileage': current_mileage,
                            'mileage_source': current_mileage_info.get('source', 'unknown'),
                            'mileage_confidence': current_mileage_info.get('confidence', 'low')
                        })
                else:
                    # Not enough records to calculate miles driven, but we have current mileage
                    vehicle_miles_breakdown.append({
                        'vehicle_name': vehicle.name,
                        'vehicle_id': vehicle.id,
                        'miles_driven': 0,
                        'first_mileage': None,
                        'last_mileage': None,
                        'first_date': None,
                        'last_date': None,
                        'record_count': len(all_vehicle_records),
                        'current_mileage': current_mileage,
                        'mileage_source': current_mileage_info.get('source', 'unknown'),
                        'mileage_confidence': current_mileage_info.get('confidence', 'low'),
                        'note': 'Insufficient records to calculate miles driven this year'
                    })
        
        # Enhanced oil change reminders with dynamic intervals
        oil_change_reminders = []
        for vehicle in vehicles:
            vehicle_id = vehicle.id
            current_mileage_info = vehicles_current_mileage.get(vehicle_id, {})
            current_mileage = current_mileage_info.get('current_mileage', 0)
            
            if current_mileage > 0:
                # Find last oil change for this vehicle
                oil_changes = [
                    record for record in records 
                    if record.vehicle_id == vehicle_id and 'oil' in record.description.lower()
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
                            "vehicle_id": vehicle.id,
                            "miles_until_due": miles_until_next,
                            "current_mileage": current_mileage,
                            "last_oil_change_mileage": last_oil_change.mileage,
                            "oil_change_interval": oil_change_interval,
                            "status": "overdue" if miles_until_next < 0 else "due_soon",
                            "last_oil_change_date": last_oil_change.date,
                            "mileage_source": current_mileage_info.get('source', 'unknown'),
                            "mileage_confidence": current_mileage_info.get('confidence', 'low')
                        })
                else:
                    # No oil change records, estimate based on current mileage
                    # Use default interval for estimation
                    default_interval = 5000
                    miles_until_next = default_interval - current_mileage % default_interval
                    if miles_until_next <= 500:
                        oil_change_reminders.append({
                            "vehicle_name": vehicle.name,
                            "vehicle_id": vehicle.id,
                            "miles_until_due": miles_until_next,
                            "current_mileage": current_mileage,
                            "last_oil_change_mileage": None,
                            "oil_change_interval": default_interval,
                            "status": "due_soon",
                            "last_oil_change_date": None,
                            "mileage_source": current_mileage_info.get('source', 'unknown'),
                            "mileage_confidence": current_mileage_info.get('confidence', 'low'),
                            "note": "No oil change records found, using default interval"
                        })
        
        return {
            "recent_activity_count": len(recent_records),
            "recent_records": recent_records,
            "total_miles_this_year": total_miles_this_year,
            "vehicle_miles_breakdown": vehicle_miles_breakdown,
            "oil_change_reminders": oil_change_reminders,
            "total_vehicles": len(vehicles),
            "mileage_data_quality": {
                "total_vehicles_with_mileage": len([v for v in vehicles_current_mileage.values() if v.get('current_mileage', 0) > 0]),
                "high_confidence_mileage": len([v for v in vehicles_current_mileage.values() if v.get('confidence') == 'high']),
                "medium_confidence_mileage": len([v for v in vehicles_current_mileage.values() if v.get('confidence') == 'medium']),
                "low_confidence_mileage": len([v for v in vehicles_current_mileage.values() if v.get('confidence') == 'low'])
            }
        }
    except Exception as e:
        print(f"Error getting home dashboard summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "recent_activity_count": 0,
            "recent_records": [],
            "total_miles_this_year": 0,
            "vehicle_miles_breakdown": [],
            "oil_change_reminders": [],
            "total_vehicles": 0,
            "mileage_data_quality": {
                "total_vehicles_with_mileage": 0,
                "high_confidence_mileage": 0,
                "medium_confidence_mileage": 0,
                "low_confidence_mileage": 0
            }
        }

# ============================================================================
# FUEL TRACKING OPERATIONS
# ============================================================================

def get_fuel_entries_for_vehicle(vehicle_id: int) -> List[Dict[str, Any]]:
    """Get all fuel entries for a specific vehicle"""
    try:
        session = SessionLocal()
        from models import FuelEntry
        
        fuel_entries = session.execute(
            select(FuelEntry).where(FuelEntry.vehicle_id == vehicle_id).order_by(FuelEntry.date.desc(), FuelEntry.mileage.desc())
        ).scalars().all()
        
        # Convert to dictionaries for easier handling
        entries = []
        for entry in fuel_entries:
            entries.append({
                'id': entry.id,
                'date': entry.date,
                'mileage': entry.mileage,
                'fuel_amount': entry.fuel_amount,
                'fuel_cost': entry.fuel_cost,
                'fuel_type': entry.fuel_type,
                'driving_pattern': entry.driving_pattern,
                'notes': entry.notes,
                'odometer_photo': entry.odometer_photo,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            })
        
        return entries
        
    except Exception as e:
        print(f"Error getting fuel entries for vehicle {vehicle_id}: {e}")
        return []
    finally:
        session.close()

def get_all_fuel_entries() -> List[Dict[str, Any]]:
    """Get all fuel entries across all vehicles"""
    try:
        session = SessionLocal()
        from models import FuelEntry
        
        fuel_entries = session.execute(
            select(FuelEntry).order_by(FuelEntry.date.desc(), FuelEntry.mileage.desc())
        ).scalars().all()
        
        # Convert to dictionaries with vehicle info
        entries = []
        for entry in fuel_entries:
            vehicle = session.execute(
                select(Vehicle).where(Vehicle.id == entry.vehicle_id)
            ).scalar_one_or_none()
            
            entries.append({
                'id': entry.id,
                'vehicle_id': entry.vehicle_id,
                'vehicle_name': vehicle.name if vehicle else 'Unknown Vehicle',
                'date': entry.date,
                'mileage': entry.mileage,
                'fuel_amount': entry.fuel_amount,
                'fuel_cost': entry.fuel_cost,
                'fuel_type': entry.fuel_type,
                'driving_pattern': entry.driving_pattern,
                'notes': entry.notes,
                'odometer_photo': entry.odometer_photo,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            })
        
        return entries
        
    except Exception as e:
        print(f"Error getting all fuel entries: {e}")
        return []
    finally:
        session.close()

def get_vehicle_health_status() -> List[Dict[str, Any]]:
    """Get health status for all vehicles including mileage, cost, and maintenance status"""
    try:
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        # Get current mileage for all vehicles
        vehicles_current_mileage = get_all_vehicles_current_mileage()
        
        # Calculate current year
        from datetime import datetime
        current_year = datetime.now().year
        
        vehicle_health = []
        
        for vehicle in vehicles:
            vehicle_id = vehicle.id
            current_mileage_info = vehicles_current_mileage.get(vehicle_id, {})
            current_mileage = current_mileage_info.get('current_mileage', 0)
            
            # Get maintenance records for this vehicle this year
            vehicle_records = [r for r in records if r.vehicle_id == vehicle_id]
            vehicle_year_records = [r for r in vehicle_records if r.date and r.date.year == current_year]
            
            # Calculate cost this year
            cost_this_year = sum(r.cost or 0 for r in vehicle_year_records)
            
            # Get oil change status
            oil_changes = [r for r in vehicle_records if 'oil' in r.description.lower()]
            oil_change_status = "unknown"
            
            if oil_changes and current_mileage > 0:
                # Sort by date (most recent first)
                oil_changes.sort(key=lambda x: x.date, reverse=True)
                last_oil_change = oil_changes[0]
                
                # Get oil change interval
                oil_change_interval = get_oil_change_interval_from_record(last_oil_change)
                miles_since_oil_change = current_mileage - last_oil_change.mileage
                miles_until_next = oil_change_interval - miles_since_oil_change
                
                if miles_until_next < 0:
                    oil_change_status = "overdue"
                elif miles_until_next <= 500:
                    oil_change_status = "due_soon"
                else:
                    oil_change_status = "good"
            
            # Determine overall health indicator
            if oil_change_status == "overdue":
                health_indicator = "🔴"
                health_text = "Overdue"
                health_class = "text-danger"
            elif oil_change_status == "due_soon":
                health_indicator = "🟡"
                health_text = "Due Soon"
                health_class = "text-warning"
            elif oil_change_status == "good":
                health_indicator = "🟢"
                health_text = "Good"
                health_class = "text-success"
            else:
                health_indicator = "⚪"
                health_text = "Unknown"
                health_class = "text-muted"
            
            vehicle_health.append({
                "vehicle": vehicle,
                "current_mileage": current_mileage,
                "cost_this_year": cost_this_year,
                "health_indicator": health_indicator,
                "health_text": health_text,
                "health_class": health_class,
                "oil_change_status": oil_change_status,
                "maintenance_count": len(vehicle_records),
                "year_records_count": len(vehicle_year_records)
            })
        
        return vehicle_health
        
    except Exception as e:
        print(f"Error getting vehicle health status: {e}")
        return []
