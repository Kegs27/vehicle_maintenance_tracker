#!/usr/bin/env python3
"""
Add email notification fields to Vehicle model
This script adds email notification capabilities to vehicles
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Vehicle, FutureMaintenance
from database import get_database_url

def add_email_notification_fields():
    """Add email notification fields to the database"""
    
    # Get database URL
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔧 Adding email notification fields to Vehicle table...")
    
    try:
        with engine.connect() as conn:
            # Check if email_notification_email column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('vehicle') 
                WHERE name = 'email_notification_email'
            """))
            
            if result.fetchone()[0] > 0:
                print("✅ Email notification fields already exist")
                return True
            
            # Add email notification fields
            conn.execute(text("""
                ALTER TABLE vehicle 
                ADD COLUMN email_notification_email VARCHAR(255)
            """))
            
            conn.execute(text("""
                ALTER TABLE vehicle 
                ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE vehicle 
                ADD COLUMN email_reminder_frequency INTEGER DEFAULT 7
            """))
            
            conn.execute(text("""
                ALTER TABLE vehicle 
                ADD COLUMN last_email_sent DATE
            """))
            
            conn.commit()
            print("✅ Successfully added email notification fields")
            return True
            
    except Exception as e:
        print(f"❌ Error adding email notification fields: {e}")
        return False

def add_future_maintenance_email_fields():
    """Add email notification fields to FutureMaintenance table"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔧 Adding email notification fields to FutureMaintenance table...")
    
    try:
        with engine.connect() as conn:
            # Check if email_sent column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('futuremaintenance') 
                WHERE name = 'email_sent'
            """))
            
            if result.fetchone()[0] > 0:
                print("✅ FutureMaintenance email fields already exist")
                return True
            
            # Add email notification fields
            conn.execute(text("""
                ALTER TABLE futuremaintenance 
                ADD COLUMN email_sent BOOLEAN DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE futuremaintenance 
                ADD COLUMN last_email_reminder DATE
            """))
            
            conn.commit()
            print("✅ Successfully added FutureMaintenance email fields")
            return True
            
    except Exception as e:
        print(f"❌ Error adding FutureMaintenance email fields: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting email notification migration...")
    
    success1 = add_email_notification_fields()
    success2 = add_future_maintenance_email_fields()
    
    if success1 and success2:
        print("🎉 Email notification migration completed successfully!")
    else:
        print("❌ Email notification migration failed")
        sys.exit(1)
