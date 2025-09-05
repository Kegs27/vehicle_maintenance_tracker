#!/usr/bin/env python3
"""
Database migration script for live PostgreSQL database
Adds all oil change and oil analysis columns to MaintenanceRecord table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def migrate_live_database():
    """Run migration on live PostgreSQL database"""
    
    # Get database URL from environment (Render sets this automatically)
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("This script should be run on the live Render server")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check existing columns in PostgreSQL
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'maintenancerecord'
                ORDER BY ordinal_position
            """))
            
            existing_columns = [row[0] for row in result]
            print(f"📋 Existing columns: {existing_columns}")
            
            # Define all oil change and oil analysis columns
            new_columns = [
                ('oil_change_interval', 'INTEGER'),
                ('is_oil_change', 'BOOLEAN DEFAULT FALSE'),
                ('oil_type', 'VARCHAR(20)'),
                ('oil_brand', 'VARCHAR(50)'),
                ('oil_filter_brand', 'VARCHAR(50)'),
                ('oil_filter_part_number', 'VARCHAR(50)'),
                ('oil_cost', 'FLOAT'),
                ('filter_cost', 'FLOAT'),
                ('labor_cost', 'FLOAT'),
                ('oil_analysis_report', 'TEXT'),
                ('oil_analysis_date', 'DATE'),
                ('next_oil_analysis_date', 'DATE'),
                ('oil_analysis_cost', 'FLOAT'),
                ('iron_level', 'FLOAT'),
                ('aluminum_level', 'FLOAT'),
                ('copper_level', 'FLOAT'),
                ('viscosity', 'FLOAT'),
                ('tbn', 'FLOAT'),
                ('fuel_dilution', 'FLOAT'),
                ('coolant_contamination', 'BOOLEAN'),
                ('driving_conditions', 'TEXT'),
                ('oil_consumption_notes', 'TEXT'),
                ('linked_oil_change_id', 'INTEGER')
            ]
            
            # Add missing columns
            added_count = 0
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f'ALTER TABLE maintenancerecord ADD COLUMN {col_name} {col_type}'))
                        print(f'✅ Added column: {col_name} ({col_type})')
                        added_count += 1
                    except (OperationalError, ProgrammingError) as e:
                        print(f'⚠️ Column {col_name} error: {e}')
                else:
                    print(f'⏭️ Column {col_name} already exists')
            
            # Commit changes
            conn.commit()
            
            print(f"\n🎉 Migration completed!")
            print(f"📊 Added {added_count} new columns")
            print(f"✅ Live database is now ready for oil change and oil analysis features")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting live database migration...")
    success = migrate_live_database()
    
    if success:
        print("\n✅ Migration successful! Your live app now has all features.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
