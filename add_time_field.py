#!/usr/bin/env python3
"""
Database migration script to add time field to FuelEntry table.
Run this script to update existing database schema.
"""

import sqlite3
import os
from pathlib import Path

def migrate_sqlite():
    """Migrate SQLite database to add time field"""
    db_path = Path("vehicle_maintenance.db")
    
    if not db_path.exists():
        print("SQLite database not found. Skipping migration.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if time column already exists
        cursor.execute("PRAGMA table_info(fuelentry)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'time' not in columns:
            print("Adding 'time' column to FuelEntry table...")
            cursor.execute("ALTER TABLE fuelentry ADD COLUMN time TEXT")
            conn.commit()
            print("✅ Successfully added 'time' column to FuelEntry table")
        else:
            print("✅ 'time' column already exists in FuelEntry table")
            
    except Exception as e:
        print(f"❌ Error migrating SQLite database: {e}")
    finally:
        conn.close()

def migrate_postgres():
    """Migrate PostgreSQL database to add time field"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get database URL from environment or use default
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/vehicle_maintenance')
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if time column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fuelentry' AND column_name = 'time'
        """)
        
        if not cursor.fetchone():
            print("Adding 'time' column to FuelEntry table...")
            cursor.execute("ALTER TABLE fuelentry ADD COLUMN time VARCHAR(10)")
            conn.commit()
            print("✅ Successfully added 'time' column to FuelEntry table")
        else:
            print("✅ 'time' column already exists in FuelEntry table")
            
    except ImportError:
        print("⚠️  psycopg2 not installed. Skipping PostgreSQL migration.")
    except Exception as e:
        print(f"❌ Error migrating PostgreSQL database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Starting database migration for FuelEntry time field...")
    
    # Try both database types
    migrate_sqlite()
    migrate_postgres()
    
    print("✅ Migration complete!")
