"""
Database migration script to make the description column nullable in the live database.
This script should be run on the live server to fix the NOT NULL constraint issue.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def migrate_description_nullable():
    """Make the description column nullable in the MaintenanceRecord table."""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                # Check if we're using PostgreSQL
                if 'postgresql' in database_url:
                    print("Detected PostgreSQL database")
                    
                    # Check current column definition
                    result = connection.execute(text("""
                        SELECT column_name, is_nullable, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'maintenancerecord' 
                        AND column_name = 'description'
                    """))
                    
                    column_info = result.fetchone()
                    if column_info:
                        print(f"Current description column: {column_info}")
                        
                        if column_info[1] == 'NO':  # is_nullable = 'NO'
                            print("Making description column nullable...")
                            
                            # Alter column to allow NULL
                            connection.execute(text("""
                                ALTER TABLE maintenancerecord 
                                ALTER COLUMN description DROP NOT NULL
                            """))
                            
                            print("✅ Successfully made description column nullable")
                        else:
                            print("✅ Description column is already nullable")
                    else:
                        print("❌ Description column not found in maintenancerecord table")
                        return False
                
                elif 'sqlite' in database_url:
                    print("Detected SQLite database")
                    print("SQLite doesn't support ALTER COLUMN directly")
                    print("For SQLite, the schema change should be handled by SQLModel migrations")
                    print("✅ SQLite migration not needed - handled by model changes")
                
                else:
                    print(f"❌ Unsupported database type in URL: {database_url}")
                    return False
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting description column migration...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
    
    success = migrate_description_nullable()
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
