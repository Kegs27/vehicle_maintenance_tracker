"""
Script to fix existing maintenance records that were incorrectly marked as oil changes.
This script should be run on the live server to clean up bad data.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def fix_bad_oil_change_records():
    """Fix maintenance records that were incorrectly marked as oil changes."""
    
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
                print("🔍 Looking for incorrectly marked oil change records...")
                
                # Find records that are marked as oil changes but shouldn't be
                # These are records with descriptions that don't contain oil-related keywords
                result = connection.execute(text("""
                    SELECT id, description, is_oil_change 
                    FROM maintenancerecord 
                    WHERE is_oil_change = true 
                    AND (
                        description ILIKE '%fuel filter%' OR
                        description ILIKE '%air filter%' OR
                        description ILIKE '%brake%' OR
                        description ILIKE '%tire%' OR
                        description ILIKE '%battery%' OR
                        description ILIKE '%spark plug%' OR
                        description ILIKE '%belt%' OR
                        description ILIKE '%hose%' OR
                        description ILIKE '%gasket%' OR
                        description ILIKE '%sensor%' OR
                        description ILIKE '%pump%' OR
                        description ILIKE '%alternator%' OR
                        description ILIKE '%starter%' OR
                        description ILIKE '%transmission%' OR
                        description ILIKE '%clutch%' OR
                        description ILIKE '%suspension%' OR
                        description ILIKE '%exhaust%' OR
                        description ILIKE '%coolant%' OR
                        description ILIKE '%thermostat%' OR
                        description ILIKE '%radiator%' OR
                        description ILIKE '%water pump%'
                    )
                    AND (
                        description NOT ILIKE '%oil%' OR
                        (description ILIKE '%oil%' AND description ILIKE '%filter%')
                    )
                """))
                
                bad_records = result.fetchall()
                
                if not bad_records:
                    print("✅ No incorrectly marked oil change records found!")
                    return True
                
                print(f"📋 Found {len(bad_records)} incorrectly marked oil change records:")
                for record in bad_records:
                    print(f"  - ID {record[0]}: {record[1][:50]}...")
                
                # Ask for confirmation
                response = input("\n🤔 Do you want to fix these records? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Operation cancelled")
                    return False
                
                # Fix the records
                fixed_count = 0
                for record in bad_records:
                    record_id = record[0]
                    
                    # Update the record to not be an oil change
                    connection.execute(text("""
                        UPDATE maintenancerecord 
                        SET is_oil_change = false,
                            oil_change_interval = NULL,
                            oil_type = NULL,
                            oil_brand = NULL,
                            oil_filter_brand = NULL,
                            oil_filter_part_number = NULL,
                            oil_cost = NULL,
                            filter_cost = NULL,
                            labor_cost = NULL
                        WHERE id = :record_id
                    """), {"record_id": record_id})
                    
                    fixed_count += 1
                    print(f"✅ Fixed record ID {record_id}")
                
                # Commit transaction
                trans.commit()
                print(f"\n🎉 Successfully fixed {fixed_count} incorrectly marked oil change records!")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Fix failed: {e}")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing incorrectly marked oil change records...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
    
    success = fix_bad_oil_change_records()
    
    if success:
        print("🎉 Database cleanup completed successfully!")
        sys.exit(0)
    else:
        print("💥 Database cleanup failed!")
        sys.exit(1)
