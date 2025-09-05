#!/usr/bin/env python3
"""
Simple script to run database migration on live server
This will add all missing oil change and oil analysis columns
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def run_migration():
    """Run migration on live PostgreSQL database"""
    
    # Get database URL from environment (Render sets this automatically)
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found. Using local SQLite for testing...")
        database_url = "sqlite:///vehicle_maintenance.db"
    
    print(f"🔗 Connecting to database...")
    print(f"📍 Database: {'PostgreSQL (Live)' if 'postgresql' in database_url else 'SQLite (Local)'}")
    
    try:
        # Handle different database URL formats
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check existing columns
            if 'postgresql' in database_url:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'maintenancerecord'
                    ORDER BY ordinal_position
                """))
            else:
                result = conn.execute(text("PRAGMA table_info(maintenancerecord)"))
            
            existing_columns = [row[0] for row in result] if 'postgresql' in database_url else [row[1] for row in result]
            print(f"📋 Existing columns ({len(existing_columns)}): {existing_columns[:5]}...")
            
            # Define all new columns needed
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
                ('driving_conditions', 'VARCHAR(50)'),
                ('oil_consumption_notes', 'TEXT'),
                ('linked_oil_change_id', 'INTEGER')
            ]
            
            # Add missing columns
            added_count = 0
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f'ALTER TABLE maintenancerecord ADD COLUMN {col_name} {col_type}'))
                        print(f'✅ Added: {col_name}')
                        added_count += 1
                    except (OperationalError, ProgrammingError) as e:
                        print(f'⚠️ Error adding {col_name}: {e}')
                else:
                    print(f'⏭️ Already exists: {col_name}')
            
            # Commit changes
            conn.commit()
            
            print(f"\n🎉 Migration completed!")
            print(f"📊 Added {added_count} new columns")
            print(f"✅ Database is now ready for all features!")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    success = run_migration()
    
    if success:
        print("\n✅ Migration successful!")
    else:
        print("\n❌ Migration failed.")
