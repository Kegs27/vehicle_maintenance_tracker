#!/usr/bin/env python3
"""
Database migration script to add oil_change_interval column to MaintenanceRecord table
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from database import SessionLocal, engine
from sqlalchemy import text

def migrate_add_oil_change_interval():
    """Add oil_change_interval column to MaintenanceRecord table"""
    
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    # Check if column already exists
    session = SessionLocal()
    try:
        # Try to query the column to see if it exists
        result = session.execute(text("PRAGMA table_info(maintenancerecord)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'oil_change_interval' in columns:
            print("✅ Column 'oil_change_interval' already exists!")
            return True
        
        print("🔍 Column 'oil_change_interval' not found. Adding it now...")
        
        # Add the column
        session.execute(text("ALTER TABLE maintenancerecord ADD COLUMN oil_change_interval INTEGER"))
        session.commit()
        
        print("✅ Successfully added 'oil_change_interval' column!")
        
        # Verify the column was added
        result = session.execute(text("PRAGMA table_info(maintenancerecord)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'oil_change_interval' in columns:
            print("✅ Column verification successful!")
            return True
        else:
            print("❌ Column verification failed!")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        session.close()

def show_table_structure():
    """Show the current table structure"""
    session = SessionLocal()
    try:
        result = session.execute(text("PRAGMA table_info(maintenancerecord)"))
        columns = result.fetchall()
        
        print(f"\n📊 CURRENT TABLE STRUCTURE:")
        print(f"{'Column Name':<20} {'Type':<15} {'Not Null':<10} {'Default':<10}")
        print("-" * 60)
        
        for col in columns:
            print(f"{col[1]:<20} {col[2]:<15} {col[3]:<10} {col[4] or 'NULL':<10}")
            
    except Exception as e:
        print(f"❌ Error showing table structure: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("🔧 Database Migration: Adding oil_change_interval column")
    print("=" * 60)
    
    # Run the migration
    success = migrate_add_oil_change_interval()
    
    if success:
        # Show the updated table structure
        show_table_structure()
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"💡 Now you can run update_oil_change_intervals.py to set the intervals!")
    else:
        print(f"\n❌ Migration failed!")
        print(f"💡 Please check the error messages above.")
