#!/usr/bin/env python3
"""
Migration script to add photo_path and photo_description columns to maintenancerecord table
This script works with both SQLite and PostgreSQL databases
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_database_url():
    """Get database URL from environment or use SQLite fallback"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"Using PostgreSQL: {database_url[:20]}...")
        return database_url
    else:
        print("Using SQLite fallback")
        return "sqlite:///vehicle_maintenance.db"

def run_migration():
    """Run the migration to add photo columns"""
    database_url = get_database_url()
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if columns already exist
            if 'postgresql' in database_url:
                # PostgreSQL
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'maintenancerecord' 
                    AND column_name IN ('photo_path', 'photo_description')
                """)
            else:
                # SQLite
                check_query = text("""
                    SELECT name FROM pragma_table_info('maintenancerecord') 
                    WHERE name IN ('photo_path', 'photo_description')
                """)
            
            existing_columns = [row[0] for row in conn.execute(check_query)]
            
            if 'photo_path' not in existing_columns:
                print("Adding photo_path column...")
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_path VARCHAR(255)"))
                else:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_path VARCHAR(255)"))
                conn.commit()
                print("✅ photo_path column added successfully")
            else:
                print("✅ photo_path column already exists")
            
            if 'photo_description' not in existing_columns:
                print("Adding photo_description column...")
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_description TEXT"))
                else:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_description TEXT"))
                conn.commit()
                print("✅ photo_description column added successfully")
            else:
                print("✅ photo_description column already exists")
        
        print("🎉 Migration completed successfully!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def run_migration_with_existing_engine(engine):
    """Run the migration using an existing database engine"""
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            database_url = str(engine.url)
            if 'postgresql' in database_url:
                # PostgreSQL
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'maintenancerecord' 
                    AND column_name IN ('photo_path', 'photo_description')
                """)
            else:
                # SQLite
                check_query = text("""
                    SELECT name FROM pragma_table_info('maintenancerecord') 
                    WHERE name IN ('photo_path', 'photo_description')
                """)
            
            existing_columns = [row[0] for row in conn.execute(check_query)]
            
            if 'photo_path' not in existing_columns:
                print("Adding photo_path column...")
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_path VARCHAR(255)"))
                else:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_path VARCHAR(255)"))
                conn.commit()
                print("✅ photo_path column added successfully")
            else:
                print("✅ photo_path column already exists")
            
            if 'photo_description' not in existing_columns:
                print("Adding photo_description column...")
                if 'postgresql' in database_url:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_description TEXT"))
                else:
                    conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN photo_description TEXT"))
                conn.commit()
                print("✅ photo_description column added successfully")
            else:
                print("✅ photo_description column already exists")
        
        print("🎉 Migration completed successfully!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting photo columns migration...")
    success = run_migration()
    sys.exit(0 if success else 1)
