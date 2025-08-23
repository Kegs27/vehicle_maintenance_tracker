#!/usr/bin/env python3
"""
Script to update existing oil change records with interval information
"""

import os
import sys
from datetime import date

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import our data operations
from data_operations import get_all_maintenance_records
from database import SessionLocal
from models import MaintenanceRecord
from sqlalchemy import select

def update_oil_change_intervals():
    """Update existing oil change records with interval information"""
    
    session = SessionLocal()
    try:
        # Query oil change records directly from the session
        from models import MaintenanceRecord
        oil_changes = session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.description.ilike('%oil%')
            )
        ).scalars().all()
        
        print(f"🔍 Found {len(oil_changes)} oil change records to update")
        
        # Update each oil change record with appropriate interval
        for record in oil_changes:
                          # Set interval based on vehicle type/age (this could be enhanced)
              # For now, use 5,000 miles as default
            record.oil_change_interval = 5000
            
            print(f"✅ Updated {record.description} for vehicle {record.vehicle_id} with {record.oil_change_interval:,} mile interval")
        
        # Commit changes
        session.commit()
        print(f"\n🎉 Successfully updated {len(oil_changes)} oil change records")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating oil change records: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def show_oil_change_records():
    """Show all oil change records with their intervals"""
    records = get_all_maintenance_records()
    oil_changes = [
        record for record in records 
        if 'oil' in record.description.lower()
    ]
    
    print(f"\n📊 OIL CHANGE RECORDS WITH INTERVALS:")
    for record in oil_changes:
        interval = record.oil_change_interval or "Not set"
        print(f"   Vehicle {record.vehicle_id}: {record.description}")
        print(f"      Date: {record.date}, Mileage: {record.mileage:,}")
        print(f"      Interval: {interval} miles")
        print("   ---")

if __name__ == "__main__":
    print("🚀 Updating oil change records with interval information...")
    print("=" * 60)
    
    # Update the records
    update_oil_change_intervals()
    
    # Show the updated records
    show_oil_change_records()
    
    print(f"\n💡 Now the dashboard will use actual oil change intervals!")
    print(f"📱 Visit http://localhost:8000/ to see the enhanced oil change reminders!")
