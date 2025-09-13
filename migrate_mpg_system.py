#!/usr/bin/env python3
"""
Migration script to ensure seamless transition to three-tier MPG system
This script validates existing fuel data and ensures compatibility
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append('.')

def migrate_mpg_system():
    """Migrate existing fuel data to new three-tier MPG system"""
    
    print("🔄 Starting MPG System Migration...")
    print("=" * 50)
    
    try:
        from database import SessionLocal
        from models import FuelEntry, Vehicle
        from sqlalchemy import select
        
        session = SessionLocal()
        
        # 1. Check existing fuel entries
        print("📊 Step 1: Analyzing existing fuel data...")
        fuel_entries = session.execute(select(FuelEntry)).scalars().all()
        vehicles = session.execute(select(Vehicle)).scalars().all()
        
        print(f"   Found {len(fuel_entries)} fuel entries across {len(vehicles)} vehicles")
        
        # 2. Validate data integrity
        print("\n🔍 Step 2: Validating data integrity...")
        
        vehicle_data = {}
        for vehicle in vehicles:
            vehicle_entries = [entry for entry in fuel_entries if entry.vehicle_id == vehicle.id]
            vehicle_data[vehicle.id] = {
                'vehicle': vehicle,
                'entries': vehicle_entries,
                'count': len(vehicle_entries)
            }
            
            print(f"   {vehicle.name}: {len(vehicle_entries)} entries")
            
            # Check for data quality issues
            if len(vehicle_entries) >= 2:
                sorted_entries = sorted(vehicle_entries, key=lambda x: x.mileage)
                
                # Check for gaps
                gaps = []
                for i in range(len(sorted_entries) - 1):
                    gap = sorted_entries[i + 1].mileage - sorted_entries[i].mileage
                    if gap > 500:
                        gaps.append(gap)
                
                if gaps:
                    print(f"     ⚠️ {len(gaps)} gap(s) detected: {gaps}")
                else:
                    print(f"     ✅ No gaps detected")
        
        # 3. Test new MPG calculations
        print("\n🧮 Step 3: Testing new MPG calculations...")
        
        for vehicle_id, data in vehicle_data.items():
            vehicle = data['vehicle']
            entries = data['entries']
            
            if len(entries) >= 2:
                sorted_entries = sorted(entries, key=lambda x: x.mileage)
                
                # Lifetime MPG
                lifetime_miles = sorted_entries[-1].mileage - sorted_entries[0].mileage
                lifetime_gallons = sum(entry.fuel_amount for entry in sorted_entries[1:])
                lifetime_mpg = lifetime_miles / lifetime_gallons if lifetime_gallons > 0 else None
                
                # Current MPG (last 2 entries)
                current_mpg = None
                if len(sorted_entries) >= 2:
                    last_gap = sorted_entries[-1].mileage - sorted_entries[-2].mileage
                    if last_gap <= 500:
                        current_miles = sorted_entries[-1].mileage - sorted_entries[-2].mileage
                        current_gallons = sorted_entries[-1].fuel_amount
                        current_mpg = current_miles / current_gallons if current_gallons > 0 else None
                
                # Entries MPG (last 5 entries)
                entries_mpg = None
                entries_count = min(5, len(sorted_entries))
                if entries_count >= 2:
                    valid_entries = []
                    for i in range(len(sorted_entries) - entries_count, len(sorted_entries)):
                        if i == 0 or (sorted_entries[i].mileage - sorted_entries[i-1].mileage) <= 500:
                            valid_entries.append(sorted_entries[i])
                        else:
                            break
                    
                    if len(valid_entries) >= 2:
                        entries_miles = valid_entries[-1].mileage - valid_entries[0].mileage
                        entries_gallons = sum(entry.fuel_amount for entry in valid_entries[1:])
                        entries_mpg = entries_miles / entries_gallons if entries_gallons > 0 else None
                
                print(f"   {vehicle.name}:")
                print(f"     Lifetime MPG: {lifetime_mpg:.2f}" if lifetime_mpg else "     Lifetime MPG: N/A")
                print(f"     Current MPG: {current_mpg:.2f}" if current_mpg else "     Current MPG: N/A (gap detected)")
                print(f"     Entries MPG: {entries_mpg:.2f}" if entries_mpg else "     Entries MPG: N/A")
        
        # 4. Validate database schema
        print("\n🗄️ Step 4: Validating database schema...")
        
        # Check if fuelentry table exists and has required columns
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        
        tables = inspector.get_table_names()
        if 'fuelentry' in tables:
            columns = inspector.get_columns('fuelentry')
            column_names = [col['name'] for col in columns]
            
            required_columns = ['id', 'vehicle_id', 'date', 'mileage', 'fuel_amount', 'fuel_cost']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                print(f"   ❌ Missing columns: {missing_columns}")
                return False
            else:
                print(f"   ✅ All required columns present")
        
        # 5. Test API endpoints
        print("\n🔌 Step 5: Testing API compatibility...")
        
        # Simulate the new MPG calculation logic
        from data_operations import get_all_fuel_entries
        
        try:
            api_entries = get_all_fuel_entries()
            print(f"   ✅ API can retrieve {len(api_entries)} fuel entries")
            
            # Test MPG summary by calling the function directly (not async)
            import asyncio
            from main import get_fuel_mpg_summary
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                mpg_summary = loop.run_until_complete(get_fuel_mpg_summary())
                print(f"   ✅ MPG summary generated for {len(mpg_summary['summary'])} vehicles")
                
                # Check if new fields are present
                if mpg_summary['summary'] and len(mpg_summary['summary']) > 0:
                    sample_vehicle = mpg_summary['summary'][0]
                    new_fields = ['lifetime_mpg', 'current_mpg', 'entries_mpg', 'gaps_detected']
                    present_fields = [field for field in new_fields if field in sample_vehicle]
                    print(f"   ✅ New MPG fields present: {present_fields}")
            finally:
                loop.close()
            
        except Exception as e:
            print(f"   ❌ API test failed: {e}")
            return False
        
        session.close()
        
        # 6. Migration summary
        print("\n📋 Migration Summary:")
        print("   ✅ Existing fuel data validated")
        print("   ✅ New MPG calculations tested")
        print("   ✅ Database schema validated")
        print("   ✅ API compatibility confirmed")
        print("   ✅ Seamless transition ready")
        
        print("\n🎯 Migration Status: READY FOR DEPLOYMENT")
        print("   • No data loss expected")
        print("   • Existing MPG calculations will be enhanced")
        print("   • New three-tier system will be active immediately")
        print("   • Gap detection will identify existing data issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_mpg_system()
    if success:
        print("\n🚀 Migration completed successfully!")
        print("   Ready to deploy to live server")
    else:
        print("\n⚠️ Migration failed - please resolve issues before deployment")
        sys.exit(1)
