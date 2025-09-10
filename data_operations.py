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
from pathlib import Path
import os

def parse_date_string(date_string: str) -> datetime.date:
    """Parse date string in either MM/DD/YYYY or YYYY-MM-DD format"""
    if not date_string or date_string == "0":
        raise ValueError("Date string cannot be empty")
    
    # Try MM/DD/YYYY format first (new standard)
    try:
        return datetime.strptime(date_string, "%m/%d/%Y").date()
    except ValueError:
        # Fall back to YYYY-MM-DD format (legacy)
        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use MM/DD/YYYY or YYYY-MM-DD")

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

def sort_maintenance_records(records: List[MaintenanceRecord], sort_by: str = 'date', direction: str = 'desc') -> List[MaintenanceRecord]:
    """
    Centralized function to sort maintenance records
    
    Args:
        records: List of MaintenanceRecord objects
        sort_by: 'vehicle', 'date', or 'mileage'
        direction: 'asc' or 'desc'
    
    Returns:
        Sorted list of maintenance records
    """
    try:
        if not records:
            return []
        
        # Create a copy to avoid modifying the original list
        sorted_records = records.copy()
        
        if sort_by == 'vehicle':
            # Sort by vehicle name first, then by mileage (desc) -> date (desc) within each vehicle
            # If no mileage, sort by date within the vehicle group
            sorted_records.sort(key=lambda x: (
                x.vehicle.name if x.vehicle else 'Unknown',
                -(x.mileage if x.mileage and x.mileage > 0 else 0),  # Negative for desc
                -(x.date.toordinal() if x.date and x.date.year > 1900 else 0)  # Negative for desc
            ))
            
        elif sort_by == 'date':
            # Sort by date (handle placeholder dates)
            sorted_records.sort(key=lambda x: (
                x.date.toordinal() if x.date and x.date.year > 1900 else 0
            ), reverse=(direction == 'desc'))
            
        elif sort_by == 'mileage':
            # Sort by mileage (handle 0/None mileage)
            sorted_records.sort(key=lambda x: (
                x.mileage if x.mileage and x.mileage > 0 else 0
            ), reverse=(direction == 'desc'))
            
        else:
            # Default to date desc if invalid sort_by
            sorted_records.sort(key=lambda x: (
                x.date.toordinal() if x.date and x.date.year > 1900 else 0
            ), reverse=True)
        
        return sorted_records
        
    except Exception as e:
        print(f"Error sorting maintenance records: {e}")
        # Return original list if sorting fails
        return records

