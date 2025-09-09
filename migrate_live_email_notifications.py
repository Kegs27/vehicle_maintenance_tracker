#!/usr/bin/env python3
"""
Migrate live PostgreSQL database to add email notification fields
This script adds email notification capabilities to the live database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Vehicle, FutureMaintenance, EmailSubscription
from database import get_database_url

def migrate_live_database():
    """Add email notification fields to the live PostgreSQL database"""
    
    # Get database URL
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔧 Migrating live PostgreSQL database...")
    print(f"Database URL: {database_url[:50]}...")
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if email_notification_email column already exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.columns 
                    WHERE table_name = 'vehicle' 
                    AND column_name = 'email_notification_email'
                """))
                
                if result.fetchone()[0] > 0:
                    print("✅ Email notification fields already exist in Vehicle table")
                else:
                    # Add email notification fields to Vehicle table
                    print("Adding email notification fields to Vehicle table...")
                    conn.execute(text("""
                        ALTER TABLE vehicle 
                        ADD COLUMN email_notification_email VARCHAR(255)
                    """))
                    
                    conn.execute(text("""
                        ALTER TABLE vehicle 
                        ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT FALSE
                    """))
                    
                    conn.execute(text("""
                        ALTER TABLE vehicle 
                        ADD COLUMN email_reminder_frequency INTEGER DEFAULT 7
                    """))
                    
                    conn.execute(text("""
                        ALTER TABLE vehicle 
                        ADD COLUMN last_email_sent DATE
                    """))
                    
                    print("✅ Successfully added email notification fields to Vehicle table")
                
                # Check if email_sent column already exists in FutureMaintenance
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.columns 
                    WHERE table_name = 'futuremaintenance' 
                    AND column_name = 'email_sent'
                """))
                
                if result.fetchone()[0] > 0:
                    print("✅ Email fields already exist in FutureMaintenance table")
                else:
                    # Add email notification fields to FutureMaintenance table
                    print("Adding email notification fields to FutureMaintenance table...")
                    conn.execute(text("""
                        ALTER TABLE futuremaintenance 
                        ADD COLUMN email_sent BOOLEAN DEFAULT FALSE
                    """))
                    
                    conn.execute(text("""
                        ALTER TABLE futuremaintenance 
                        ADD COLUMN last_email_reminder DATE
                    """))
                    
                    print("✅ Successfully added email notification fields to FutureMaintenance table")
                
                # Check if EmailSubscription table exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = 'emailsubscription'
                """))
                
                if result.fetchone()[0] > 0:
                    print("✅ EmailSubscription table already exists")
                else:
                    # Create EmailSubscription table
                    print("Creating EmailSubscription table...")
                    SQLModel.metadata.create_all(engine, tables=[EmailSubscription.__table__])
                    print("✅ Successfully created EmailSubscription table")
                
                # Commit transaction
                trans.commit()
                print("🎉 Live database migration completed successfully!")
                return True
                
            except Exception as e:
                # Rollback transaction on error
                trans.rollback()
                print(f"❌ Error during migration, rolling back: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting live database migration...")
    
    success = migrate_live_database()
    
    if success:
        print("🎉 Live database migration completed successfully!")
    else:
        print("❌ Live database migration failed")
        sys.exit(1)
