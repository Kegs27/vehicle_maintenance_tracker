#!/usr/bin/env python3
"""
Script to add a test vehicle with comprehensive test data to LOCAL SQLite database:
- 1 vehicle
- 3 oil changes
- 20 fuel entries
- 10 maintenance records
- 3 future maintenance records (not due, due soon, past due)
"""

import os
import sys
from datetime import date, timedelta, datetime
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Force local SQLite database
local_db_path = Path(__file__).parent / "vehicle_maintenance.db"
local_db_url = f"sqlite:///{local_db_path}"

# Create engine and session for local database
local_engine = create_engine(local_db_url, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)

# Import models AFTER setting up local engine
from models import Vehicle, Account, MaintenanceRecord, FuelEntry, FutureMaintenance

# Initialize database tables
SQLModel.metadata.create_all(local_engine)

DEFAULT_OWNER_ID = "kory"
import random

def get_or_create_default_account():
    """Get the default account or create one if it doesn't exist."""
    session = SessionLocal()
    try:
        account = session.execute(
            select(Account).where(Account.owner_user_id == DEFAULT_OWNER_ID, Account.is_default == True)
        ).scalar_one_or_none()
        
        if account:
            print(f"Using existing default account: {account.name} (ID: {account.id})")
            return account
        
        # Create a default account
        account = Account(
            name="Default Account",
            owner_user_id=DEFAULT_OWNER_ID,
            is_default=True
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        print(f"Created default account: {account.name} (ID: {account.id})")
        return account
    except Exception as e:
        session.rollback()
        print(f"Error with account: {e}")
        raise
    finally:
        session.close()

def delete_existing_test_vehicle(account_id: str):
    """Delete existing test vehicle if it exists."""
    session = SessionLocal()
    try:
        vehicle = session.execute(
            select(Vehicle)
            .where(Vehicle.account_id == account_id, Vehicle.name == "Test Vehicle")
        ).scalar_one_or_none()
        
        if vehicle:
            print(f"Deleting existing test vehicle: {vehicle.name} (ID: {vehicle.id})")
            session.delete(vehicle)
            session.commit()
            print("Existing test vehicle deleted")
    except Exception as e:
        session.rollback()
        print(f"Error deleting existing test vehicle: {e}")
    finally:
        session.close()

def create_test_vehicle(account_id: str):
    """Create a test vehicle."""
    # Delete existing test vehicle first
    delete_existing_test_vehicle(account_id)
    
    session = SessionLocal()
    try:
        # Generate unique VIN
        vin = f"TEST{random.randint(100000, 999999)}"
        
        # Check for duplicate VIN
        existing_vin = session.execute(
            select(Vehicle).where(Vehicle.vin == vin)
        ).scalar_one_or_none()
        
        if existing_vin:
            vin = f"TEST{random.randint(100000, 999999)}"
        
        vehicle = Vehicle(
            name="Test Vehicle",
            make="Toyota",
            model="Camry",
            year=2020,
            vin=vin,
            account_id=account_id
        )
        session.add(vehicle)
        session.commit()
        session.refresh(vehicle)
        print(f"Created test vehicle: {vehicle.name} (ID: {vehicle.id})")
        return vehicle
    except Exception as e:
        session.rollback()
        print(f"Error creating vehicle: {e}")
        raise
    finally:
        session.close()

def add_oil_changes(vehicle_id: int):
    """Add 3 oil changes with increasing mileage."""
    session = SessionLocal()
    try:
        base_date = date.today()
        base_mileage = 30000
        
        oil_changes = [
            {
                "date": base_date - timedelta(days=180),
                "mileage": base_mileage,
                "oil_type": "5W-30",
                "oil_brand": "Mobil 1",
                "oil_filter_brand": "Fram",
                "oil_filter_part_number": "PH3614",
                "oil_cost": 45.99,
                "filter_cost": 8.99,
                "labor_cost": 20.00,
                "oil_change_interval": 5000,
                "description": "Full synthetic oil change"
            },
            {
                "date": base_date - timedelta(days=120),
                "mileage": base_mileage + 5000,
                "oil_type": "5W-30",
                "oil_brand": "Mobil 1",
                "oil_filter_brand": "Fram",
                "oil_filter_part_number": "PH3614",
                "oil_cost": 45.99,
                "filter_cost": 8.99,
                "labor_cost": 20.00,
                "oil_change_interval": 5000,
                "description": "Full synthetic oil change"
            },
            {
                "date": base_date - timedelta(days=60),
                "mileage": base_mileage + 10000,
                "oil_type": "5W-30",
                "oil_brand": "Mobil 1",
                "oil_filter_brand": "Fram",
                "oil_filter_part_number": "PH3614",
                "oil_cost": 45.99,
                "filter_cost": 8.99,
                "labor_cost": 20.00,
                "oil_change_interval": 5000,
                "description": "Full synthetic oil change"
            }
        ]
        
        for oil_change in oil_changes:
            record = MaintenanceRecord(
                vehicle_id=vehicle_id,
                date=oil_change["date"],
                mileage=oil_change["mileage"],
                description=oil_change["description"],
                cost=oil_change["oil_cost"] + oil_change["filter_cost"] + oil_change["labor_cost"],
                is_oil_change=True,
                oil_type=oil_change["oil_type"],
                oil_brand=oil_change["oil_brand"],
                oil_filter_brand=oil_change["oil_filter_brand"],
                oil_filter_part_number=oil_change["oil_filter_part_number"],
                oil_cost=oil_change["oil_cost"],
                filter_cost=oil_change["filter_cost"],
                labor_cost=oil_change["labor_cost"],
                oil_change_interval=oil_change["oil_change_interval"]
            )
            session.add(record)
        
        session.commit()
        print(f"Added 3 oil changes for vehicle {vehicle_id}")
    except Exception as e:
        session.rollback()
        print(f"Error adding oil changes: {e}")
        raise
    finally:
        session.close()

def add_fuel_entries(vehicle_id: int):
    """Add 20 fuel entries with increasing mileage."""
    session = SessionLocal()
    try:
        base_date = date.today() - timedelta(days=200)
        base_mileage = 30000
        current_mileage = base_mileage
        fuel_types = ["87", "89", "91"]
        driving_patterns = ["highway", "city", "mixed"]
        
        # Get the last oil change mileage to start fuel entries after that
        last_oil_change = session.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.vehicle_id == vehicle_id, MaintenanceRecord.is_oil_change == True)
            .order_by(MaintenanceRecord.mileage.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        if last_oil_change:
            current_mileage = last_oil_change.mileage + 100
        
        fuel_entries = []
        for i in range(20):
            # Increase mileage by 300-500 miles each time
            miles_since_last = random.randint(300, 500)
            current_mileage += miles_since_last
            
            # Calculate date (spread over ~200 days)
            entry_date = base_date + timedelta(days=int(i * 10))
            
            # Calculate fuel amount (assuming ~25 MPG average)
            fuel_amount = round(miles_since_last / 25 + random.uniform(-1, 1), 2)
            fuel_amount = max(8.0, min(20.0, fuel_amount))  # Clamp between 8-20 gallons
            
            # Calculate cost (assuming $3.50/gal average)
            price_per_gal = round(random.uniform(3.20, 3.80), 2)
            fuel_cost = round(fuel_amount * price_per_gal, 2)
            
            fuel_entry = FuelEntry(
                vehicle_id=vehicle_id,
                date=entry_date,
                time=f"{random.randint(6, 20):02d}:{random.randint(0, 59):02d}",
                mileage=current_mileage,
                fuel_amount=fuel_amount,
                fuel_cost=fuel_cost,
                fuel_type=random.choice(fuel_types),
                driving_pattern=random.choice(driving_patterns),
                notes=f"Fuel entry #{i+1}" if i % 5 == 0 else None
            )
            fuel_entries.append(fuel_entry)
        
        # Sort by date to ensure chronological order
        fuel_entries.sort(key=lambda x: (x.date, x.mileage))
        
        for entry in fuel_entries:
            session.add(entry)
        
        session.commit()
        print(f"Added 20 fuel entries for vehicle {vehicle_id}")
    except Exception as e:
        session.rollback()
        print(f"Error adding fuel entries: {e}")
        raise
    finally:
        session.close()

def add_maintenance_records(vehicle_id: int):
    """Add 10 maintenance records (non-oil change)."""
    session = SessionLocal()
    try:
        base_date = date.today()
        base_mileage = 30000
        
        maintenance_types = [
            {"description": "Tire Rotation", "cost": 25.00, "mileage_interval": 5000},
            {"description": "Brake Pad Replacement", "cost": 150.00, "mileage_interval": 30000},
            {"description": "Air Filter Replacement", "cost": 35.00, "mileage_interval": 15000},
            {"description": "Cabin Air Filter Replacement", "cost": 40.00, "mileage_interval": 20000},
            {"description": "Battery Replacement", "cost": 120.00, "mileage_interval": 50000},
            {"description": "Spark Plug Replacement", "cost": 80.00, "mileage_interval": 60000},
            {"description": "Transmission Fluid Change", "cost": 150.00, "mileage_interval": 60000},
            {"description": "Coolant Flush", "cost": 100.00, "mileage_interval": 50000},
            {"description": "Wiper Blade Replacement", "cost": 30.00, "mileage_interval": 12000},
            {"description": "Belt Replacement", "cost": 90.00, "mileage_interval": 60000}
        ]
        
        current_mileage = base_mileage
        current_date = base_date - timedelta(days=365)
        
        for i, maint_type in enumerate(maintenance_types):
            # Spread maintenance over time
            maint_date = current_date + timedelta(days=int(i * 40))
            maint_mileage = current_mileage + (i * 3500)
            
            record = MaintenanceRecord(
                vehicle_id=vehicle_id,
                date=maint_date,
                mileage=maint_mileage,
                description=maint_type["description"],
                cost=maint_type["cost"],
                is_oil_change=False
            )
            session.add(record)
        
        session.commit()
        print(f"Added 10 maintenance records for vehicle {vehicle_id}")
    except Exception as e:
        session.rollback()
        print(f"Error adding maintenance records: {e}")
        raise
    finally:
        session.close()

def add_future_maintenance(vehicle_id: int):
    """Add 3 future maintenance records: not due, due soon, past due."""
    session = SessionLocal()
    try:
        # Get current mileage from last fuel entry
        last_fuel_entry = session.execute(
            select(FuelEntry)
            .where(FuelEntry.vehicle_id == vehicle_id)
            .order_by(FuelEntry.mileage.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        current_mileage = last_fuel_entry.mileage if last_fuel_entry else 40000
        today = date.today()
        
        # 1. Not due - target date far in the future
        future_maintenance_1 = FutureMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type="Oil Change",
            target_date=today + timedelta(days=60),
            target_mileage=None,
            mileage_reminder=100,
            date_reminder=30,
            estimated_cost=75.00,
            notes="Not due - scheduled for future",
            is_recurring=False,
            is_active=True
        )
        
        # 2. Due soon - target date within 30 days
        future_maintenance_2 = FutureMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type="Tire Rotation",
            target_date=today + timedelta(days=15),
            target_mileage=None,
            mileage_reminder=100,
            date_reminder=30,
            estimated_cost=25.00,
            notes="Due soon - within 30 days",
            is_recurring=False,
            is_active=True
        )
        
        # 3. Past due - target date in the past
        future_maintenance_3 = FutureMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type="Brake Inspection",
            target_date=today - timedelta(days=10),
            target_mileage=current_mileage - 500,  # Also past due by mileage
            mileage_reminder=100,
            date_reminder=30,
            estimated_cost=50.00,
            notes="Past due - should have been done already",
            is_recurring=False,
            is_active=True
        )
        
        session.add(future_maintenance_1)
        session.add(future_maintenance_2)
        session.add(future_maintenance_3)
        
        session.commit()
        print(f"Added 3 future maintenance records for vehicle {vehicle_id}")
        print(f"  - Not due: Oil Change (target: {future_maintenance_1.target_date})")
        print(f"  - Due soon: Tire Rotation (target: {future_maintenance_2.target_date})")
        print(f"  - Past due: Brake Inspection (target: {future_maintenance_3.target_date}, mileage: {future_maintenance_3.target_mileage})")
    except Exception as e:
        session.rollback()
        print(f"Error adding future maintenance: {e}")
        raise
    finally:
        session.close()

def main():
    """Main function to create test vehicle and all test data."""
    print("=" * 60)
    print("Creating test vehicle with comprehensive test data")
    print("Using LOCAL SQLite database:", local_db_path)
    print("=" * 60)
    
    try:
        # Initialize database
        SQLModel.metadata.create_all(local_engine)
        print("\n1. Database initialized")
        
        # Get or create default account
        account = get_or_create_default_account()
        print(f"\n2. Account ready: {account.name}")
        
        # Create test vehicle
        vehicle = create_test_vehicle(account.id)
        print(f"\n3. Vehicle created: {vehicle.name} (ID: {vehicle.id})")
        
        # Add oil changes
        add_oil_changes(vehicle.id)
        
        # Add fuel entries
        add_fuel_entries(vehicle.id)
        
        # Add maintenance records
        add_maintenance_records(vehicle.id)
        
        # Add future maintenance
        add_future_maintenance(vehicle.id)
        
        print("\n" + "=" * 60)
        print("Test vehicle created successfully!")
        print(f"Vehicle ID: {vehicle.id}")
        print(f"Vehicle: {vehicle.year} {vehicle.make} {vehicle.model} ({vehicle.name})")
        print(f"Database: {local_db_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError creating test vehicle: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

