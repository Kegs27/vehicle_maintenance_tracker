#!/usr/bin/env python3
"""
Database migration script to add enhanced oil change fields to MaintenanceRecord table.
Run this script to update existing database schema.
"""

import sqlite3
import os
from pathlib import Path

def migrate_sqlite():
    """Migrate SQLite database to add oil change fields"""
    db_path = Path("vehicle_maintenance.db")
    
    if not db_path.exists():
        print("SQLite database not found. Skipping migration.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List of new fields to add
        new_fields = [
            ("is_oil_change", "BOOLEAN DEFAULT 0"),
            ("oil_type", "VARCHAR(20)"),
            ("oil_brand", "VARCHAR(50)"),
            ("oil_filter_brand", "VARCHAR(50)"),
            ("oil_filter_part_number", "VARCHAR(50)"),
            ("oil_cost", "REAL"),
            ("filter_cost", "REAL"),
            ("labor_cost", "REAL"),
            ("oil_analysis_report", "TEXT"),
            ("oil_analysis_date", "DATE"),
            ("next_oil_analysis_date", "DATE"),
            ("oil_analysis_cost", "REAL"),
            ("iron_level", "REAL"),
            ("aluminum_level", "REAL"),
            ("copper_level", "REAL"),
            ("viscosity", "REAL"),
            ("tbn", "REAL"),
            ("fuel_dilution", "REAL"),
            ("coolant_contamination", "BOOLEAN"),
            ("driving_conditions", "VARCHAR(50)"),
            ("oil_consumption_notes", "TEXT")
        ]
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(maintenancerecord)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Add new fields
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                print(f"Adding '{field_name}' column to MaintenanceRecord table...")
                cursor.execute(f"ALTER TABLE maintenancerecord ADD COLUMN {field_name} {field_type}")
            else:
                print(f"✅ Column '{field_name}' already exists in MaintenanceRecord table")
        
        conn.commit()
        print("✅ Successfully updated SQLite MaintenanceRecord table")
            
    except Exception as e:
        print(f"❌ Error migrating SQLite database: {e}")
    finally:
        conn.close()

def migrate_postgres():
    """Migrate PostgreSQL database to add oil change fields"""
    try:
        import psycopg2
        
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/vehicle_maintenance')
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # List of new fields to add
        new_fields = [
            ("is_oil_change", "BOOLEAN DEFAULT FALSE"),
            ("oil_type", "VARCHAR(20)"),
            ("oil_brand", "VARCHAR(50)"),
            ("oil_filter_brand", "VARCHAR(50)"),
            ("oil_filter_part_number", "VARCHAR(50)"),
            ("oil_cost", "REAL"),
            ("filter_cost", "REAL"),
            ("labor_cost", "REAL"),
            ("oil_analysis_report", "TEXT"),
            ("oil_analysis_date", "DATE"),
            ("next_oil_analysis_date", "DATE"),
            ("oil_analysis_cost", "REAL"),
            ("iron_level", "REAL"),
            ("aluminum_level", "REAL"),
            ("copper_level", "REAL"),
            ("viscosity", "REAL"),
            ("tbn", "REAL"),
            ("fuel_dilution", "REAL"),
            ("coolant_contamination", "BOOLEAN"),
            ("driving_conditions", "VARCHAR(50)"),
            ("oil_consumption_notes", "TEXT")
        ]
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'maintenancerecord'
        """)
        
        existing_columns = [column[0] for column in cursor.fetchall()]
        
        # Add new fields
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                print(f"Adding '{field_name}' column to MaintenanceRecord table...")
                cursor.execute(f"ALTER TABLE maintenancerecord ADD COLUMN {field_name} {field_type}")
            else:
                print(f"✅ Column '{field_name}' already exists in MaintenanceRecord table")
        
        conn.commit()
        print("✅ Successfully updated PostgreSQL MaintenanceRecord table")
            
    except ImportError:
        print("⚠️  psycopg2 not installed. Skipping PostgreSQL migration.")
    except Exception as e:
        print(f"❌ Error migrating PostgreSQL database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Starting database migration for enhanced oil change fields...")
    
    # Try both database types
    migrate_sqlite()
    migrate_postgres()
    
    print("✅ Migration complete!")
