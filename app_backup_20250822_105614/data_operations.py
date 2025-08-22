"""
Centralized data operations for Vehicle Maintenance Tracker
This module contains all database operations to ensure consistency across pages
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
import csv
from io import StringIO
from datetime import datetime

# Try to import local modules, with fallbacks
try:
    from models import Vehicle, MaintenanceRecord
    from database import SessionLocal
    from importer import import_csv, ImportResult
    print("Successfully imported all modules in data_operations.py")
except ImportError as e:
    print(f"Failed to import modules in data_operations.py: {e}")
    # Create dummy objects to prevent crashes
    Vehicle = None
    MaintenanceRecord = None
    SessionLocal = None
    import_csv = None
    ImportResult = None

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
    # Create a new session directly
    from database import SessionLocal
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
    # Create a new session directly
    from database import SessionLocal
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

def get_maintenance_by_id(record_id: int) -> Optional[MaintenanceRecord]:
    """Get a specific maintenance record by ID"""
    session = get_session()
    try:
        record = session.execute(
            select(MaintenanceRecord).where(MaintenanceRecord.id == record_id)
        ).scalar_one_or_none()
        return record
    except Exception as e:
        print(f"Error getting maintenance record {record_id}: {e}")
        return None
    finally:
        session.close()

def create_maintenance_record(vehicle_id: int, date: str, description: str, cost: float, mileage: int) -> Dict[str, Any]:
    """Create a new maintenance record"""
    session = get_session()
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
            mileage=mileage
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

def update_maintenance_record(record_id: int, vehicle_id: int, date: str, description: str, cost: float, mileage: int) -> Dict[str, Any]:
    """Update an existing maintenance record"""
    session = get_session()
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
    session = get_session()
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
    """Import CSV data with centralized logic"""
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
        
        # Parse CSV content
        csv_file = StringIO(file_content)
        reader = csv.DictReader(csv_file)
        
        fieldnames_lower = [col.lower() for col in reader.fieldnames]
        required_columns = ['description']
        if not all(col in fieldnames_lower for col in required_columns):
            return ImportResult(
                success=False,
                message=f"Missing required columns. Found: {reader.fieldnames}",
                vehicles_imported=0,
                maintenance_imported=0,
                errors=[]
            )
        
        # Check that we have either date OR mileage
        has_date = 'date' in fieldnames_lower
        has_mileage = 'mileage' in fieldnames_lower
        if not has_date and not has_mileage:
            return ImportResult(
                success=False,
                message="CSV must contain either 'date' or 'mileage' column (or both)",
                vehicles_imported=0,
                maintenance_imported=0,
                errors=[]
            )
        
        has_cost = 'cost' in fieldnames_lower
        col_mapping = {}
        for col in reader.fieldnames:
            col_lower = col.lower()
            if col_lower in required_columns or col_lower == 'cost' or col_lower == 'date' or col_lower == 'mileage':
                col_mapping[col_lower] = col
        
        # Placeholder date for records without dates
        from datetime import date
        PLACEHOLDER_DATE = date(1900, 1, 1)
        
        result = ImportResult()
        
        for row_num, row in enumerate(reader, start=2):
            result.total_rows += 1
            
            try:
                date_obj = None
                if has_date and row[col_mapping['date']] and row[col_mapping['date']].strip():
                    try:
                        date_obj = datetime.strptime(row[col_mapping['date']], "%Y-%m-%d").date()
                    except ValueError:
                        result.skipped_rows += 1
                        result.skipped_details.append(f"Row {row_num}: Invalid date format '{row[col_mapping['date']]}' - will use placeholder date")
                        date_obj = None
                
                mileage = 0
                if has_mileage and row[col_mapping['mileage']]:
                    try:
                        mileage = int(row[col_mapping['mileage']])
                    except ValueError:
                        result.skipped_rows += 1
                        result.skipped_details.append(f"Row {row_num}: Invalid mileage '{row[col_mapping['mileage']]}' - using 0")
                        mileage = 0
                
                cost = None
                if has_cost and row[col_mapping['cost']]:
                    try:
                        cost = float(row[col_mapping['cost']])
                    except ValueError:
                        result.skipped_rows += 1
                        result.skipped_details.append(f"Row {row_num}: Invalid cost '{row[col_mapping['cost']]}' - using null")
                        cost = None
                
                description = row[col_mapping['description']].strip()
                if not description:
                    result.skipped_rows += 1
                    result.skipped_details.append(f"Row {row_num}: Empty description - skipping")
                    continue
                
                # Use placeholder date if no valid date provided
                final_date = date_obj if date_obj else PLACEHOLDER_DATE
                
                # Create maintenance record
                record = MaintenanceRecord(
                    vehicle_id=vehicle_id,
                    date=final_date,
                    description=description,
                    cost=cost,
                    mileage=mileage
                )
                
                session.add(record)
                result.maintenance_imported += 1
                
            except Exception as e:
                result.skipped_rows += 1
                result.skipped_details.append(f"Row {row_num}: Error processing row - {str(e)}")
                continue
        
        session.commit()
        result.success = True
        result.message = f"Successfully imported {result.maintenance_imported} maintenance records"
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
    """Get summary statistics for dashboard"""
    try:
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        total_vehicles = len(vehicles)
        total_records = len(records)
        total_cost = sum(record.cost for record in records)
        
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
