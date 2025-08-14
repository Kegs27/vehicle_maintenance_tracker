import csv
import re
from io import StringIO
from datetime import date, datetime
from dateutil import parser
from sqlmodel import select

class ImportResult:
    """Result of CSV import operation"""
    def __init__(self):
        self.total_rows = 0
        self.imported_rows = 0
        self.skipped_rows = 0
        self.duplicate_rows = 0
        self.skipped_details = []
        self.duplicate_details = []

def _parse_date_flexible(date_str: str) -> date:
    """Parse date from various formats"""
    if not date_str or not date_str.strip():
        return None
    
    # Remove common separators and normalize
    date_str = re.sub(r'[,/\-]', ' ', date_str.strip())
    
    try:
        # Try parsing with dateutil first (most flexible)
        parsed = parser.parse(date_str, fuzzy=True)
        return parsed.date()
    except:
        try:
            # Try common formats
            for fmt in ['%m %Y', '%m %d %Y', '%Y %m %d']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
        except:
            pass
    
    return None

def _parse_mileage_flexible(mileage_str: str) -> int:
    """Parse mileage from various formats"""
    if not mileage_str:
        return None
    
    # Remove common words and punctuation
    mileage_str = re.sub(r'[,\s]', '', mileage_str.lower())
    mileage_str = re.sub(r'miles?', '', mileage_str)
    mileage_str = re.sub(r'k$', '000', mileage_str)
    
    try:
        return int(mileage_str)
    except ValueError:
        return None

def _parse_cost_flexible(cost_str: str) -> float:
    """Parse cost from various formats"""
    if not cost_str:
        return None
    
    # Remove currency symbols and parentheses (negative amounts)
    cost_str = re.sub(r'[\$,\s]', '', cost_str)
    
    # Handle negative amounts in parentheses
    if cost_str.startswith('(') and cost_str.endswith(')'):
        cost_str = '-' + cost_str[1:-1]
    
    try:
        return float(cost_str)
    except ValueError:
        return None

def _check_duplicate_record(session, vehicle_id: int, date: date, mileage: int, description: str) -> bool:
    """Check if a maintenance record already exists with the same key fields"""
    from .models import MaintenanceRecord
    
    # Check for exact matches on key fields
    existing = session.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.date == date,
            MaintenanceRecord.mileage == mileage,
            MaintenanceRecord.description == description
        )
    ).scalars().first()
    
    return existing is not None

def _check_duplicate_record_no_date(session, vehicle_id: int, mileage: int, description: str) -> bool:
    """Check if a maintenance record already exists with the same key fields (no date)"""
    from .models import MaintenanceRecord
    
    # Check for exact matches on key fields
    existing = session.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.mileage == mileage,
            MaintenanceRecord.description == description
        )
    ).scalars().first()
    
    return existing is not None

def import_csv(csv_content: bytes, vehicle_id: int, session, handle_duplicates: str = "skip") -> ImportResult:
    result = ImportResult()
    csv_file = StringIO(csv_content.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    fieldnames_lower = [col.lower() for col in reader.fieldnames]
    required_columns = ['description']  # Only description is absolutely required
    if not all(col in fieldnames_lower for col in required_columns):
        result.errors.append(f"Missing required columns. Found: {reader.fieldnames}")
        return result
    
    # Check that we have either date OR mileage
    has_date = 'date' in fieldnames_lower
    has_mileage = 'mileage' in fieldnames_lower
    if not has_date and not has_mileage:
        result.errors.append("CSV must contain either 'date' or 'mileage' column (or both)")
        return result
    
    has_date = 'date' in fieldnames_lower
    has_cost = 'cost' in fieldnames_lower
    
    col_mapping = {}
    for col in reader.fieldnames:
        col_lower = col.lower()
        if col_lower in required_columns or col_lower == 'cost' or col_lower == 'date':
            col_mapping[col_lower] = col
    
    # Placeholder date for records without dates
    PLACEHOLDER_DATE = date(1900, 1, 1)
    
    for row_num, row in enumerate(reader, start=2):
        result.total_rows += 1
        
        try:
            date_obj = None
            if has_date and row[col_mapping['date']] and row[col_mapping['date']].strip():
                date_obj = _parse_date_flexible(row[col_mapping['date']])
                if not date_obj:
                    result.skipped_rows += 1
                    result.skipped_details.append(f"Row {row_num}: Invalid date format '{row[col_mapping['date']]}' - will use placeholder date and sort by mileage")
            
            mileage = _parse_mileage_flexible(row[col_mapping['mileage']])
            # If no mileage provided, use 0 as placeholder
            if mileage is None:
                mileage = 0
                result.skipped_details.append(f"Row {row_num}: No mileage provided - using placeholder (0) for sorting by date")
            
            cost = None
            if has_cost and row[col_mapping['cost']]:
                cost = _parse_cost_flexible(row[col_mapping['cost']])
            
            description = row[col_mapping['description']].strip()
            is_duplicate = False
            
            # Use placeholder date if no valid date provided
            final_date = date_obj if date_obj else PLACEHOLDER_DATE
            is_estimated = not date_obj
            
            if date_obj:
                is_duplicate = _check_duplicate_record(
                    session, vehicle_id, date_obj, mileage, description
                )
            else:
                is_duplicate = _check_duplicate_record_no_date(
                    session, vehicle_id, mileage, description
                )
            
            if is_duplicate:
                if handle_duplicates == "skip":
                    result.duplicate_rows += 1
                    date_str = date_obj.strftime('%m/%d/%Y') if date_obj else "No date (placeholder)"
                    result.duplicate_details.append(
                        f"Row {row_num}: Duplicate record - {date_str} at {mileage:,} miles: {description}"
                    )
                    continue
                elif handle_duplicates == "replace":
                    from .models import MaintenanceRecord
                    if date_obj:
                        existing = session.execute(
                            select(MaintenanceRecord).where(
                                MaintenanceRecord.vehicle_id == vehicle_id,
                                MaintenanceRecord.date == date_obj,
                                MaintenanceRecord.mileage == mileage,
                                MaintenanceRecord.description == description
                            )
                        ).scalars().first()
                    else:
                        existing = session.execute(
                            select(MaintenanceRecord).where(
                                MaintenanceRecord.vehicle_id == vehicle_id,
                                MaintenanceRecord.mileage == mileage,
                                MaintenanceRecord.description == description
                            )
                        ).scalars().first()
                    
                    if existing:
                        session.delete(existing)
                        date_str = date_obj.strftime('%m/%d/%Y') if date_obj else "No date (placeholder)"
                        result.skipped_details.append(
                            f"Row {row_num}: Replaced existing record - {date_str} at {mileage:,} miles: {description}"
                        )
            
            from .models import MaintenanceRecord
            
            maintenance_record = MaintenanceRecord(
                vehicle_id=vehicle_id,
                date=final_date,
                mileage=mileage,
                description=description,
                cost=cost,
                date_estimated=is_estimated
            )
            
            session.add(maintenance_record)
            result.imported_rows += 1
            
        except Exception as e:
            result.skipped_rows += 1
            result.skipped_details.append(f"Row {row_num}: Error processing row - {str(e)}")
            continue
    
    session.commit()
    return result
