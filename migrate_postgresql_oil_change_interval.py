#!/usr/bin/env python3
"""
PostgreSQL Migration Script for Vehicle Maintenance Tracker
Adds oil_change_interval column to maintenancerecord table
"""

import os
from database import SessionLocal, engine
from sqlalchemy import text

def migrate_postgresql():
    """Add oil_change_interval column to maintenancerecord table"""
    print("🔄 Starting PostgreSQL migration...")
    
    # Check if we're using PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
        print("❌ This script is for PostgreSQL databases only")
        return
    
    print(f"✅ Using PostgreSQL database")
    
    try:
        # Create a connection to execute raw SQL
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'maintenancerecord' 
                AND column_name = 'oil_change_interval'
            """))
            
            if result.fetchone():
                print("✅ oil_change_interval column already exists")
                return
            
            # Add the column
            print("🔧 Adding oil_change_interval column...")
            connection.execute(text("""
                ALTER TABLE maintenancerecord 
                ADD COLUMN oil_change_interval INTEGER
            """))
            
            # Add comment to the column
            connection.execute(text("""
                COMMENT ON COLUMN maintenancerecord.oil_change_interval 
                IS 'Miles until next oil change (for oil change records)'
            """))
            
            # Commit the changes
            connection.commit()
            
            print("✅ Successfully added oil_change_interval column")
            
            # Verify the column was added
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'maintenancerecord' 
                AND column_name = 'oil_change_interval'
            """))
            
            column_info = result.fetchone()
            if column_info:
                print(f"✅ Column verified: {column_info[0]} ({column_info[1]}, nullable: {column_info[2]})")
            else:
                print("❌ Column verification failed")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_postgresql()