def create_basic_maintenance_record(vehicle_id: int, date: str, description: str, cost: float, mileage: Optional[int], 
                                   oil_change_interval: Optional[int] = None) -> Dict[str, Any]:
    """Create a basic maintenance record (regular maintenance or oil change)"""
    session = SessionLocal()
    try:
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Parse date
        parsed_date = parse_date_string(date)
        if parsed_date is None:
            # Use placeholder date (01/01/1900) for records without dates
            from datetime import date as date_class
            parsed_date = date_class(1900, 1, 1)
            date_estimated = True
        else:
            date_estimated = False
        
        # Handle missing mileage
        if mileage is None:
            mileage = 0
            date_estimated = True
        else:
            date_estimated = False
        
        # Determine if this is an oil change
        is_oil_change = oil_change_interval is not None
        
        # Create record
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=parsed_date,
            description=description,
            cost=cost,
            mileage=mileage,
            date_estimated=date_estimated,
            oil_change_interval=oil_change_interval,
            is_oil_change=is_oil_change
        )
        
        session.add(record)
        session.commit()
        session.refresh(record)
        
        return {"success": True, "record": record}
    except Exception as e:
        session.rollback()
        print(f"Error creating basic maintenance record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def create_oil_analysis_record(vehicle_id: int, date: str, description: str, mileage: int,
                              oil_analysis_date: Optional[str] = None,
                              next_oil_analysis_date: Optional[str] = None,
                              oil_analysis_cost: Optional[float] = None,
                              iron_level: Optional[float] = None,
                              aluminum_level: Optional[float] = None,
                              copper_level: Optional[float] = None,
                              viscosity: Optional[float] = None,
                              tbn: Optional[float] = None,
                              fuel_dilution: Optional[float] = None,
                              coolant_contamination: Optional[bool] = None,
                              driving_conditions: Optional[str] = None,
                              oil_consumption_notes: Optional[str] = None,
                              linked_oil_change_id: Optional[int] = None,
                              oil_analysis_report: Optional[str] = None) -> Dict[str, Any]:
    """Create an oil analysis record"""
    session = SessionLocal()
    try:
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Parse dates
        try:
            parsed_date = parse_date_string(date)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        parsed_oil_analysis_date = None
        parsed_next_oil_analysis_date = None
        
        if oil_analysis_date:
            try:
                parsed_oil_analysis_date = parse_date_string(oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid oil analysis date: {str(e)}"}
        
        if next_oil_analysis_date:
            try:
                parsed_next_oil_analysis_date = parse_date_string(next_oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid next oil analysis date: {str(e)}"}
        
        # Create record
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=parsed_date,
            description=description,
            cost=0.0,  # Oil analysis records have no cost
            mileage=mileage,
            date_estimated=False,
            oil_change_interval=None,  # Not an oil change
            is_oil_change=False,  # Not an oil change
            # Oil analysis fields
            oil_analysis_date=parsed_oil_analysis_date,
            next_oil_analysis_date=parsed_next_oil_analysis_date,
            oil_analysis_cost=oil_analysis_cost,
            iron_level=iron_level,
            aluminum_level=aluminum_level,
            copper_level=copper_level,
            viscosity=viscosity,
            tbn=tbn,
            fuel_dilution=fuel_dilution,
            coolant_contamination=coolant_contamination,
            driving_conditions=driving_conditions,
            oil_consumption_notes=oil_consumption_notes,
            linked_oil_change_id=linked_oil_change_id,
            oil_analysis_report=oil_analysis_report
        )
        
        session.add(record)
        session.commit()
        session.refresh(record)
        
        return {"success": True, "record": record}
    except Exception as e:
        session.rollback()
        print(f"Error creating oil analysis record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def create_placeholder_oil_analysis(vehicle_id: int, date: str, description: str, mileage: int, 
                                   linked_oil_change_id: int) -> Dict[str, Any]:
    """Create a placeholder oil analysis record linked to an oil change"""
    return create_oil_analysis_record(
        vehicle_id=vehicle_id,
        date=date,
        description=description,
        mileage=mileage,
        linked_oil_change_id=linked_oil_change_id
    )

def create_maintenance_record(vehicle_id: int, date: str, description: str, cost: float, mileage: Optional[int], 
                            oil_change_interval: Optional[int] = None,
                            oil_analysis_date: Optional[str] = None,
                            next_oil_analysis_date: Optional[str] = None,
                            oil_analysis_cost: Optional[float] = None,
                            iron_level: Optional[float] = None,
                            aluminum_level: Optional[float] = None,
                            copper_level: Optional[float] = None,
                            viscosity: Optional[float] = None,
                            tbn: Optional[float] = None,
                            fuel_dilution: Optional[float] = None,
                            coolant_contamination: Optional[bool] = None,
                            driving_conditions: Optional[str] = None,
                            oil_consumption_notes: Optional[str] = None,
                            linked_oil_change_id: Optional[int] = None,
                            oil_analysis_report: Optional[str] = None,
                            photo_path: Optional[str] = None,
                            photo_description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new maintenance record"""
    session = SessionLocal()
    try:
        # Verify vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Parse date
        try:
            parsed_date = parse_date_string(date)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        # Handle missing mileage - use placeholder and mark date as estimated for sorting
        if mileage is None:
            mileage = 0  # Placeholder mileage
            date_estimated = True
        else:
            date_estimated = False
        
        # Parse oil analysis dates if provided
        parsed_oil_analysis_date = None
        parsed_next_oil_analysis_date = None
        
        if oil_analysis_date:
            try:
                parsed_oil_analysis_date = parse_date_string(oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid oil analysis date: {str(e)}"}
        
        if next_oil_analysis_date:
            try:
                parsed_next_oil_analysis_date = parse_date_string(next_oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid next oil analysis date: {str(e)}"}
        
        # Determine if this is an oil change based on oil_change_interval
        is_oil_change = oil_change_interval is not None
        
        # Create maintenance record
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=parsed_date,
            description=description,
            cost=cost,
            mileage=mileage,
            date_estimated=date_estimated,
            oil_change_interval=oil_change_interval,
            is_oil_change=is_oil_change,  # Set based on detection logic
            # Oil analysis fields
            oil_analysis_date=parsed_oil_analysis_date,
            next_oil_analysis_date=parsed_next_oil_analysis_date,
            oil_analysis_cost=oil_analysis_cost,
            iron_level=iron_level,
            aluminum_level=aluminum_level,
            copper_level=copper_level,
            viscosity=viscosity,
            tbn=tbn,
            fuel_dilution=fuel_dilution,
            coolant_contamination=coolant_contamination,
            driving_conditions=driving_conditions,
            oil_consumption_notes=oil_consumption_notes,
            linked_oil_change_id=linked_oil_change_id,
            oil_analysis_report=oil_analysis_report,
            # Photo documentation fields
            photo_path=photo_path,
            photo_description=photo_description
        )
        
        session.add(record)
        session.commit()
        session.refresh(record)
        
        # If this is an oil change, automatically create future maintenance record
        future_maintenance_result = None
        if is_oil_change and oil_change_interval and mileage:
            try:
                # Extract oil type from description if possible
                oil_type = "Conventional"  # Default
                if "synthetic" in description.lower():
                    oil_type = "Synthetic"
                elif "blend" in description.lower():
                    oil_type = "Blend"
                
                future_maintenance_result = create_future_oil_change_record(
                    vehicle_id=vehicle_id,
                    current_mileage=mileage,
                    oil_change_interval=oil_change_interval,
                    oil_type=oil_type,
                    estimated_cost=cost
                )
            except Exception as e:
                print(f"Warning: Could not create future oil change record: {e}")
                future_maintenance_result = {"success": False, "error": str(e)}
        
        return {
            "success": True, 
            "record": record,
            "future_maintenance": future_maintenance_result
        }
    except Exception as e:
        session.rollback()
        print(f"Error creating maintenance record: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def update_maintenance_record(record_id: int, vehicle_id: int, date: str, description: str, cost: float, mileage: Optional[int], 
                            oil_change_interval: Optional[int] = None,
                            # Oil change fields
                            is_oil_change: Optional[bool] = None,
                            oil_type: Optional[str] = None,
                            oil_brand: Optional[str] = None,
                            oil_filter_brand: Optional[str] = None,
                            oil_filter_part_number: Optional[str] = None,
                            oil_cost: Optional[float] = None,
                            filter_cost: Optional[float] = None,
                            labor_cost: Optional[float] = None,
                            # Oil analysis fields
                            oil_analysis_date: Optional[str] = None,
                            next_oil_analysis_date: Optional[str] = None,
                            oil_analysis_cost: Optional[float] = None,
                            iron_level: Optional[float] = None,
                            aluminum_level: Optional[float] = None,
                            copper_level: Optional[float] = None,
                            viscosity: Optional[float] = None,
                            tbn: Optional[float] = None,
                            fuel_dilution: Optional[float] = None,
                            coolant_contamination: Optional[bool] = None,
                            driving_conditions: Optional[str] = None,
                            oil_consumption_notes: Optional[str] = None,
                            oil_analysis_report: Optional[str] = None,
                            # Photo documentation fields
                            photo_path: Optional[str] = None,
                            photo_description: Optional[str] = None) -> Dict[str, Any]:
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
            parsed_date = parse_date_string(date)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        # Handle missing mileage - use placeholder and mark date as estimated for sorting
        if mileage is None:
            mileage = 0  # Placeholder mileage
            date_estimated = True
        else:
            date_estimated = False
        
        # Parse oil analysis dates if provided
        parsed_oil_analysis_date = None
        parsed_next_oil_analysis_date = None
        
        if oil_analysis_date:
            try:
                parsed_oil_analysis_date = parse_date_string(oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid oil analysis date: {str(e)}"}
        
        if next_oil_analysis_date:
            try:
                parsed_next_oil_analysis_date = parse_date_string(next_oil_analysis_date)
            except ValueError as e:
                return {"success": False, "error": f"Invalid next oil analysis date: {str(e)}"}
        
        # Update record
        record.vehicle_id = vehicle_id
        record.date = parsed_date
        record.description = description
        record.cost = cost
        record.mileage = mileage
        record.date_estimated = date_estimated
        record.oil_change_interval = oil_change_interval
        # Oil change fields
        record.is_oil_change = is_oil_change if is_oil_change is not None else False
        record.oil_type = oil_type
        record.oil_brand = oil_brand
        record.oil_filter_brand = oil_filter_brand
        record.oil_filter_part_number = oil_filter_part_number
        record.oil_cost = oil_cost
        record.filter_cost = filter_cost
        record.labor_cost = labor_cost
        # Oil analysis fields
        record.oil_analysis_date = parsed_oil_analysis_date
        record.next_oil_analysis_date = parsed_next_oil_analysis_date
        record.oil_analysis_cost = oil_analysis_cost
        record.iron_level = iron_level
        record.aluminum_level = aluminum_level
        record.copper_level = copper_level
        record.viscosity = viscosity
        record.tbn = tbn
        record.fuel_dilution = fuel_dilution
        record.coolant_contamination = coolant_contamination
        record.driving_conditions = driving_conditions
        record.oil_consumption_notes = oil_consumption_notes
        record.oil_analysis_report = oil_analysis_report
        # Photo documentation fields
        record.photo_path = photo_path
        record.photo_description = photo_description
        
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
        result = import_csv(file_content.encode('utf-8'), vehicle_id, session, "skip")
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

def export_vehicles_csv(vehicle_ids: Optional[List[int]] = None) -> str:
    """Export vehicles to CSV format"""
    try:
        if vehicle_ids:
            # Export specific vehicles
            vehicles = [get_vehicle_by_id(vid) for vid in vehicle_ids if get_vehicle_by_id(vid)]
        else:
            # Export all vehicles
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

def export_maintenance_csv(vehicle_id: Optional[int] = None) -> str:
    """Export maintenance records to CSV format"""
    session = SessionLocal()
    try:
        # Get records with vehicle info while session is active
        from sqlalchemy.orm import selectinload
        
        if vehicle_id:
            # Export single vehicle maintenance
            records = session.execute(
                select(MaintenanceRecord)
                .options(selectinload(MaintenanceRecord.vehicle))
                .where(MaintenanceRecord.vehicle_id == vehicle_id)
                .order_by(MaintenanceRecord.date.desc())
            ).scalars().all()
        else:
            # Export all maintenance records
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

def export_vehicles_pdf(vehicle_ids: Optional[List[int]] = None) -> bytes:
    """Export vehicles to PDF format using ReportLab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from io import BytesIO
        
        # Get vehicle data
        if vehicle_ids:
            vehicles = [get_vehicle_by_id(vid) for vid in vehicle_ids if get_vehicle_by_id(vid)]
        else:
            vehicles = get_all_vehicles()
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        title = Paragraph("Vehicle Export Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Create table data
        data = [['Name', 'Make', 'Model', 'Year', 'VIN']]
        for vehicle in vehicles:
            data.append([
                vehicle.name,
                vehicle.make,
                vehicle.model,
                str(vehicle.year),
                vehicle.vin or 'N/A'
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
        
    except Exception as e:
        print(f"Error exporting vehicles to PDF: {e}")
        return b""

def export_maintenance_pdf(vehicle_id: Optional[int] = None) -> bytes:
    """Export maintenance records to PDF format using ReportLab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from io import BytesIO
        
        session = SessionLocal()
        try:
            # Get maintenance records
            from sqlalchemy.orm import selectinload
            
            if vehicle_id:
                records = session.execute(
                    select(MaintenanceRecord)
                    .options(selectinload(MaintenanceRecord.vehicle))
                    .where(MaintenanceRecord.vehicle_id == vehicle_id)
                    .order_by(MaintenanceRecord.date.desc())
                ).scalars().all()
            else:
                records = session.execute(
                    select(MaintenanceRecord)
                    .options(selectinload(MaintenanceRecord.vehicle))
                    .order_by(MaintenanceRecord.date.desc())
                ).scalars().all()
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            if vehicle_id:
                vehicle = get_vehicle_by_id(vehicle_id)
                title_text = f"Maintenance Records - {vehicle.name if vehicle else 'Vehicle'}"
            else:
                title_text = "All Maintenance Records"
            
            title = Paragraph(title_text, title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # Create table data
            data = [['Vehicle', 'Date', 'Description', 'Cost', 'Mileage']]
            for record in records:
                vehicle_name = record.vehicle.name if record.vehicle else "Unknown"
                data.append([
                    vehicle_name,
                    record.date.strftime("%Y-%m-%d"),
                    record.description,
                    f"${record.cost:.2f}" if record.cost else "$0.00",
                    str(record.mileage)
                ])
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            return pdf_content
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"Error exporting maintenance to PDF: {e}")
        return b""
        
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
        
        # Sort by mileage (highest first) to get the most current mileage
        mileage_data.sort(key=lambda x: x['mileage'], reverse=True)
        
        # Get the highest mileage overall (most current)
        current_mileage = mileage_data[0]['mileage']
        
        # Find the record that provides this mileage
        current_record = mileage_data[0]
        
        # Determine confidence level
        confidence = 'high'
        if len(mileage_data) > 1:
            # Multiple sources - check for consistency
            mileage_range = max(m['mileage'] for m in mileage_data) - min(m['mileage'] for m in mileage_data)
            if mileage_range > 1000:  # More than 1000 mile difference
                confidence = 'medium'
        elif len(mileage_data) == 1:
            confidence = 'medium'  # Only one data point
        
        # Calculate days since last update
        days_since_update = (datetime.now().date() - current_record['date']).days if current_record['date'] else None
        
        result = {
            'current_mileage': current_mileage,
            'source': current_record['source'],
            'source_date': current_record['date'],
            'source_description': current_record['description'],
            'record_id': current_record['record_id'],
            'confidence': confidence,
            'days_since_update': days_since_update,
            'all_sources': mileage_data,
            'total_sources': len(mileage_data)
        }
        
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

def create_future_oil_change_record(vehicle_id: int, 
                                   current_mileage: int, 
                                   oil_change_interval: int,
                                   oil_type: str = "Conventional",
                                   estimated_cost: float = 50.0) -> Dict[str, Any]:
    """Create a future maintenance record for the next oil change"""
    try:
        session = next(get_session())
        
        # Calculate next due mileage
        next_due_mileage = current_mileage + oil_change_interval
        
        # Calculate next due date (6 months from now as fallback)
        from datetime import date, timedelta
        next_due_date = date.today() + timedelta(days=180)  # 6 months
        
        # Create future maintenance record
        future_maintenance = FutureMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type="Oil Change",
            target_mileage=next_due_mileage,
            target_date=next_due_date,
            mileage_reminder=100,  # Remind 100 miles before
            date_reminder=30,      # Remind 30 days before
            estimated_cost=estimated_cost,
            notes=f"Next oil change - {oil_type} oil, {oil_change_interval:,} mile interval",
            is_recurring=True,
            recurrence_interval_miles=oil_change_interval,
            recurrence_interval_months=6,  # 6 months as time-based fallback
            is_active=True
        )
        
        session.add(future_maintenance)
        session.commit()
        session.refresh(future_maintenance)
        
        return {
            "success": True,
            "future_maintenance_id": future_maintenance.id,
            "next_due_mileage": next_due_mileage,
            "next_due_date": next_due_date,
            "message": f"Next oil change scheduled for {next_due_mileage:,} miles or {next_due_date}"
        }
        
    except Exception as e:
        print(f"Error creating future oil change record: {e}")
        return {
            "success": False,
            "error": f"Failed to create future oil change record: {str(e)}"
        }
    finally:
        session.close()

def get_future_maintenance_by_id(future_maintenance_id: int) -> Optional[FutureMaintenance]:
    """Get a specific future maintenance record by ID"""
    try:
        session = next(get_session())
        future_maintenance = session.execute(
            select(FutureMaintenance).where(FutureMaintenance.id == future_maintenance_id)
        ).scalar_one_or_none()
        return future_maintenance
    except Exception as e:
        print(f"Error getting future maintenance by ID: {e}")
        return None
    finally:
        session.close()

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
                    if record.vehicle_id == vehicle_id and record.is_oil_change
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
                'time': getattr(entry, 'time', None),  # Handle missing time column gracefully
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
                'time': getattr(entry, 'time', None),  # Handle missing time column gracefully
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
            oil_changes = [r for r in vehicle_records if r.is_oil_change]
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

# ============================================================================
# FUTURE MAINTENANCE OPERATIONS
# ============================================================================

def create_future_maintenance(
    vehicle_id: int,
    maintenance_type: str,
    target_date: str = "0",
    target_mileage: int = 0,
    mileage_reminder: int = 100,
    date_reminder: int = 30,
    estimated_cost: float = 0.0,
    parts_link: str = "",
    notes: str = "",
    is_recurring: bool = False,
    recurrence_interval_miles: int = 0,
    recurrence_interval_months: int = 0
) -> Dict[str, Any]:
    """Create a new future maintenance reminder"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        from datetime import datetime
        
        # Validate hierarchy: At least one of target_mileage or target_date must be provided
        # Treat "0" values as "not provided"
        has_target_mileage = target_mileage and target_mileage != 0
        has_target_date = target_date and target_date != "0" and target_date != ""
        
        if not has_target_mileage and not has_target_date:
            return {
                "success": False,
                "error": "At least one of Target Mileage or Target Date must be provided"
            }
        
        # Parse the target date if provided
        parsed_date = None
        if target_date and target_date != "0" and target_date != "":
            try:
                parsed_date = parse_date_string(target_date)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Convert "0" values to None for database storage
        db_target_mileage = target_mileage if target_mileage and target_mileage != 0 else None
        db_target_date = parsed_date
        
        # Validate vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Create future maintenance record
        future_maintenance = FutureMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            target_date=db_target_date,
            target_mileage=db_target_mileage,
            mileage_reminder=mileage_reminder,
            date_reminder=date_reminder,
            estimated_cost=estimated_cost,
            parts_link=parts_link,
            notes=notes,
            is_recurring=is_recurring,
            recurrence_interval_miles=recurrence_interval_miles,
            recurrence_interval_months=recurrence_interval_months,
            created_at=datetime.now().date(),
            updated_at=datetime.now().date()
        )
        
        session.add(future_maintenance)
        session.commit()
        session.refresh(future_maintenance)
        
        return {
            "success": True,
            "message": "Future maintenance reminder created successfully",
            "future_maintenance_id": future_maintenance.id
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": f"Failed to create future maintenance: {str(e)}"
        }
    finally:
        session.close()

def update_future_maintenance(
    future_maintenance_id: int,
    vehicle_id: int,
    maintenance_type: str,
    target_date: str = "0",
    target_mileage: int = 0,
    mileage_reminder: int = 100,
    date_reminder: int = 30,
    estimated_cost: float = 0.0,
    parts_link: str = "",
    notes: str = "",
    is_recurring: bool = False,
    recurrence_interval_miles: int = 0,
    recurrence_interval_months: int = 0
) -> Dict[str, Any]:
    """Update an existing future maintenance reminder"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        from datetime import datetime
        
        # Validate hierarchy: At least one of target_mileage or target_date must be provided
        # Treat "0" values as "not provided"
        has_target_mileage = target_mileage and target_mileage != 0
        has_target_date = target_date and target_date != "0" and target_date != ""
        
        if not has_target_mileage and not has_target_date:
            return {
                "success": False,
                "error": "At least one of Target Mileage or Target Date must be provided"
            }
        
        # Get the existing record
        future_maintenance = session.execute(
            select(FutureMaintenance).where(FutureMaintenance.id == future_maintenance_id)
        ).scalar_one_or_none()
        
        if not future_maintenance:
            return {
                "success": False,
                "error": "Future maintenance reminder not found"
            }
        
        # Parse the target date if provided
        parsed_date = None
        if target_date and target_date != "0" and target_date != "":
            try:
                parsed_date = parse_date_string(target_date)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Convert "0" values to None for database storage
        db_target_mileage = target_mileage if target_mileage and target_mileage != 0 else None
        db_target_date = parsed_date
        
        # Validate vehicle exists
        vehicle = session.execute(select(Vehicle).where(Vehicle.id == vehicle_id)).scalar_one_or_none()
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        # Update the fields
        future_maintenance.vehicle_id = vehicle_id
        future_maintenance.maintenance_type = maintenance_type
        future_maintenance.target_date = db_target_date
        future_maintenance.target_mileage = db_target_mileage
        future_maintenance.mileage_reminder = mileage_reminder
        future_maintenance.date_reminder = date_reminder
        future_maintenance.estimated_cost = estimated_cost
        future_maintenance.parts_link = parts_link
        future_maintenance.notes = notes
        future_maintenance.is_recurring = is_recurring
        future_maintenance.recurrence_interval_miles = recurrence_interval_miles
        future_maintenance.recurrence_interval_months = recurrence_interval_months
        future_maintenance.updated_at = datetime.now().date()
        
        session.commit()
        
        return {
            "success": True,
            "message": "Future maintenance reminder updated successfully"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": f"Failed to update future maintenance: {str(e)}"
        }
    finally:
        session.close()

def get_all_future_maintenance() -> List[Dict[str, Any]]:
    """Get all future maintenance reminders with vehicle information"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        
        # Get all future maintenance records with vehicle info
        future_maintenance = session.execute(
            select(FutureMaintenance, Vehicle)
            .join(Vehicle, FutureMaintenance.vehicle_id == Vehicle.id)
            .where(FutureMaintenance.is_active == True)
            .order_by(FutureMaintenance.target_date)
        ).all()
        
        # Convert to list of dictionaries
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
                'parts_link': fm.parts_link,
                'notes': fm.notes,
                'is_recurring': fm.is_recurring,
                'recurrence_interval_miles': fm.recurrence_interval_miles,
                'recurrence_interval_months': fm.recurrence_interval_months,
                'is_active': fm.is_active,
                'created_at': fm.created_at,
                'updated_at': fm.updated_at
            })
        
        return result
        
    except Exception as e:
        return []
    finally:
        session.close()

def get_future_maintenance_by_vehicle(vehicle_id: int) -> List[Dict[str, Any]]:
    """Get future maintenance reminders for a specific vehicle"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        
        future_maintenance = session.execute(
            select(FutureMaintenance)
            .where(FutureMaintenance.vehicle_id == vehicle_id)
            .where(FutureMaintenance.is_active == True)
            .order_by(FutureMaintenance.target_date)
        ).scalars().all()
        
        # Convert to list of dictionaries
        result = []
        for fm in future_maintenance:
            result.append({
                'id': fm.id,
                'vehicle_id': fm.vehicle_id,
                'maintenance_type': fm.maintenance_type,
                'target_mileage': fm.target_mileage,
                'target_date': fm.target_date,
                'mileage_reminder': fm.mileage_reminder,
                'date_reminder': fm.date_reminder,
                'estimated_cost': fm.estimated_cost,
                'parts_link': fm.parts_link,
                'notes': fm.notes,
                'is_recurring': fm.is_recurring,
                'recurrence_interval_miles': fm.recurrence_interval_miles,
                'recurrence_interval_months': fm.recurrence_interval_months,
                'is_active': fm.is_active,
                'created_at': fm.created_at,
                'updated_at': fm.updated_at
            })
        
        return result
        
    except Exception as e:
        return []
    finally:
        session.close()

def get_future_maintenance_by_id(future_maintenance_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific future maintenance reminder by ID"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        
        future_maintenance = session.execute(
            select(FutureMaintenance).where(FutureMaintenance.id == future_maintenance_id)
        ).scalar_one_or_none()
        
        if not future_maintenance:
            return None
        
        # Convert to dictionary
        result = {
            'id': future_maintenance.id,
            'vehicle_id': future_maintenance.vehicle_id,
            'maintenance_type': future_maintenance.maintenance_type,
            'target_mileage': future_maintenance.target_mileage,
            'target_date': future_maintenance.target_date,
            'mileage_reminder': future_maintenance.mileage_reminder,
            'date_reminder': future_maintenance.date_reminder,
            'estimated_cost': future_maintenance.estimated_cost,
            'parts_link': future_maintenance.parts_link,
            'notes': future_maintenance.notes,
            'is_recurring': future_maintenance.is_recurring,
            'recurrence_interval_miles': future_maintenance.recurrence_interval_miles,
            'recurrence_interval_months': future_maintenance.recurrence_interval_months,
            'is_active': future_maintenance.is_active,
            'created_at': future_maintenance.created_at,
            'updated_at': future_maintenance.updated_at
        }
        
        return result
        
    except Exception as e:
        return None
    finally:
        session.close()

def delete_future_maintenance(future_maintenance_id: int) -> Dict[str, Any]:
    """Delete a future maintenance reminder"""
    session = SessionLocal()
    try:
        from models import FutureMaintenance
        
        future_maintenance = session.execute(
            select(FutureMaintenance).where(FutureMaintenance.id == future_maintenance_id)
        ).scalar_one_or_none()
        
        if not future_maintenance:
            return {"success": False, "error": "Future maintenance reminder not found"}
        
        session.delete(future_maintenance)
        session.commit()
        
        return {
            "success": True,
            "message": "Future maintenance reminder deleted successfully"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": f"Failed to delete future maintenance: {str(e)}"
        }
    finally:
        session.close()

# ============================================================================
# FUTURE MAINTENANCE TRIGGER FUNCTIONS
# ============================================================================

def get_triggered_future_maintenance(vehicle_id: int, current_mileage: int) -> List[Dict[str, Any]]:
    """Get future maintenance items that have met their notification triggers"""
    try:
        future_items = get_future_maintenance_by_vehicle(vehicle_id)
        triggered_items = []
        
        for item in future_items:
            # Check if mileage trigger is met
            mileage_triggered = False
            if item.get('target_mileage') and item.get('mileage_reminder'):
                reminder_threshold = item['target_mileage'] - item['mileage_reminder']
                if current_mileage >= reminder_threshold:
                    mileage_triggered = True
            
            # Check if date trigger is met
            date_triggered = False
            if item.get('target_date') and item.get('date_reminder'):
                from datetime import date, timedelta
                today = date.today()
                
                # target_date is already a date object from the database
                target_date = item['target_date']
                
                # Calculate the reminder threshold (target_date - reminder_days)
                reminder_threshold = target_date - timedelta(days=item['date_reminder'])
                
                if today >= reminder_threshold:
                    date_triggered = True
            
            # Only include items that have met their triggers
            if mileage_triggered or date_triggered:
                # Calculate urgency based on what's actually overdue
                is_mileage_overdue = False
                is_date_overdue = False
                
                # Check if mileage is overdue (past target)
                if item.get('target_mileage'):
                    is_mileage_overdue = current_mileage >= item['target_mileage']
                
                # Check if date is overdue (past target)
                if item.get('target_date'):
                    from datetime import date
                    today = date.today()
                    is_date_overdue = today >= item['target_date']
                
                # Determine urgency level with priority on mileage for vehicles
                if is_mileage_overdue:
                    urgency = "high"  # Mileage overdue - RED
                elif mileage_triggered and not is_mileage_overdue:
                    urgency = "medium"  # Approaching mileage target - YELLOW
                elif is_date_overdue:
                    urgency = "high"  # Date overdue - RED
                elif date_triggered:
                    urgency = "low"  # Approaching date - BLUE
                else:
                    urgency = "low"  # Default - BLUE
                

                
                triggered_items.append({
                    **item,
                    'urgency': urgency,
                    'mileage_triggered': mileage_triggered,
                    'date_triggered': date_triggered
                })
        
        return triggered_items
        
    except Exception as e:
        return []

def get_all_vehicles_triggered_maintenance() -> Dict[int, List[Dict[str, Any]]]:
    """Get triggered future maintenance for all vehicles"""
    try:
        vehicles = get_all_vehicles()
        vehicles_current_mileage = get_all_vehicles_current_mileage()
        
        result = {}
        for vehicle in vehicles:
            current_mileage = vehicles_current_mileage.get(vehicle.id, {}).get('current_mileage', 0)
            triggered_items = get_triggered_future_maintenance(vehicle.id, current_mileage)
            
            if triggered_items:  # Only include vehicles with triggered items
                result[vehicle.id] = triggered_items
        
        return result
        
    except Exception as e:
        print(f"Error getting all vehicles triggered maintenance: {e}")
        return {}
