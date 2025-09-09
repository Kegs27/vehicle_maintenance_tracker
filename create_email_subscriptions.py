#!/usr/bin/env python3
"""
Create EmailSubscription table for vehicle notification management
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import EmailSubscription
from database import get_database_url

def create_email_subscription_table():
    """Create the EmailSubscription table"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔧 Creating EmailSubscription table...")
    
    try:
        # Create the table
        SQLModel.metadata.create_all(engine, tables=[EmailSubscription.__table__])
        print("✅ EmailSubscription table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating EmailSubscription table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating EmailSubscription table...")
    
    success = create_email_subscription_table()
    
    if success:
        print("🎉 EmailSubscription table creation completed successfully!")
    else:
        print("❌ EmailSubscription table creation failed")
        sys.exit(1)
