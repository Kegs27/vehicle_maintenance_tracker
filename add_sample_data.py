#!/usr/bin/env python3
"""
Script to add sample data to the vehicle maintenance tracker database
"""

import os
import sys
from datetime import date, timedelta
from random import randint, choice

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import our data operations
from data_operations import (
    create_vehicle, 
    create_maintenance_record,
    get_all_vehicles,
    get_all_maintenance_records
)

def add_sample_vehicles():
    """Add sample vehicles to the database"""
    vehicles = [
        {
            "name": "Honda Civic",
            "year": 2019,
            "make": "Honda",
            "model": "Civic",
            "vin": "1HGBH41JXMN109186"
        },
        {
            "name": "Toyota Camry",
            "year": 2020,
            "make": "Toyota", 
            "model": "Camry",
            "vin": "4T1BF1FK5CU000001"
        },
        {
            "name": "Ford F-150",
            "year": 2018,
            "make": "Ford",
            "model": "F-150",
            "vin": "1FTFW1ET5DFC10312"
        }
    ]
    
    added_vehicles = []
    for vehicle_data in vehicles:
        try:
            result = create_vehicle(**vehicle_data)
            if result["success"]:
                vehicle = result["vehicle"]
                added_vehicles.append(vehicle)
                print(f"✅ Added vehicle: {vehicle.name}")
            else:
                print(f"❌ Error adding vehicle {vehicle_data['name']}: {result['error']}")
        except Exception as e:
            print(f"❌ Error adding vehicle {vehicle_data['name']}: {e}")
    
    return added_vehicles

def add_sample_maintenance_records(vehicles):
    """Add sample maintenance records for the vehicles"""
    
    # Define maintenance types
    maintenance_types = [
        "Oil change",
        "Tire rotation", 
        "Brake inspection",
        "Air filter replacement",
        "Transmission service",
        "Battery replacement",
        "Coolant flush",
        "Spark plug replacement"
    ]
    
    # Get today's date
    today = date.today()
    
    records_added = 0
    
    for vehicle in vehicles:
        # Starting mileage for this vehicle
        current_mileage = randint(50000, 120000)
        
        # Add records going back 6 months with realistic progression
        for i in range(15):  # 15 records per vehicle
            # Go back in time
            record_date = today - timedelta(days=randint(1, 180))
            
            # Increment mileage realistically (200-800 miles per record)
            if i > 0:
                current_mileage += randint(200, 800)
            
            # Choose maintenance type
            maintenance_type = choice(maintenance_types)
            
            # Add cost variation
            if "oil" in maintenance_type.lower():
                cost = randint(25, 60)
            elif "tire" in maintenance_type.lower():
                cost = randint(40, 80)
            elif "brake" in maintenance_type.lower():
                cost = randint(150, 400)
            elif "battery" in maintenance_type.lower():
                cost = randint(100, 200)
            elif "transmission" in maintenance_type.lower():
                cost = randint(200, 500)
            else:
                cost = randint(30, 150)
            
            try:
                result = create_maintenance_record(
                    vehicle_id=vehicle.id,
                    date=record_date.strftime("%Y-%m-%d"),  # Convert date to string
                    mileage=current_mileage,
                    description=maintenance_type,
                    cost=float(cost)
                )
                
                if result["success"]:
                    records_added += 1
                    
                    # Show progress for recent records
                    if record_date >= today - timedelta(days=30):
                        print(f"📅 Recent: {vehicle.name} - {maintenance_type} at {current_mileage:,} miles")
                else:
                    print(f"❌ Error adding record for {vehicle.name}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Error adding record for {vehicle.name}: {e}")
    
    print(f"\n✅ Added {records_added} maintenance records total")
    return records_added

def show_summary():
    """Show summary of data in the database"""
    vehicles = get_all_vehicles()
    records = get_all_maintenance_records()
    
    print(f"\n📊 DATABASE SUMMARY:")
    print(f"   Vehicles: {len(vehicles)}")
    print(f"   Maintenance Records: {len(records)}")
    
    # Show recent activity
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    recent_records = [r for r in records if r.date >= thirty_days_ago]
    
    print(f"   Recent Activity (30 days): {len(recent_records)} records")
    
    # Show vehicle details
    print(f"\n🚗 VEHICLES:")
    for vehicle in vehicles:
        vehicle_records = [r for r in records if r.vehicle_id == vehicle.id]
        if vehicle_records:
            latest_record = max(vehicle_records, key=lambda x: x.date)
            print(f"   {vehicle.name} ({vehicle.year} {vehicle.make} {vehicle.model})")
            print(f"      Current mileage: {latest_record.mileage:,}")
            print(f"      Records: {len(vehicle_records)}")

def main():
    """Main function to add sample data"""
    print("🚀 Adding sample data to Vehicle Maintenance Tracker...")
    print("=" * 60)
    
    # Check if we already have data
    existing_vehicles = get_all_vehicles()
    existing_records = get_all_maintenance_records()
    
    if existing_vehicles or existing_records:
        print(f"⚠️  Database already has data:")
        print(f"   Vehicles: {len(existing_vehicles)}")
        print(f"   Records: {len(existing_records)}")
        
        response = input("\nDo you want to add MORE sample data? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Add sample vehicles
    print("\n1️⃣ Adding sample vehicles...")
    vehicles = add_sample_vehicles()
    
    # If no new vehicles were added, use existing vehicles
    if not vehicles:
        print("ℹ️  No new vehicles added. Using existing vehicles...")
        vehicles = get_all_vehicles()
        if not vehicles:
            print("❌ No vehicles found in database. Cannot continue.")
            return
        print(f"📋 Found {len(vehicles)} existing vehicles:")
        for vehicle in vehicles:
            print(f"   - {vehicle.name} ({vehicle.year} {vehicle.make} {vehicle.model})")
    
    # Add sample maintenance records
    print("\n2️⃣ Adding sample maintenance records...")
    records_count = add_sample_maintenance_records(vehicles)
    
    # Show summary
    show_summary()
    
    print(f"\n🎉 Sample data added successfully!")
    print(f"📱 Visit http://localhost:8000/ to see the enhanced dashboard in action!")
    print(f"💡 Try clicking 'View Details' on the dashboard cards to test the modals.")

if __name__ == "__main__":
    main()
