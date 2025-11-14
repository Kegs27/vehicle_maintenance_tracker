# Standard library imports
import os
import sys
import csv
import json
import re
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, Any
from io import StringIO
from urllib.parse import urlencode
from itertools import zip_longest

# Third-party imports
from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, ConfigDict, ValidationError

from schemas import MaintenanceCreate, TireMeta

# Define dummy functions at module level to ensure they're always available
def dummy_get_all_vehicles():
    return []
def dummy_get_vehicle_by_id(vehicle_id):
    return None
def dummy_create_vehicle(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_update_vehicle(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_delete_vehicle(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_get_all_maintenance_records():
    return []
def dummy_get_maintenance_records_by_vehicle(*args, **kwargs):
    return []
def dummy_get_maintenance_by_id(*args, **kwargs):
    return None
def dummy_create_maintenance_record(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_update_maintenance_record(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_delete_maintenance_record(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_import_csv_data(*args, **kwargs):
    return {"success": False, "error": "Database not available"}
def dummy_export_vehicles_csv():
    return ""
def dummy_export_maintenance_csv():
    return ""
def dummy_get_vehicle_names():
    return []
def dummy_get_maintenance_summary():
    return {
        "total_vehicles": 0,
        "total_records": 0,
        "total_cost": 0,
        "average_cost_per_record": 0
    }

def dummy_sort_maintenance_records(*args, **kwargs):
    return []

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _errors_dict(validation_error: ValidationError) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    for item in validation_error.errors():
        field = item.get("loc")[-1]
        message = item.get("msg")
        if isinstance(field, str) and isinstance(message, str):
            errors.setdefault(field, message)
    return errors

# Initialize functions with dummy versions by default
get_all_vehicles = dummy_get_all_vehicles
get_vehicle_by_id = dummy_get_vehicle_by_id
create_vehicle = dummy_create_vehicle
update_vehicle = dummy_update_vehicle
delete_vehicle = dummy_delete_vehicle
get_all_maintenance_records = dummy_get_all_maintenance_records
get_maintenance_records_by_vehicle = dummy_get_maintenance_records_by_vehicle
get_maintenance_by_id = dummy_get_maintenance_by_id
create_maintenance_record = dummy_create_maintenance_record
update_maintenance_record = dummy_update_maintenance_record
delete_maintenance_record = dummy_delete_maintenance_record
import_csv_data = dummy_import_csv_data
export_vehicles_csv = dummy_export_vehicles_csv
export_maintenance_csv = dummy_export_maintenance_csv
get_vehicle_names = dummy_get_vehicle_names
get_maintenance_summary = dummy_get_maintenance_summary
sort_maintenance_records = dummy_sort_maintenance_records

# Limits
MAX_TIRE_META_BYTES = 4096

# Simplified import system
try:
    from database import engine, init_db, get_session, SessionLocal
    from models import Vehicle, MaintenanceRecord
    from importer import import_csv, ImportResult
    from data_operations import (
        get_all_vehicles,
        get_vehicle_by_id,
        create_vehicle,
        update_vehicle,
        delete_vehicle,
        get_all_maintenance_records,
        get_maintenance_records_by_vehicle,
        get_maintenance_by_id,
        create_maintenance_record,
        create_basic_maintenance_record,
        create_oil_analysis_record,
        create_placeholder_oil_analysis,
        update_maintenance_record,
        delete_maintenance_record,
        import_csv_data,
        export_vehicles_csv,
        export_maintenance_csv,
        get_vehicle_names,
        get_maintenance_summary,
        get_home_dashboard_summary,
        get_current_mileage_from_all_sources,
        get_oil_change_interval_from_record,
        get_fuel_entries_for_vehicle,
        get_all_fuel_entries,
        get_vehicle_health_status,
        sort_maintenance_records,
        get_all_vehicles_triggered_maintenance,
        get_accounts,
        get_account_by_id,
        get_account_by_name,
        create_account,
        rename_account,
        delete_account,
        set_default_account,
        get_default_account,
        transfer_vehicle_to_account,
        get_account_vehicle_counts,
        get_all_future_maintenance,
    )
    print("✅ Successfully imported all modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Fallback for app package (for local development)
    try:
        from app.database import engine, init_db, get_session, SessionLocal
        from app.models import Vehicle, MaintenanceRecord
        from app.importer import import_csv, ImportResult
        from app.data_operations import (
            get_all_vehicles,
            get_vehicle_by_id,
            create_vehicle,
            update_vehicle,
            delete_vehicle,
            get_all_maintenance_records,
            get_maintenance_records_by_vehicle,
            get_maintenance_by_id,
            create_maintenance_record,
            create_basic_maintenance_record,
            create_oil_analysis_record,
            create_placeholder_oil_analysis,
            update_maintenance_record,
            delete_maintenance_record,
            import_csv_data,
            export_vehicles_csv,
            export_maintenance_csv,
            get_vehicle_names,
            get_maintenance_summary,
            get_home_dashboard_summary,
            get_current_mileage_from_all_sources,
            get_oil_change_interval_from_record,
            get_fuel_entries_for_vehicle,
            get_all_fuel_entries,
            get_vehicle_health_status,
            sort_maintenance_records,
            get_all_vehicles_triggered_maintenance,
            get_accounts,
            get_account_by_id,
            get_account_by_name,
            create_account,
            rename_account,
            delete_account,
            set_default_account,
            get_default_account,
            transfer_vehicle_to_account,
            get_account_vehicle_counts,
            get_all_future_maintenance,
        )
        print("✅ Successfully imported from app package")
    except ImportError as e2:
        print(f"❌ App package import failed: {e2}")
        # Create minimal stubs to prevent crashes
        class DummyEngine: pass
        class DummySession: pass
        engine = DummyEngine()
        init_db = lambda: print("Database init skipped")
        get_session = lambda: None
        Vehicle = None
        MaintenanceRecord = None
        import_csv = lambda *args, **kwargs: None
        ImportResult = None
        print("⚠️ Using dummy objects to prevent crashes")

# Create FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker")

if os.getenv("ENV") == "development":
    from starlette.middleware.base import BaseHTTPMiddleware

    class LogRedirects(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            if response.status_code in (301, 302):
                location = response.headers.get("location")
                print(f"[REDIRECT] {request.method} {request.url.path} -> {location}")
            return response

    app.add_middleware(LogRedirects)

# Templates
templates = Jinja2Templates(directory="./templates")

try:
    from database import ENV, APP_IS_DEV  # type: ignore
except ImportError:
    # Fallback so prod doesn't crash if ENV/APP_IS_DEV aren't exported
    ENV = os.getenv("ENV", "prod").lower()
    APP_IS_DEV = ENV != "prod"

templates.env.globals["APP_ENV"] = ENV
templates.env.globals["APP_IS_DEV"] = APP_IS_DEV

def zip_filter(a, b):
    """Jinja filter to zip two sequences."""
    return zip(a, b)

templates.env.filters["zip"] = zip_filter

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

@app.get("/favicon.svg")
async def favicon_svg():
    return FileResponse("static/favicon.svg")

@app.get("/favicon.ico")
async def favicon_ico():
    return FileResponse("static/favicon.ico")

@app.get("/apple-touch-icon.png")
async def apple_touch_icon():
    return FileResponse("static/apple-touch-icon.png")


def get_account_context(request: Request):
    """
    Resolve the current account selection from the request.

    Priority order:
      1. Explicit query parameter ?accountId=
      2. Cookie `vmt.accountId` (account id) or legacy `selected_account` (name)
      3. Owner default account

    Returns a dict with:
      - scope: "all" or "single"
      - account: Account instance or None
      - account_id: selected account id or None
      - accounts: list of all accounts for the owner
    """
    if hasattr(request.state, "account_context"):
        return request.state.account_context

    selected_account = None
    scope = "all"

    candidate_sources = [
        ("id", request.query_params.get("accountId")),
        ("id", request.cookies.get("vmt.accountId")),
        ("name", request.cookies.get("selected_account")),
    ]

    for source, raw_value in candidate_sources:
        if not raw_value:
            continue

        value = raw_value.strip()
        if value.lower() in ("", "all", "null", "none"):
            scope = "all"
            selected_account = None
            break

        if source == "id":
            account = get_account_by_id(value)
        else:
            account = get_account_by_name(value)

        if account:
            selected_account = account
            scope = "single"
            break

    if selected_account is None:
        default_account = get_default_account()
        if default_account:
            selected_account = default_account
            scope = "single"

    accounts = get_accounts()
    context = {
        "scope": scope,
        "account": selected_account,
        "account_id": selected_account.id if selected_account else None,
        "accounts": accounts,
    }
    request.state.account_context = context
    return context


def serialize_account(account, vehicle_count: int = 0, is_default: bool = False) -> Dict[str, Any]:
    """Convert an Account model to a JSON-serializable dict."""
    return {
        "id": account.id,
        "name": account.name,
        "owner_user_id": account.owner_user_id,
        "is_default": is_default or account.is_default,
        "vehicle_count": vehicle_count,
        "created_at": account.created_at.isoformat() if getattr(account, "created_at", None) else None,
        "updated_at": account.updated_at.isoformat() if getattr(account, "updated_at", None) else None,
    }


def build_accounts_payload() -> Dict[str, Any]:
    """Return accounts data with counts and default information."""
    accounts = get_accounts()
    counts = get_account_vehicle_counts()
    default_account = get_default_account()
    default_id = default_account.id if default_account else None

    serialized = [
        serialize_account(account, counts.get(account.id, 0), is_default=(account.id == default_id))
        for account in accounts
    ]

    return {
        "accounts": serialized,
        "default_account_id": default_id,
    }


class AccountCreateRequest(BaseModel):
    name: str
    set_default: bool = Field(False, alias="setDefault")

    model_config = ConfigDict(populate_by_name=True)


class AccountRenameRequest(BaseModel):
    name: str


class VehicleTransferRequest(BaseModel):
    account_id: str = Field(..., alias="accountId")

    model_config = ConfigDict(populate_by_name=True)


def serialize_vehicle_for_api(vehicle: Vehicle) -> Dict[str, Any]:
    """Serialize a vehicle object into a JSON-friendly dictionary."""
    account = getattr(vehicle, "account", None)
    return {
        "id": vehicle.id,
        "name": vehicle.name,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "vin": vehicle.vin,
        "account_id": vehicle.account_id,
        "account_name": account.name if account else None,
        "created_at": vehicle.created_at.isoformat() if getattr(vehicle, "created_at", None) else None,
        "updated_at": vehicle.updated_at.isoformat() if getattr(vehicle, "updated_at", None) else None,
    }


def serialize_maintenance_record(record: MaintenanceRecord) -> Dict[str, Any]:
    """Serialize a maintenance record including its vehicle information."""
    vehicle = getattr(record, "vehicle", None)
    account = getattr(vehicle, "account", None) if vehicle else None
    return {
        "id": record.id,
        "vehicle_id": record.vehicle_id,
        "vehicle_name": vehicle.name if vehicle else None,
        "account_id": vehicle.account_id if vehicle else None,
        "account_name": account.name if account else None,
        "date": record.date.isoformat() if record.date else None,
        "mileage": record.mileage,
        "description": record.description,
        "cost": record.cost,
        "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
        "updated_at": record.updated_at.isoformat() if getattr(record, "updated_at", None) else None,
        "is_oil_change": getattr(record, "is_oil_change", False),
    }


def serialize_fuel_entry_for_api(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize fuel entry dictionaries returned from data operations."""
    serialized = entry.copy()
    for key in ("date", "created_at", "updated_at"):
        value = serialized.get(key)
        if value is not None and hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
        elif value is not None:
            serialized[key] = str(value)
    return serialized


def resolve_account_filter(account_id: Optional[str], account_name: Optional[str]) -> Optional[str]:
    """Resolve account id or name query parameters to a canonical account id."""
    normalized_id = account_id.strip() if account_id else None
    if normalized_id and normalized_id.lower() not in ("", "all", "null"):
        account = get_account_by_id(normalized_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return account.id

    normalized_name = account_name.strip() if account_name else None
    if normalized_name and normalized_name.lower() not in ("", "all", "null"):
        account = get_account_by_name(normalized_name)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found.")
        return account.id

    return None

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        print("Starting Vehicle Maintenance Tracker...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Templates directory exists: {os.path.exists('templates')}")
        print(f"Static directory exists: {os.path.exists('static')}")
        print(f"App directory exists: {os.path.exists('app')}")
        print(f"App directory contents: {os.listdir('.') if os.path.exists('.') else 'No current dir'}")
        
        init_db()
        
        # Run PostgreSQL migration if needed
        database_url = os.getenv("DATABASE_URL")
        if database_url and database_url.startswith("postgresql"):
            print("🔗 PostgreSQL database connected successfully")
            
            # Run photo columns migration if needed
            try:
                from migrate_photo_columns import run_migration_with_existing_engine
                from database import engine
                print("Running photo columns migration...")
                success = run_migration_with_existing_engine(engine)
                if success:
                    print("✅ Photo columns migration completed successfully!")
                else:
                    print("⚠️ Photo columns migration failed, but continuing startup...")
            except Exception as e:
                print(f"⚠️ Photo columns migration error: {e}, but continuing startup...")
            
            # Run tire_meta migration if needed
            try:
                from migrate_tire_meta import run
                print("Running tire_meta migration...")
                run()
                print("✅ tire_meta migration completed successfully!")
            except Exception as e:
                print(f"⚠️ tire_meta migration error: {e}, but continuing startup...")
        
        # Ensure account and vehicle linkage migration runs for all environments
        try:
            from migrate_accounts import run_migration_with_existing_engine
            from database import engine
            print("Running account migration...")
            account_success = run_migration_with_existing_engine(engine)
            if account_success:
                print("✅ Account migration completed successfully!")
            else:
                print("⚠️ Account migration failed, continuing startup...")
        except Exception as e:
            print(f"⚠️ Account migration error: {e}, continuing startup...")
        
        print("Startup completed successfully!")
    except Exception as e:
        print(f"Startup warning (non-critical): {e}")
        # Don't crash the app on startup errors

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation and summary using centralized data operations"""
    try:
        # Get enhanced dashboard data using centralized function
        from data_operations import get_home_dashboard_summary
        dashboard_data = get_home_dashboard_summary()
        
        return templates.TemplateResponse("index.html", {"request": request, "dashboard": dashboard_data})
    except Exception as e:
        print(f"Template error: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Create a default dashboard for the error fallback
        default_dashboard = {
            'recent_activity_count': 0,
            'recent_records': [],
            'total_miles_this_year': 0,
            'oil_change_reminders': [],
            'total_vehicles': 0
        }
        
        return templates.TemplateResponse("home_fallback.html", {"request": request, "dashboard": default_dashboard})

@app.head("/")
async def home_head():
    return Response(status_code=200)

@app.get("/migrate-photo-columns")
async def migrate_photo_columns():
    """Run migration to add photo columns to database"""
    try:
        from migrate_photo_columns import run_migration
        success = run_migration()
        if success:
            return {"success": True, "message": "Photo columns migration completed successfully!"}
        else:
            return {"success": False, "message": "Migration failed. Check logs for details."}
    except Exception as e:
        return {"success": False, "message": f"Migration error: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "healthy", "message": "Vehicle Maintenance Tracker is running"}

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the app is working"""
    return {"message": "App is working!", "timestamp": datetime.now().isoformat()}

@app.get("/test-dashboard")
async def test_dashboard():
    """Test endpoint to verify dashboard data is working"""
    try:
        from data_operations import get_home_dashboard_summary
        dashboard_data = get_home_dashboard_summary()
        return {"success": True, "dashboard": dashboard_data}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@app.get("/vehicles", response_class=HTMLResponse)
async def list_vehicles(request: Request):
    """List all vehicles using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None

        vehicles = get_all_vehicles(account_id=account_id)
        vehicle_health = get_vehicle_health_status(account_id=account_id)
        triggered_maintenance = get_all_vehicles_triggered_maintenance(account_id=account_id)

        if account_id:
            allowed_vehicle_ids = {vehicle.id for vehicle in vehicles}
            vehicle_health = [
                status
                for status in vehicle_health
                if status.get("vehicle") and status["vehicle"].id in allowed_vehicle_ids
            ]
            triggered_maintenance = {
                vehicle_id: items
                for vehicle_id, items in triggered_maintenance.items()
                if vehicle_id in allowed_vehicle_ids
            }

        return templates.TemplateResponse("vehicles_list.html", {
            "request": request, 
            "vehicles": vehicles, 
            "vehicle_health": vehicle_health,
            "triggered_maintenance": triggered_maintenance,
            "account_context": account_context,
        })
    except Exception as e:
        print(f"ERROR in list_vehicles: {e}")
        return HTMLResponse(content=f"""
        <h1>Database Error</h1>
        <p>Error: {str(e)}</p>
        <p>This suggests the database connection or models are not properly configured.</p>
        <a href="/">Back to Home</a>
        """)

@app.get("/vehicles/new", response_class=HTMLResponse)
async def new_vehicle_form(request: Request, return_url: Optional[str] = Query(None)):
    """Form to add new vehicle"""
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request, 
        "vehicle": None,
        "return_url": return_url or "/vehicles"
    })

@app.post("/vehicles")
async def create_vehicle_route(
    request: Request,
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None)
):
    """Create a new vehicle using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account = account_context.get("account")
        if account is None:
            account = get_default_account()
        if account is None and account_context.get("accounts"):
            account = account_context["accounts"][0]
        if account is None:
            raise HTTPException(status_code=400, detail="No account available to assign this vehicle.")

        # Auto-generate name if none provided
        if not name or name.strip() == "":
            name = f"{year} {make} {model}"
        
        # Use centralized function with duplicate checking
        result = create_vehicle(name, make, model, year, vin, account_id=account.id)
        
        if result["success"]:
            return RedirectResponse(url=return_url or "/vehicles", status_code=303)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vehicle: {str(e)}")

@app.get("/vehicles/{vehicle_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_form(
    request: Request,
    vehicle_id: int,
    return_url: Optional[str] = Query(None)
):
    """Form to edit existing vehicle"""
    account_context = get_account_context(request)
    account_id = account_context["account_id"] if account_context["scope"] != "all" else None
    vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")
    
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request, 
        "vehicle": vehicle,
        "return_url": return_url or "/vehicles",
        "account_context": account_context,
    })

@app.post("/vehicles/{vehicle_id}")
async def update_vehicle_route(
    request: Request,
    vehicle_id: int,
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None)
):
    """Update an existing vehicle using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")

        # Auto-generate name if none provided
        if not name or name.strip() == "":
            name = f"{year} {make} {model}"
        
        # Use centralized function with duplicate checking
        result = update_vehicle(vehicle_id, name, make, model, year, vin)
        
        if result["success"]:
            return RedirectResponse(url=return_url or "/vehicles", status_code=303)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vehicle: {str(e)}")

@app.delete("/vehicles/{vehicle_id}/delete")
async def delete_vehicle_route(request: Request, vehicle_id: int):
    """Delete a vehicle and all its maintenance records using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")

        result = delete_vehicle(vehicle_id)
        
        if result["success"]:
            return {"success": True, "message": "Vehicle deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vehicle: {str(e)}")

@app.get("/maintenance", response_class=HTMLResponse)
async def list_maintenance(
    request: Request, 
    vehicle_id: Optional[int] = Query(None, alias="vehicleId")
):
    """List maintenance records using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None

        vehicles = get_all_vehicles(account_id=account_id)
        allowed_vehicle_ids = {vehicle.id for vehicle in vehicles}

        vehicle = None
        vehicle_name = None

        if vehicle_id:
            if allowed_vehicle_ids and vehicle_id not in allowed_vehicle_ids:
                raise HTTPException(status_code=404, detail="Vehicle not found in this account.")
            vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")
            vehicle_name = vehicle.name
            records = get_maintenance_records_by_vehicle(vehicle_id, account_id=account_id)
        else:
            records = get_all_maintenance_records(account_id=account_id)

        total_cost = sum(record.cost or 0 for record in records)
        total_records = len(records)
        summary = {
            "total_vehicles": len(vehicles),
            "total_records": total_records,
            "total_cost": total_cost,
            "average_cost_per_record": total_cost / total_records if total_records else 0,
        }

        try:
            future_maintenance = get_all_future_maintenance(account_id=account_id)
            if future_maintenance is None:
                future_maintenance = []
        except Exception as e:
            print(f"Error getting future maintenance: {e}")
            future_maintenance = []

        if allowed_vehicle_ids:
            future_maintenance = [
                record for record in future_maintenance if record.get("vehicle_id") in allowed_vehicle_ids
            ]

        return templates.TemplateResponse("maintenance_list.html", {
            "request": request, 
            "records": records, 
            "vehicle": vehicle,
            "vehicle_name": vehicle_name,
            "summary": summary,
            "vehicles": vehicles,
            "future_maintenance": future_maintenance,
            "account_context": account_context,
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/maintenance/new", response_class=HTMLResponse)
async def new_maintenance_form(
    request: Request, 
    return_url: Optional[str] = Query(None), 
    vehicle_id: Optional[int] = Query(None),
    form_type: Optional[str] = Query(None),
    future_maintenance_id: Optional[int] = Query(None)
):
    """Unified form handler for creating new maintenance, oil changes, and oil analysis"""
    account_context = get_account_context(request)
    account_id = account_context["account_id"] if account_context["scope"] != "all" else None
    incoming_params = dict(request.query_params)
    vehicles_for_account = get_all_vehicles(account_id=account_id)
    vehicle_options = [{"id": v.id, "name": v.name} for v in vehicles_for_account]
    allowed_vehicle_ids = {v.id for v in vehicles_for_account}
    
    # Determine what type of form to show using unified logic
    detected_form_type = determine_form_type(None, return_url, form_type)

    if detected_form_type == "oil_change":
        params = [("open", "add-oil")]

        vehicle_param = (
            vehicle_id
            or incoming_params.get("vehicleId")
            or incoming_params.get("vehicle_id")
        )
        if vehicle_param:
            params.append(("vehicleId", str(vehicle_param)))

        account_param = (
            incoming_params.get("accountId")
            or incoming_params.get("account_id")
            or (account_context["account_id"] if account_context["scope"] != "all" else None)
        )
        if account_param:
            params.append(("accountId", str(account_param)))

        query_string = urlencode(params)
        return RedirectResponse(url=f"/oil-management?{query_string}", status_code=303)
    
    # Pre-populate data from future maintenance if provided
    pre_populated_data = None
    if future_maintenance_id:
        try:
            from data_operations import get_future_maintenance_by_id
            future_maintenance = get_future_maintenance_by_id(future_maintenance_id)
            if future_maintenance and (
                not allowed_vehicle_ids or future_maintenance.vehicle_id in allowed_vehicle_ids
            ):
                pre_populated_data = {
                    "description": f"Oil Change - {future_maintenance.notes or 'Regular maintenance'}",
                    "estimated_cost": future_maintenance.estimated_cost,
                    "target_mileage": future_maintenance.target_mileage,
                    "target_date": future_maintenance.target_date,
                    "notes": future_maintenance.notes,
                    "future_maintenance_id": future_maintenance.id
                }
            else:
                raise HTTPException(status_code=404, detail="Future maintenance not found in this account.")
        except Exception as e:
            print(f"Error loading future maintenance data: {e}")
    
    if vehicle_id and allowed_vehicle_ids and vehicle_id not in allowed_vehicle_ids:
        raise HTTPException(status_code=404, detail="Vehicle not found in this account.")

    return templates.TemplateResponse("maintenance_form.html", {
        "request": request, 
        "vehicles": vehicle_options, 
        "record": None,
        "return_url": return_url or "/maintenance",
        "selected_vehicle_id": vehicle_id,
        "form_type": detected_form_type,
        "pre_populated_data": pre_populated_data,
        "future_maintenance_id": future_maintenance_id,
        # Legacy compatibility for existing template logic
        "is_oil_analysis": detected_form_type == "oil_analysis",
        "is_oil_change": detected_form_type == "oil_change",
        "account_context": account_context,
    })

@app.post("/maintenance")
async def create_maintenance_route(
    request: Request,
    oil_analysis_report: UploadFile = File(None),
    photo: UploadFile = File(None),
):
    """Create a new maintenance record using centralized data operations."""
    try:
        form = await request.form()
        data = dict(form)

        service_type = data.get("service_type")
        rotation_pattern = data.get("rotation_pattern")
        notes_value = data.get("description_notes")
        create_future_raw = data.get("create_future_maintenance")
        target_mileage_raw = data.get("tr_target_mileage")
        target_date_raw = data.get("tr_target_date")
        raw_tire_json = data.get("tire_depths_json")

        payload_extras = {
            "service_type",
            "rotation_pattern",
            "description_notes",
            "create_future_maintenance",
            "tr_target_mileage",
            "tr_target_date",
            "tire_depths_json",
        }
        payload_input = {key: value for key, value in data.items() if key not in payload_extras}

        pattern_labels = {
            "front_to_rear": "Front to Rear",
            "cross": "Cross",
            "five_tire": "5-Tire Rotation",
            "custom": "Custom",
        }
        pattern_label = pattern_labels.get(rotation_pattern, rotation_pattern if rotation_pattern else "")

        pattern_schema_map = {
            "front_to_rear": "front-to-rear",
            "cross": "cross",
            "five_tire": "five-tire",
            "custom": "custom",
        }
        pattern_schema_value = None
        if rotation_pattern:
            pattern_schema_value = pattern_schema_map.get(rotation_pattern, "unknown")

        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        vehicles_for_account = get_all_vehicles(account_id=account_id)
        vehicle_options = [{"id": v.id, "name": v.name} for v in vehicles_for_account]

        def render_with_errors(errors: Dict[str, str]):
            detected_form_type = determine_form_type(
                None,
                data.get("return_url"),
                data.get("form_type"),
            )
            selected_vehicle_id = data.get("vehicle_id")
            try:
                selected_vehicle_id = int(selected_vehicle_id)
            except (TypeError, ValueError):
                pass
            context = {
                "request": request,
                "vehicles": vehicle_options,
                "record": None,
                "return_url": data.get("return_url") or "/maintenance",
                "selected_vehicle_id": selected_vehicle_id,
                "form_type": detected_form_type,
                "pre_populated_data": None,
                "future_maintenance_id": data.get("future_maintenance_id"),
                "is_oil_analysis": detected_form_type == "oil_analysis",
                "is_oil_change": detected_form_type == "oil_change",
                "account_context": account_context,
                "form": data,
                "errors": errors,
            }
            return templates.TemplateResponse("maintenance_form.html", context, status_code=422)

        if raw_tire_json and len(raw_tire_json.encode("utf-8")) > MAX_TIRE_META_BYTES:
            return render_with_errors({"tire_depths_json": "Tire tread data is too large."})

        tire_meta = None
        tire_meta_model: Optional[TireMeta] = None
        if raw_tire_json:
            try:
                parsed_meta = json.loads(raw_tire_json)
                if not isinstance(parsed_meta, dict):
                    raise ValueError("Tire data must be an object.")

                meta_payload: Dict[str, Any] = {
                    key: parsed_meta.get(key)
                    for key in ("fl", "fr", "rl", "rr")
                    if key in parsed_meta
                }
                if pattern_schema_value:
                    meta_payload["pattern"] = pattern_schema_value

                tire_meta_model = TireMeta.model_validate(meta_payload)
                if tire_meta_model.has_measurements():
                    if tire_meta_model.measured_at is None:
                        tire_meta_model = tire_meta_model.model_copy(update={"measured_at": datetime.utcnow()})
                    tire_meta = tire_meta_model.model_dump(exclude_none=True)
                else:
                    tire_meta_model = None
            except ValidationError as exc:
                error_messages = "; ".join(
                    {err.get("msg", "Invalid tire depth values") for err in exc.errors()}
                )
                return render_with_errors({"tire_depths_json": error_messages})
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ invalid tire_depths_json: {exc}")
                return render_with_errors({"tire_depths_json": "Unable to read tire tread data."})

        create_future_flag = isinstance(create_future_raw, str) and create_future_raw.strip().lower() == "true"
        target_mileage = None
        if target_mileage_raw not in (None, "", "None"):
            try:
                target_mileage = int(str(target_mileage_raw).replace(",", ""))
            except (TypeError, ValueError):
                try:
                    target_mileage = int(float(target_mileage_raw))
                except (TypeError, ValueError):
                    print(f"⚠️ invalid tire rotation target mileage: {target_mileage_raw}")
                    target_mileage = None

        target_date = target_date_raw.strip() if isinstance(target_date_raw, str) and target_date_raw.strip() else None
        if isinstance(notes_value, str):
            notes_value = notes_value.strip()
            if not notes_value:
                notes_value = None

        try:
            payload = MaintenanceCreate(**payload_input)
        except ValidationError as exc:
            return render_with_errors(_errors_dict(exc))

        vehicle = get_vehicle_by_id(payload.vehicle_id, account_id=account_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")

        if payload.future_maintenance_id:
            from data_operations import get_future_maintenance_by_id

            future_record = get_future_maintenance_by_id(payload.future_maintenance_id)
            if not future_record or future_record.vehicle_id != payload.vehicle_id:
                raise HTTPException(status_code=404, detail="Future maintenance not found for this vehicle.")

        pdf_file_path = None
        if oil_analysis_report and oil_analysis_report.filename:
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            import uuid

            file_extension = os.path.splitext(oil_analysis_report.filename)[1]
            unique_filename = f"oil_analysis_{uuid.uuid4().hex}{file_extension}"
            pdf_file_path = os.path.join(upload_dir, unique_filename)
            with open(pdf_file_path, "wb") as buffer:
                buffer.write(await oil_analysis_report.read())

        photo_path = None
        if photo and photo.filename:
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            import uuid

            file_extension = os.path.splitext(photo.filename)[1]
            unique_filename = f"photo_{uuid.uuid4().hex}{file_extension}"
            photo_path = os.path.join(upload_dir, unique_filename)
            with open(photo_path, "wb") as buffer:
                buffer.write(await photo.read())

        def dec_to_float(value: Optional[Decimal]) -> Optional[float]:
            return float(value) if value is not None else None

        def clean_fragment(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            cleaned = re.sub(r"[\r\n\t]+", " ", value)
            cleaned = cleaned.strip()
            return cleaned or None

        def summarize_tire_meta(meta: Optional[Dict[str, Any]]) -> Optional[str]:
            if not isinstance(meta, dict):
                return None
            segments = []
            order = (("fl", "FL"), ("fr", "FR"), ("rl", "RL"), ("rr", "RR"))
            for code, label in order:
                section = meta.get(code)
                if not isinstance(section, dict):
                    continue
                depths = [section.get(key) for key in ("i", "m", "o")]
                if not any(depth is not None for depth in depths):
                    continue
                display_values = []
                for depth in depths:
                    if depth is None:
                        display_values.append("—")
                    else:
                        try:
                            display_values.append(str(int(depth)))
                        except (TypeError, ValueError):
                            display_values.append("—")
                segments.append(f"{label} {'/'.join(display_values)}")
            return "; ".join(segments) if segments else None

        notes_value = clean_fragment(notes_value)
        description_for_record = clean_fragment(payload.description)
        if service_type == "tire_rotation":
            description_parts = ["Tire Rotation"]
            if pattern_label:
                description_parts.append(f"Pattern: {pattern_label}")
            if payload.mileage is not None:
                description_parts.append(f"{payload.mileage:,} mi")
            if notes_value:
                description_parts.append(f"Notes: {notes_value}")
            description_for_record = clean_fragment(" · ".join(description_parts))
            tread_summary = summarize_tire_meta(tire_meta)
            if tread_summary:
                description_for_record = f"{description_for_record} | Tread (I/M/O): {tread_summary}"

        payload_description = description_for_record
        if payload_description:
            data["description"] = payload_description

        date_str = payload.date_str or "01/01/1900"
        cost_value = float(payload.cost) if payload.cost is not None else 0.0

        result = create_maintenance_record(
            vehicle_id=payload.vehicle_id,
            date=date_str,
            description=payload_description,
            cost=cost_value,
            mileage=payload.mileage,
            oil_change_interval=payload.oil_change_interval,
            is_oil_change=payload.is_oil_change,
            oil_analysis_date=payload.oil_analysis_date,
            next_oil_analysis_date=payload.next_oil_analysis_date,
            oil_analysis_cost=dec_to_float(payload.oil_analysis_cost),
            iron_level=payload.iron_level,
            aluminum_level=payload.aluminum_level,
            copper_level=payload.copper_level,
            viscosity=payload.viscosity,
            tbn=payload.tbn,
            fuel_dilution=payload.fuel_dilution,
            coolant_contamination=payload.coolant_contamination,
            driving_conditions=payload.driving_conditions,
            oil_consumption_notes=payload.oil_consumption_notes,
            oil_analysis_report=pdf_file_path,
            photo_path=photo_path,
            photo_description=payload.photo_description,
            tire_meta=tire_meta,
        )

        if result["success"] and service_type == "tire_rotation":
            try:
                if create_future_flag and (target_mileage is not None or target_date):
                    from data_operations import create_future_maintenance

                    fm_payload = {
                        "vehicle_id": payload.vehicle_id,
                        "maintenance_type": "Tire Rotation",
                        "target_mileage": target_mileage or 0,
                        "target_date": target_date or "0",
                        "notes": "Auto-created from Tire Rotation form",
                    }
                    fm_result = create_future_maintenance(**fm_payload)
                    if not fm_result.get("success"):
                        print(f"Failed to create future tire rotation reminder: {fm_result.get('error')}")
            except Exception as exc:  # noqa: BLE001
                print("Failed to create future tire rotation reminder", exc)

        is_oil_change_flag = bool(payload.is_oil_change)
        oil_type = payload.oil_type
        oil_brand = payload.oil_brand

        if result["success"] and (is_oil_change_flag or oil_type or oil_brand):
            try:
                from data_operations import update_maintenance_record

                update_result = update_maintenance_record(
                    record_id=result["record"].id,
                    vehicle_id=payload.vehicle_id,
                    date=date_str,
                    description=payload_description,
                    cost=cost_value,
                    mileage=payload.mileage,
                    oil_change_interval=payload.oil_change_interval or 3000,
                    is_oil_change=True,
                    oil_type=payload.oil_type,
                    oil_brand=payload.oil_brand,
                    oil_filter_brand=payload.oil_filter_brand,
                    oil_filter_part_number=payload.oil_filter_part_number,
                    oil_cost=dec_to_float(payload.oil_cost),
                    filter_cost=dec_to_float(payload.filter_cost),
                    labor_cost=dec_to_float(payload.labor_cost),
                )
                if not update_result["success"]:
                    print(f"Warning: Failed to update oil change fields: {update_result.get('error', 'Unknown error')}")
            except Exception as exc:  # noqa: BLE001
                print(f"Warning: Exception updating oil change fields: {exc}")

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        if payload.link_oil_analysis:
            try:
                oil_analysis_result = create_placeholder_oil_analysis(
                    payload.vehicle_id,
                    date_str,
                    f"Oil analysis for {payload_description}" if payload_description else "Oil analysis",
                    payload.mileage,
                    result["record"].id,
                )
                if not oil_analysis_result.get("success"):
                    print(f"Failed to create placeholder oil analysis: {oil_analysis_result.get('error')}")
            except Exception as exc:  # noqa: BLE001
                print(f"Error creating placeholder oil analysis: {exc}")

        if payload.future_maintenance_id:
            try:
                from data_operations import mark_future_maintenance_completed

                mark_future_maintenance_completed(payload.future_maintenance_id)
            except Exception as exc:  # noqa: BLE001
                print(f"Error marking future maintenance as completed: {exc}")

        # Additional oil analysis linking
        if is_oil_change_flag:
            from data_operations import get_maintenance_records_by_vehicle

            vehicle_records = get_maintenance_records_by_vehicle(payload.vehicle_id)
            if payload.link_oil_analysis:
                existing_analysis = [
                    record
                    for record in vehicle_records
                    if record.mileage == payload.mileage
                    and (
                        record.oil_analysis_date
                        or record.oil_analysis_cost
                        or record.iron_level
                        or record.aluminum_level
                        or record.copper_level
                        or (record.description and "analysis" in record.description.lower())
                    )
                ]
                if not existing_analysis:
                    try:
                        from data_operations import create_maintenance_record as create_maintenance_record_fn

                        create_maintenance_record_fn(
                            vehicle_id=payload.vehicle_id,
                            date=date_str,  # Same date as oil change
                            description=(
                                f"Oil Analysis - {payload.mileage:,} miles"
                                if payload.mileage is not None
                                else "Oil Analysis"
                            ),
                            cost=0.0,  # Analysis cost separate from oil change cost
                            mileage=payload.mileage,  # Same mileage as oil change - this creates the link!
                            is_oil_change=False,  # This is an analysis record, not an oil change
                            # Set as analysis record with oil change data for reference
                            oil_analysis_date=date_str,  # Mark as analysis record
                            oil_type=payload.oil_type,  # Copy oil change data
                            oil_brand=payload.oil_brand,
                            oil_filter_brand=payload.oil_filter_brand,
                            oil_filter_part_number=payload.oil_filter_part_number,
                            oil_cost=dec_to_float(payload.oil_cost),
                            filter_cost=dec_to_float(payload.filter_cost),
                            labor_cost=dec_to_float(payload.labor_cost),
                        )
                    except Exception as exc:  # noqa: BLE001
                        print(f"Error creating oil analysis: {exc}")
                else:
                    if payload.mileage is not None:
                        print(f"Oil analysis already exists at {payload.mileage:,} miles")
                    else:
                        print("Oil analysis already exists for this entry")

        analysis_fields = [
            payload.oil_analysis_date,
            payload.next_oil_analysis_date,
            payload.oil_analysis_cost,
            payload.iron_level,
            payload.aluminum_level,
            payload.copper_level,
            payload.viscosity,
            payload.tbn,
            payload.fuel_dilution,
            payload.coolant_contamination,
            payload.driving_conditions,
            payload.oil_consumption_notes,
        ]
        if any(field is not None for field in analysis_fields):
            return RedirectResponse(url="/oil-management", status_code=303)

        return RedirectResponse(url=(payload.return_url or "/maintenance"), status_code=303)

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error creating maintenance record: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to create maintenance record: {str(exc)}")

def determine_form_type(record=None, return_url=None, form_type_param=None):
    """Unified function to determine what type of form to display"""
    
    # 1. Explicit form type parameter takes priority
    if form_type_param:
        return form_type_param
    
    # 2. Check if editing existing record - analyze record data
    if record:
        # Oil analysis detection - comprehensive check
        if (record.oil_analysis_date or record.oil_analysis_cost or 
            record.iron_level or record.aluminum_level or record.copper_level or
            (record.description and 'analysis' in record.description.lower())):
            return "oil_analysis"
        
        # Oil change detection - be more specific about what constitutes an oil change
        # Only consider it an oil change if it has oil-specific data AND doesn't contain non-oil keywords
        is_oil_change_by_data = (record.oil_type or record.oil_brand or record.oil_filter_brand)
        has_non_oil_keywords = (record.description and any(keyword in record.description.lower() 
                              for keyword in ['fuel filter', 'air filter', 'brake', 'tire', 'battery', 'spark plug', 'belt', 'hose', 'gasket', 'sensor', 'pump', 'alternator', 'starter', 'transmission', 'clutch', 'suspension', 'exhaust', 'coolant', 'thermostat', 'radiator', 'water pump']))
        
        if is_oil_change_by_data and not has_non_oil_keywords:
            return "oil_change"
        elif record.is_oil_change and not has_non_oil_keywords:
            return "oil_change"
    
    # 3. Check return URL context
    if return_url:
        if 'oil-management' in return_url:
            # Coming from oil management - could be either, let record data decide
            pass
        elif 'oil-analysis' in return_url:
            return "oil_analysis"
    
    # 4. Default to general maintenance
    return "maintenance"

@app.get("/maintenance/{record_id}/edit", response_class=HTMLResponse)
async def edit_maintenance_form(
    request: Request, 
    record_id: int, 
    return_url: Optional[str] = Query(None),
    form_type: Optional[str] = Query(None)
):
    """Unified form handler for editing maintenance, oil changes, and oil analysis"""
    try:
        record = get_maintenance_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        # Determine what type of form to show using unified logic
        detected_form_type = determine_form_type(record, return_url, form_type)
        
        # Auto-fix incorrectly marked oil change records
        if (record.is_oil_change and 
            record.description and 
            any(keyword in record.description.lower() 
                for keyword in ['fuel filter', 'air filter', 'brake', 'tire', 'battery', 'spark plug', 'belt', 'hose', 'gasket', 'sensor', 'pump', 'alternator', 'starter', 'transmission', 'clutch', 'suspension', 'exhaust', 'coolant', 'thermostat', 'radiator', 'water pump'])):
            # This is incorrectly marked as oil change - auto-fix it
            from data_operations import update_maintenance_record
            update_result = update_maintenance_record(
                record_id=record_id,
                vehicle_id=record.vehicle_id,
                date=record.date.strftime('%m/%d/%Y'),
                description=record.description,
                cost=record.cost or 0.0,  # Handle None cost
                mileage=record.mileage,
                is_oil_change=False,  # Fix the incorrect marking
                oil_change_interval=None,
                oil_type=None,
                oil_brand=None,
                oil_filter_brand=None,
                oil_filter_part_number=None,
                oil_cost=None,
                filter_cost=None,
                labor_cost=None
            )
            if update_result.get("success"):
                # Refresh the record after fixing
                record = get_maintenance_by_id(record_id)
                detected_form_type = "maintenance"  # Now it should be detected as maintenance
        
        vehicles = get_vehicle_names()
        
        # Check if this record has linked oil analysis (for oil change forms)
        has_linked_oil_analysis = False
        if detected_form_type == "oil_change" and record.is_oil_change:
            from data_operations import get_maintenance_records_by_vehicle
            vehicle_records = get_maintenance_records_by_vehicle(record.vehicle_id)
            linked_analysis = [
                r for r in vehicle_records 
                if r.linked_oil_change_id == record.id
            ]
            has_linked_oil_analysis = len(linked_analysis) > 0
        
        return templates.TemplateResponse("maintenance_form.html", {
            "request": request, 
            "vehicles": vehicles, 
            "record": record,
            "return_url": return_url or "/maintenance",
            "form_type": detected_form_type,
            # Legacy compatibility for existing template logic
            "is_oil_analysis": detected_form_type == "oil_analysis",
            "is_oil_change": detected_form_type == "oil_change",
            "has_linked_oil_analysis": has_linked_oil_analysis
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load maintenance record: {str(e)}")

@app.get("/oil-changes", response_class=HTMLResponse)
async def oil_changes_page_redirect(request: Request):
    """Legacy alias for the oil management page (no redirect)."""
    return await oil_management_new(request)

@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    """Email notifications management page"""
    try:
        # Get all vehicles for the dropdown
        vehicles = get_all_vehicles()
        
        # Get all email subscriptions (if the table exists)
        subscriptions = []
        try:
            from app.models import EmailSubscription
            from app.database import get_session
            
            with get_session() as session:
                subscriptions = session.exec(select(EmailSubscription)).all()
        except Exception as e:
            # If EmailSubscription table doesn't exist yet, return empty list
            print(f"EmailSubscription table not available yet: {e}")
            subscriptions = []
        
        return templates.TemplateResponse("notifications.html", {
            "request": request,
            "vehicles": vehicles,
            "subscriptions": subscriptions
        })
    except Exception as e:
        print(f"Error loading notifications page: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load notifications page: {str(e)}")

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Manage Accounts (soft multi-tenancy labels stored client-side)."""
    return templates.TemplateResponse("accounts.html", {"request": request})

@app.get("/oil-analysis/{record_id}")
async def oil_analysis_redirect(record_id: int):
    """Redirect old oil-analysis routes to new maintenance edit system"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/maintenance/{record_id}/edit?return_url=/oil-management", status_code=301)

# ============================================================================
# OLD OIL ANALYSIS ROUTES REMOVED - Now using modal-based system in Oil Management
# All oil analysis functionality is now handled through modals in /oil-management
# ============================================================================

@app.post("/maintenance/{record_id}")
async def update_maintenance_route(
    request: Request,
    record_id: int,
    vehicle_id: int = Form(...),
    date_str: str = Form(default=""),
    mileage: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None),
    link_oil_analysis: bool = Form(False),
    # Oil change fields
    is_oil_change: Optional[bool] = Form(None),
    oil_type: Optional[str] = Form(None),
    oil_brand: Optional[str] = Form(None),
    oil_filter_brand: Optional[str] = Form(None),
    oil_filter_part_number: Optional[str] = Form(None),
    oil_cost: Optional[float] = Form(None),
    filter_cost: Optional[float] = Form(None),
    labor_cost: Optional[float] = Form(None),
    # Oil analysis fields
    oil_analysis_date: Optional[str] = Form(None),
    next_oil_analysis_date: Optional[str] = Form(None),
    oil_analysis_cost: Optional[float] = Form(None),
    iron_level: Optional[float] = Form(None),
    aluminum_level: Optional[float] = Form(None),
    copper_level: Optional[float] = Form(None),
    viscosity: Optional[float] = Form(None),
    tbn: Optional[float] = Form(None),
    fuel_dilution: Optional[float] = Form(None),
    coolant_contamination: Optional[bool] = Form(None),
    driving_conditions: Optional[str] = Form(None),
    oil_consumption_notes: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    # PDF upload for oil analysis
    oil_analysis_report: UploadFile = File(None),
    # Photo documentation
    photo: UploadFile = File(None),
    photo_description: Optional[str] = Form(None)
):
    """Update an existing maintenance record using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found or inaccessible in this account.")

        existing_record = get_maintenance_by_id(record_id)
        if not existing_record or existing_record.vehicle_id != vehicle_id:
            raise HTTPException(status_code=404, detail="Maintenance record not found for this vehicle.")

        # Handle PDF file upload for oil analysis
        pdf_file_path = None
        if oil_analysis_report and oil_analysis_report.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            import uuid
            file_extension = os.path.splitext(oil_analysis_report.filename)[1]
            unique_filename = f"oil_analysis_{uuid.uuid4().hex}{file_extension}"
            pdf_file_path = os.path.join(upload_dir, unique_filename)
            
            # Save the uploaded file
            with open(pdf_file_path, "wb") as buffer:
                content = await oil_analysis_report.read()
                buffer.write(content)
        
        # Handle photo upload for documentation
        photo_path = None
        if photo and photo.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            import uuid
            file_extension = os.path.splitext(photo.filename)[1]
            unique_filename = f"photo_{uuid.uuid4().hex}{file_extension}"
            photo_path = os.path.join(upload_dir, unique_filename)
            
            # Save the uploaded file
            with open(photo_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
        
        # Handle empty date_str by using existing record's date
        if not date_str or date_str.strip() == "":
            if existing_record and existing_record.date:
                date_str = existing_record.date.strftime('%m/%d/%Y')
            else:
                # Fallback to current date if no existing date
                date_str = date.today().strftime('%m/%d/%Y')
        
        # Use centralized function with validation
        result = update_maintenance_record(
            record_id, vehicle_id, date_str, description, cost or 0.0, mileage, oil_change_interval,
            is_oil_change, oil_type, oil_brand, oil_filter_brand, oil_filter_part_number,
            oil_cost, filter_cost, labor_cost,
            oil_analysis_date, next_oil_analysis_date, oil_analysis_cost,
            iron_level, aluminum_level, copper_level, viscosity, tbn,
            fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes,
            oil_analysis_report=pdf_file_path,
            photo_path=photo_path,
            photo_description=photo_description
        )
        
        if result["success"]:
            # If oil analysis linking was requested, create or link oil analysis record
            # Check if this is an oil change (either from form, existing record, or description)
            updated_record = get_maintenance_by_id(record_id)
            
            # Detect oil change from description if not explicitly marked
            description_indicates_oil_change = False
            if updated_record and updated_record.description:
                oil_keywords = ['oil change', 'oil/filter', 'oil & filter', 'oil and filter', 'oil+filter']
                description_indicates_oil_change = any(keyword in updated_record.description.lower() for keyword in oil_keywords)
            
            is_oil_change_record = is_oil_change or (updated_record and updated_record.is_oil_change) or description_indicates_oil_change
            
            # Handle oil analysis linking/unlinking
            if is_oil_change_record:
                vehicle_records = get_maintenance_records_by_vehicle(vehicle_id)
                
                # Simple mileage-based oil analysis creation
                if link_oil_analysis:
                    # Check if oil analysis already exists at this mileage
                    existing_analysis = [
                        r for r in vehicle_records 
                        if r.mileage == mileage and (
                            r.oil_analysis_date or r.oil_analysis_cost or 
                            r.iron_level or r.aluminum_level or r.copper_level or
                            "analysis" in r.description.lower()
                        )
                    ]
                    
                    if not existing_analysis:
                        # Create new oil analysis placeholder at same mileage
                        try:
                            oil_analysis_result = create_maintenance_record(
                                vehicle_id=vehicle_id,
                                date=date_str,  # Same date as oil change
                                description=f"Oil Analysis - {mileage:,} miles",
                                cost=0.0,  # Analysis cost separate from oil change cost
                                mileage=mileage,  # Same mileage as oil change - this creates the link!
                                is_oil_change=False,  # This is an analysis record, not an oil change
                                # Set as analysis record with oil change data for reference
                                oil_analysis_date=date_str,  # Mark as analysis record
                                oil_type=oil_type,  # Copy oil change data
                                oil_brand=oil_brand,
                                oil_filter_brand=oil_filter_brand,
                                oil_filter_part_number=oil_filter_part_number,
                                oil_cost=oil_cost,
                                filter_cost=filter_cost,
                                labor_cost=labor_cost
                            )
                            
                            if oil_analysis_result.get("success"):
                                print(f"Created oil analysis placeholder at {mileage:,} miles")
                            else:
                                print(f"Failed to create oil analysis: {oil_analysis_result.get('error')}")
                        except Exception as e:
                            print(f"Error creating oil analysis: {e}")
                    else:
                        print(f"Oil analysis already exists at {mileage:,} miles")
            
            # Use return_url if provided, otherwise use smart redirect logic
            if return_url:
                return RedirectResponse(url=return_url, status_code=303)
            elif any(field is not None for field in [oil_analysis_date, next_oil_analysis_date, oil_analysis_cost, 
                                                 iron_level, aluminum_level, copper_level, viscosity, tbn,
                                                 fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes]):
                # This was an oil analysis record, redirect to oil analysis page
                return RedirectResponse(url="/oil-management", status_code=303)
            else:
                return RedirectResponse(url=return_url or "/maintenance", status_code=303)
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update maintenance record: {str(e)}")

@app.get("/maintenance/oil-new")
async def maintenance_oil_new_redirect(
    request: Request,
    vehicle_id: Optional[int] = Query(default=None, alias="vehicleId"),
    account_id: Optional[str] = Query(default=None, alias="accountId"),
):
    """
    Redirect to the Oil Management add-oil flow, preserving vehicle/account context.
    """
    params: Dict[str, str] = {"open": "add-oil"}
    incoming = dict(request.query_params)

    vehicle_param = vehicle_id or incoming.get("vehicleId") or incoming.get("vehicle_id")
    if vehicle_param:
        params["vehicleId"] = str(vehicle_param)

    account_param = account_id or incoming.get("accountId") or incoming.get("account_id")
    if account_param:
        params["accountId"] = str(account_param)

    query_string = urlencode(params)
    return RedirectResponse(url=f"/oil-management?{query_string}", status_code=302)

@app.delete("/maintenance/{record_id}")
async def delete_maintenance(request: Request, record_id: int):
    """Delete a maintenance record using centralized data operations"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        record = get_maintenance_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found.")
        vehicle = get_vehicle_by_id(record.vehicle_id, account_id=account_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Maintenance record not accessible in this account.")

        result = delete_maintenance_record(record_id)
        
        if result["success"]:
            return {"success": True, "message": "Maintenance record deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete maintenance record: {str(e)}")

@app.post("/vehicles/{vehicle_id}/update-mileage")
async def update_vehicle_mileage(
    vehicle_id: int,
    new_mileage: int = Form(...),
    date_str: str = Form(...)
):
    """Update vehicle mileage by creating a mileage update record"""
    try:
        # Get current mileage for validation
        from data_operations import get_vehicle_current_mileage, create_maintenance_record
        
        current_mileage_info = get_vehicle_current_mileage(vehicle_id)
        current_mileage = current_mileage_info.get("current_mileage", 0)
        
        # Create the mileage update record
        result = create_maintenance_record(
            vehicle_id=vehicle_id,
            date=date_str,
            description="Mileage Update",
            cost=0.0,
            mileage=new_mileage,
            is_oil_change=False  # This is a mileage update, not an oil change
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Mileage updated successfully",
                "new_mileage": new_mileage,
                "previous_mileage": current_mileage,
                "is_lower": new_mileage < current_mileage,
                "record_id": result.get("record_id")
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mileage: {str(e)}")

@app.delete("/api/fuel/{entry_id}")
async def delete_fuel_entry(entry_id: int):
    """Delete a fuel entry from the database"""
    try:
        from database import SessionLocal
        from models import FuelEntry
        
        session = SessionLocal()
        try:
            # Find and delete the fuel entry
            fuel_entry = session.execute(
                select(FuelEntry).where(FuelEntry.id == entry_id)
            ).scalar_one_or_none()
            
            if not fuel_entry:
                raise HTTPException(status_code=404, detail="Fuel entry not found")
            
            # Store vehicle ID for response
            vehicle_id = fuel_entry.vehicle_id
            
            # Delete the entry
            session.delete(fuel_entry)
            session.commit()
            
            return {
                "success": True, 
                "message": "Fuel entry deleted successfully",
                "vehicle_id": vehicle_id
            }
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete fuel entry: {str(e)}")

@app.get("/api/fuel/entries")
async def get_fuel_entries(
    accountId: Optional[str] = Query(None),
    accountName: Optional[str] = Query(None),
):
    """Get all fuel entries from the database with optional account filtering."""
    try:
        from data_operations import get_all_fuel_entries

        account_id = resolve_account_filter(accountId, accountName)
        entries = get_all_fuel_entries(account_id=account_id)
        serialized_entries = [serialize_fuel_entry_for_api(entry) for entry in entries]

        return {
            "success": True,
            "account_id": account_id,
            "entries": serialized_entries,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting fuel entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get fuel entries: {str(e)}")

@app.get("/api/fuel/mpg-summary")
async def get_fuel_mpg_summary(
    accountId: Optional[str] = Query(None),
    accountName: Optional[str] = Query(None),
):
    """Get MPG summary for all vehicles"""
    try:
        from data_operations import get_all_vehicles, get_fuel_entries_for_vehicle

        account_id = resolve_account_filter(accountId, accountName)
        vehicles = get_all_vehicles(account_id=account_id)
        summary = []
        
        def to_datetime(value):
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, datetime.min.time())
            if isinstance(value, str):
                for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    return None
            return None

        for vehicle in vehicles:
            fuel_entries = get_fuel_entries_for_vehicle(vehicle.id, account_id=account_id)

            total_cost = sum((entry.get("fuel_cost") or 0) for entry in fuel_entries)
            total_gallons_all = sum((entry.get("fuel_amount") or 0) for entry in fuel_entries)
            avg_price_per_gal = (
                float(total_cost) / float(total_gallons_all)
                if total_gallons_all
                else None
            )

            date_values = [dt for dt in (to_datetime(entry.get("date")) for entry in fuel_entries) if dt]
            avg_days_between = None
            if len(date_values) >= 2:
                date_values.sort()
                diffs = []
                for i in range(len(date_values) - 1):
                    diff = (date_values[i + 1] - date_values[i]).days
                    if diff >= 0:
                        diffs.append(diff)
                if diffs:
                    avg_days_between = sum(diffs) / len(diffs)

            # Calculate miles_traveled from fuel entry odometer readings
            # Filter entries with valid odometer readings (non-None, positive values)
            valid_mileage_entries = [
                entry for entry in fuel_entries
                if entry.get('mileage') is not None
                and isinstance(entry.get('mileage'), (int, float))
                and entry.get('mileage') > 0
            ]
            
            miles_traveled = None
            if len(valid_mileage_entries) >= 2:
                # Sort by mileage (lowest to highest)
                sorted_valid_entries = sorted(valid_mileage_entries, key=lambda x: x['mileage'])
                
                # Sum positive deltas between consecutive entries
                total_miles = 0
                for i in range(len(sorted_valid_entries) - 1):
                    current_mileage = sorted_valid_entries[i]['mileage']
                    next_mileage = sorted_valid_entries[i + 1]['mileage']
                    delta = max(0, next_mileage - current_mileage)
                    total_miles += delta
                
                miles_traveled = total_miles if total_miles > 0 else None
            
            if len(fuel_entries) >= 2:
                # 🎯 SIMPLE MPG: Sort by mileage, not date!
                print(f"🎯 SIMPLE MPG for {vehicle.name}:")
                print(f"  Total entries: {len(fuel_entries)}")
                
                # Show all entries
                for i, entry in enumerate(fuel_entries):
                    print(f"    Entry {i}: Mileage={entry['mileage']}, Fuel={entry['fuel_amount']}")
                
                # Sort by mileage (lowest to highest) - filter invalid entries for MPG calculations
                # This ensures backwards compatibility while avoiding errors from None/0 mileage
                valid_for_mpg = [
                    entry for entry in fuel_entries
                    if entry.get('mileage') is not None
                    and isinstance(entry.get('mileage'), (int, float))
                    and entry.get('mileage') > 0
                ]
                sorted_by_mileage = sorted(valid_for_mpg, key=lambda x: x['mileage']) if valid_for_mpg else []
                
                print(f"  Sorted by mileage (lowest to highest):")
                for i, entry in enumerate(sorted_by_mileage):
                    print(f"    Mileage {i}: {entry['mileage']}, Fuel={entry['fuel_amount']}")
                
                # Enhanced MPG calculation with three types
                # Initialize variables
                lifetime_mpg = None
                current_mpg = None
                entries_mpg = None
                gaps_detected = []
                lifetime_miles = 0
                lifetime_gallons = 0
                valid_entries_for_entries_mpg = []
                
                # Only calculate if we have at least 2 valid entries
                if len(sorted_by_mileage) >= 2:
                    print(f"  🚗 {vehicle.name} MPG Calculations:")
                    
                    # 1. LIFETIME MPG (never resets, accumulates from first entry)
                    lifetime_miles = sorted_by_mileage[-1]['mileage'] - sorted_by_mileage[0]['mileage']
                    lifetime_gallons = sum(entry['fuel_amount'] for entry in sorted_by_mileage[1:])
                    lifetime_mpg = lifetime_miles / lifetime_gallons if lifetime_gallons > 0 else None
                    
                    if lifetime_mpg is not None:
                        print(f"    Lifetime MPG: {lifetime_miles:,} miles ÷ {lifetime_gallons} gallons = {lifetime_mpg:.2f} MPG")
                    else:
                        print(f"    Lifetime MPG: Unable to calculate (insufficient data)")
                    
                    # 2. DETECT GAPS (>500 miles between consecutive entries)
                    for i in range(len(sorted_by_mileage) - 1):
                        current_mileage = sorted_by_mileage[i]['mileage']
                        next_mileage = sorted_by_mileage[i + 1]['mileage']
                        gap = next_mileage - current_mileage
                        
                        if gap > 500:
                            gaps_detected.append({
                                'between_entries': f"{current_mileage:,} and {next_mileage:,}",
                                'gap_miles': gap,
                                'suggested_missing_fuel': gap / 25  # Assume 25 MPG average
                            })
                    
                    # 3. CURRENT MPG (last 2 entries only, resets on gaps)
                    # Check if last entry has a gap
                    last_gap = sorted_by_mileage[-1]['mileage'] - sorted_by_mileage[-2]['mileage']
                    if last_gap <= 500:  # No gap detected
                        current_miles = sorted_by_mileage[-1]['mileage'] - sorted_by_mileage[-2]['mileage']
                        current_gallons = sorted_by_mileage[-1]['fuel_amount']
                        current_mpg = current_miles / current_gallons if current_gallons > 0 else None
                        if current_mpg is not None:
                            print(f"    Current MPG: {current_miles:,} miles ÷ {current_gallons} gallons = {current_mpg:.2f} MPG")
                        else:
                            print(f"    Current MPG: Unable to calculate (insufficient data)")
                    else:
                        print(f"    Current MPG: RESET (gap detected: {last_gap:,} miles)")
                    
                    # 4. ENTRIES-BASED MPG (last 5 entries, resets on gaps)
                    entries_count = min(5, len(sorted_by_mileage))
                    
                    if entries_count >= 2:
                        # Check for gaps in the last 5 entries
                        valid_entries_for_entries_mpg = []
                        start_idx = len(sorted_by_mileage) - entries_count
                        for i in range(start_idx, len(sorted_by_mileage)):
                            if i == start_idx or (sorted_by_mileage[i]['mileage'] - sorted_by_mileage[i-1]['mileage']) <= 500:
                                valid_entries_for_entries_mpg.append(sorted_by_mileage[i])
                            else:
                                break  # Stop at first gap
                        
                        if len(valid_entries_for_entries_mpg) >= 2:
                            entries_miles = valid_entries_for_entries_mpg[-1]['mileage'] - valid_entries_for_entries_mpg[0]['mileage']
                            entries_gallons = sum(entry['fuel_amount'] for entry in valid_entries_for_entries_mpg[1:])
                            entries_mpg = entries_miles / entries_gallons if entries_gallons > 0 else None
                            if entries_mpg is not None:
                                print(f"    Entries MPG ({len(valid_entries_for_entries_mpg)} entries): {entries_miles:,} miles ÷ {entries_gallons} gallons = {entries_mpg:.2f} MPG")
                            else:
                                print(f"    Entries MPG: Unable to calculate (insufficient data)")
                        else:
                            print(f"    Entries MPG: RESET (insufficient valid entries after gap removal)")
                    else:
                        print(f"    Entries MPG: Need at least 2 entries")
                else:
                    print(f"  🚗 {vehicle.name} MPG Calculations: Need at least 2 entries with valid mileage")
                
                # Store results
                mpg = lifetime_mpg  # Keep backward compatibility for now
                
                summary.append({
                    "vehicle_id": vehicle.id,
                    "vehicle_name": vehicle.name,
                    "account_id": vehicle.account_id,
                    "mpg": mpg,  # Lifetime MPG for backward compatibility
                    "lifetime_mpg": lifetime_mpg,
                    "current_mpg": current_mpg,
                    "entries_mpg": entries_mpg,
                    "entries_count": len(fuel_entries),
                    "gaps_detected": gaps_detected,
                    "avg_price_per_gal": avg_price_per_gal,
                    "miles_traveled": miles_traveled,
                    "gallons_filled": float(total_gallons_all) if total_gallons_all else 0,
                    "avg_days_between_fills": avg_days_between,
                    "calculation_details": {
                        "lifetime_miles": lifetime_miles,
                        "lifetime_gallons": lifetime_gallons,
                        "gaps_count": len(gaps_detected),
                        "debug_info": {
                            "total_entries": len(sorted_by_mileage),
                            "valid_entries_for_entries_mpg": len(valid_entries_for_entries_mpg)
                        }
                    }
                })
            else:
                summary.append({
                    "vehicle_id": vehicle.id,
                    "vehicle_name": vehicle.name,
                    "account_id": vehicle.account_id,
                    "mpg": None,
                    "entries_count": len(fuel_entries),
                    "avg_price_per_gal": avg_price_per_gal,
                    "miles_traveled": miles_traveled,
                    "gallons_filled": float(total_gallons_all) if total_gallons_all else 0,
                    "avg_days_between_fills": avg_days_between,
                    "calculation_details": {
                        "total_miles": 0,
                        "total_gallons": 0,
                        "formula": "Need at least 2 fuel entries"
                    }
                })
        
        return {
            "success": True,
            "account_id": account_id,
            "summary": summary
        }
        
    except Exception as e:
        print(f"Error getting MPG summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MPG summary: {str(e)}")

@app.get("/import", response_class=HTMLResponse)
async def import_form(request: Request):
    """Form to import CSV data using centralized data operations"""
    vehicles = get_vehicle_names()
    return templates.TemplateResponse("import.html", {"request": request, "vehicles": vehicles})

@app.post("/import")
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    vehicle_id: int = Form(...),
    handle_duplicates: str = Form("skip")
):
    """Import CSV data using centralized data operations"""
    try:
        # Validate vehicle exists using centralized function
        vehicle = get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=400, detail="Selected vehicle not found")
        
        file_content = await file.read()
        # Use centralized import function with vehicle_id
        result = import_csv_data(file_content.decode('utf-8'), vehicle_id)
        return templates.TemplateResponse("import_result.html", {"request": request, "result": result})
    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(content=f"<h1>Import Error</h1><p>{str(e)}</p>")

@app.get("/api/export/vehicles")
async def export_vehicles_csv(vehicle_ids: Optional[str] = Query(None)):
    """Export vehicles to CSV using centralized data operations"""
    try:
        from data_operations import export_vehicles_csv as export_vehicles_func
        
        if vehicle_ids:
            # Export specific vehicles
            vehicle_id_list = [int(id.strip()) for id in vehicle_ids.split(',')]
            csv_content = export_vehicles_func(vehicle_ids=vehicle_id_list)
            filename = f"vehicles_selected_export.csv"
        else:
            # Export all vehicles
            csv_content = export_vehicles_func()
            filename = "vehicles_export.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/maintenance")
async def export_maintenance_csv(vehicle_id: Optional[int] = Query(None)):
    """Export maintenance records to CSV using centralized data operations"""
    try:
        from data_operations import export_maintenance_csv as export_maintenance_func
        
        if vehicle_id:
            # Export single vehicle maintenance
            csv_content = export_maintenance_func(vehicle_id=vehicle_id)
            filename = f"maintenance_vehicle_{vehicle_id}_export.csv"
        else:
            # Export all maintenance
            csv_content = export_maintenance_func()
            filename = "maintenance_export.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/vehicles/pdf")
async def export_vehicles_pdf(vehicle_ids: Optional[str] = Query(None)):
    """Export vehicles to PDF using centralized data operations"""
    try:
        from data_operations import export_vehicles_pdf as export_vehicles_pdf_func
        
        if vehicle_ids:
            vehicle_id_list = [int(id.strip()) for id in vehicle_ids.split(',')]
            pdf_content = export_vehicles_pdf_func(vehicle_ids=vehicle_id_list)
        else:
            pdf_content = export_vehicles_pdf_func()
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=vehicles_export.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.get("/api/vehicles/names")
async def get_vehicle_names_for_export():
    """Get vehicle names and IDs for export selection"""
    try:
        from data_operations import get_vehicle_names
        vehicles = get_vehicle_names()
        return {"success": True, "vehicles": vehicles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vehicle names: {str(e)}")

@app.get("/api/export/maintenance/pdf")
async def export_maintenance_pdf(vehicle_id: Optional[int] = Query(None)):
    """Export maintenance records to PDF using centralized data operations"""
    try:
        from data_operations import export_maintenance_pdf as export_maintenance_pdf_func
        
        pdf_content = export_maintenance_pdf_func(vehicle_id=vehicle_id)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=maintenance_export.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.get("/fuel", response_class=HTMLResponse)
async def fuel_redirect():
    """Redirect old fuel route to new fuel system"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/fuel-new", status_code=301)

@app.get("/fuel-new", response_class=HTMLResponse)
async def fuel_tracking_new(request: Request):
    """New, clean fuel tracking page"""
    try:
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None
        vehicles = get_all_vehicles(account_id=account_id)

        vehicles_dict = [
            {
                "id": vehicle.id,
                "name": vehicle.name,
                "year": vehicle.year,
                "make": vehicle.make,
                "model": vehicle.model,
                "vin": vehicle.vin,
                "account_id": vehicle.account_id,
            }
            for vehicle in vehicles
        ]

        return templates.TemplateResponse(
            "fuel_tracking_new.html",
            {
                "request": request,
                "vehicles": vehicles_dict,
                "account_context": account_context,
            },
        )
    except Exception as e:
        return HTMLResponse(content=f"<h1>Fuel Tracking Error</h1><p>{str(e)}</p>")

@app.get("/migrate-database")
async def migrate_database():
    """Redirect to comprehensive migration endpoint"""
    return RedirectResponse(url="/migrate-database-full", status_code=302)

# Debug endpoint removed for production

@app.get("/migrate-oil-change-fields")
async def migrate_oil_change_fields():
    """Migration endpoint to add enhanced oil change fields to MaintenanceRecord table"""
    try:
        from database import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            # List of all the new columns we need to add
            new_columns = [
                ("is_oil_change", "BOOLEAN DEFAULT FALSE"),
                ("oil_type", "VARCHAR(20)"),
                ("oil_brand", "VARCHAR(50)"),
                ("oil_filter_brand", "VARCHAR(50)"),
                ("oil_filter_part_number", "VARCHAR(50)"),
                ("oil_cost", "DECIMAL(10,2)"),
                ("filter_cost", "DECIMAL(10,2)"),
                ("labor_cost", "DECIMAL(10,2)"),
                ("oil_analysis_report", "TEXT"),
                ("oil_analysis_date", "DATE"),
                ("next_oil_analysis_date", "DATE"),
                ("oil_analysis_cost", "DECIMAL(10,2)"),
                ("iron_level", "DECIMAL(8,2)"),
                ("aluminum_level", "DECIMAL(8,2)"),
                ("copper_level", "DECIMAL(8,2)"),
                ("viscosity", "DECIMAL(8,2)"),
                ("tbn", "DECIMAL(8,2)"),
                ("fuel_dilution", "DECIMAL(5,2)"),
                ("coolant_contamination", "BOOLEAN"),
                ("driving_conditions", "VARCHAR(50)"),
                ("oil_consumption_notes", "TEXT")
            ]
            
            added_columns = []
            existing_columns = []
            
            for column_name, column_type in new_columns:
                # Check if column already exists
                result = session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'maintenancerecord' AND column_name = '{column_name}'
                """))
                
                if not result.fetchone():
                    # Add the column
                    session.execute(text(f"ALTER TABLE maintenancerecord ADD COLUMN {column_name} {column_type}"))
                    added_columns.append(column_name)
                else:
                    existing_columns.append(column_name)
            
            session.commit()
            
            return {
                "success": True, 
                "message": f"Migration completed successfully!",
                "added_columns": added_columns,
                "existing_columns": existing_columns,
                "total_columns_processed": len(new_columns)
            }
                
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        return {"success": False, "error": f"Migration failed: {str(e)}"}

@app.post("/api/fuel/entry")
async def create_fuel_entry(
    vehicle_id: int = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    mileage: int = Form(...),
    fuel_amount: float = Form(...),
    fuel_cost: float = Form(...),
    fuel_type: str = Form(...),
    driving_pattern: str = Form(...),
    notes: Optional[str] = Form(None),
    odometer_photo: Optional[str] = Form(None)
):
    """Create a new fuel entry in the database"""
    try:
        from database import SessionLocal
        from models import FuelEntry
        from datetime import datetime
        from data_operations import parse_date_string
        
        # Parse the date string
        try:
            parsed_date = parse_date_string(date)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # Check for gaps before creating entry
        from data_operations import get_fuel_entries_for_vehicle
        existing_entries = get_fuel_entries_for_vehicle(vehicle_id)
        gaps_detected = []
        
        if existing_entries:
            # Sort by mileage to find the closest previous entry
            sorted_entries = sorted(existing_entries, key=lambda x: x['mileage'])
            last_entry = sorted_entries[-1]
            
            # Check for gap
            gap = mileage - last_entry['mileage']
            if gap > 500:
                gaps_detected.append({
                    'gap_miles': gap,
                    'previous_mileage': last_entry['mileage'],
                    'current_mileage': mileage,
                    'suggested_missing_fuel': gap / 25  # Assume 25 MPG average
                })
                print(f"⚠️ GAP DETECTED: {gap:,} miles between {last_entry['mileage']:,} and {mileage:,}")
        
        # Create the fuel entry
        session = SessionLocal()
        try:
            fuel_entry = FuelEntry(
                vehicle_id=vehicle_id,
                date=parsed_date,
                time=time,
                mileage=mileage,
                fuel_amount=fuel_amount,
                fuel_cost=fuel_cost,
                fuel_type=fuel_type,
                driving_pattern=driving_pattern,
                notes=notes,
                odometer_photo=odometer_photo,
                created_at=datetime.now().date(),
                updated_at=datetime.now().date()
            )
            
            session.add(fuel_entry)
            session.commit()
            session.refresh(fuel_entry)
            
            print(f"Fuel entry created: Vehicle {vehicle_id}, Mileage {mileage:,}, Date {parsed_date}")
            
            result = {
                "success": True,
                "message": "Fuel entry created successfully",
                "entry_id": fuel_entry.id,
                "mileage": mileage,
                "date": str(parsed_date)
            }
            
            # Add gap detection info to result
            if gaps_detected:
                result["gaps_detected"] = gaps_detected
                result["gap_warning"] = f"Gap detected: {gap:,} miles between {last_entry['mileage']:,} and {mileage:,}"
                result["requires_user_choice"] = True
            
            return result
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"Error creating fuel entry: {e}")
        return {
            "success": False,
            "error": f"Failed to create fuel entry: {str(e)}"
        }

@app.put("/api/fuel/{entry_id}")
async def update_fuel_entry(
    entry_id: int,
    vehicle_id: int = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    mileage: int = Form(...),
    fuel_amount: float = Form(...),
    fuel_cost: float = Form(...),
    fuel_type: str = Form(...),
    driving_pattern: str = Form(...),
    notes: Optional[str] = Form(None),
    odometer_photo: Optional[str] = Form(None)
):
    """Update an existing fuel entry in the database"""
    try:
        from database import SessionLocal
        from models import FuelEntry
        from datetime import datetime
        from data_operations import parse_date_string
        
        # Parse the date string
        try:
            parsed_date = parse_date_string(date)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # Update the fuel entry
        session = SessionLocal()
        try:
            fuel_entry = session.execute(
                select(FuelEntry).where(FuelEntry.id == entry_id)
            ).scalar_one_or_none()
            
            if not fuel_entry:
                return {
                    "success": False,
                    "error": "Fuel entry not found"
                }
            
            # Update the fields
            fuel_entry.vehicle_id = vehicle_id
            fuel_entry.date = parsed_date
            fuel_entry.time = time
            fuel_entry.mileage = mileage
            fuel_entry.fuel_amount = fuel_amount
            fuel_entry.fuel_cost = fuel_cost
            fuel_entry.fuel_type = fuel_type
            fuel_entry.driving_pattern = driving_pattern
            fuel_entry.notes = notes
            fuel_entry.odometer_photo = odometer_photo
            fuel_entry.updated_at = datetime.now().date()
            
            session.commit()
            session.refresh(fuel_entry)
            
            print(f"Fuel entry updated: ID {entry_id}, Vehicle {vehicle_id}, Mileage {mileage:,}, Date {parsed_date}")
            
            return {
                "success": True,
                "message": "Fuel entry updated successfully",
                "entry_id": fuel_entry.id,
                "mileage": mileage,
                "date": str(parsed_date)
            }
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"Error updating fuel entry: {e}")
        return {
            "success": False,
            "error": f"Failed to update fuel entry: {str(e)}"
        }

# ============================================================================
# FUTURE MAINTENANCE API ENDPOINTS
# ============================================================================

@app.post("/api/future-maintenance")
async def create_future_maintenance_api(
    vehicle_id: int = Form(...),
    maintenance_type: str = Form(...),
    target_date: str = Form(),
    target_mileage: int = Form(),
    mileage_reminder: int = Form(100),
    date_reminder: int = Form(30),
    estimated_cost: float = Form(),
    parts_link: str = Form(),
    notes: str = Form(),
    is_recurring: bool = Form(False),
    recurrence_interval_miles: int = Form(),
    recurrence_interval_months: int = Form()
):
    """Create a new future maintenance reminder"""
    try:
        from data_operations import create_future_maintenance
        
        result = create_future_maintenance(
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            target_date=target_date,
            target_mileage=target_mileage,
            mileage_reminder=mileage_reminder,
            date_reminder=date_reminder,
            estimated_cost=estimated_cost,
            parts_link=parts_link,
            notes=notes,
            is_recurring=is_recurring,
            recurrence_interval_miles=recurrence_interval_miles,
            recurrence_interval_months=recurrence_interval_months
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create future maintenance: {str(e)}"
        }

@app.put("/api/future-maintenance/{future_maintenance_id}")
async def update_future_maintenance_api(
    future_maintenance_id: int,
    vehicle_id: int = Form(...),
    maintenance_type: str = Form(...),
    target_date: str = Form(),
    target_mileage: int = Form(),
    mileage_reminder: int = Form(100),
    date_reminder: int = Form(30),
    estimated_cost: float = Form(),
    parts_link: str = Form(),
    notes: str = Form(),
    is_recurring: bool = Form(False),
    recurrence_interval_miles: int = Form(),
    recurrence_interval_months: int = Form()
):
    """Update an existing future maintenance reminder"""
    try:
        from data_operations import update_future_maintenance
        
        result = update_future_maintenance(
            future_maintenance_id=future_maintenance_id,
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            target_date=target_date,
            target_mileage=target_mileage,
            mileage_reminder=mileage_reminder,
            date_reminder=date_reminder,
            estimated_cost=estimated_cost,
            parts_link=parts_link,
            notes=notes,
            is_recurring=is_recurring,
            recurrence_interval_miles=recurrence_interval_miles,
            recurrence_interval_months=recurrence_interval_months
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update future maintenance: {str(e)}"
        }

@app.get("/api/future-maintenance/vehicle/{vehicle_id}")
async def get_future_maintenance_by_vehicle_api(vehicle_id: int):
    """Get future maintenance reminders for a specific vehicle"""
    try:
        from data_operations import get_future_maintenance_by_vehicle
        
        future_maintenance = get_future_maintenance_by_vehicle(vehicle_id)
        return {
            "success": True,
            "future_maintenance": future_maintenance
        }
        
    except Exception as e:
        print(f"Error in get_future_maintenance_by_vehicle_api: {e}")
        return {
            "success": False,
            "error": f"Failed to get future maintenance for vehicle: {str(e)}"
        }

@app.get("/api/future-maintenance/single/{future_maintenance_id}")
async def get_future_maintenance_by_id_api(future_maintenance_id: int):
    """Get a specific future maintenance reminder by ID"""
    try:
        from data_operations import get_future_maintenance_by_id
        
        future_maintenance = get_future_maintenance_by_id(future_maintenance_id)
        if future_maintenance:
            return {
                "success": True,
                "future_maintenance": future_maintenance
            }
        else:
            return {
                "success": False,
                "error": "Future maintenance reminder not found"
            }
        
    except Exception as e:
        print(f"Error in get_future_maintenance_by_id_api: {e}")
        return {
            "success": False,
            "error": f"Failed to get future maintenance: {str(e)}"
        }

@app.get("/api/future-maintenance")
async def get_future_maintenance_api():
    """Get all future maintenance reminders"""
    try:
        future_maintenance = get_all_future_maintenance()
        return {
            "success": True,
            "future_maintenance": future_maintenance
        }
        
    except Exception as e:
        print(f"Error in get_future_maintenance_api: {e}")
        return {
            "success": False,
            "error": f"Failed to get future maintenance: {str(e)}"
        }


@app.get("/api/accounts")
async def get_accounts_api():
    """Return all accounts with vehicle counts and default information."""
    payload = build_accounts_payload()
    return {"success": True, **payload}


@app.post("/api/accounts")
async def create_account_api(payload: AccountCreateRequest):
    """Create a new account for the current owner."""
    result = create_account(payload.name, set_default=payload.set_default)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create account."))

    account_name = result["account"].name
    payload_data = build_accounts_payload()
    return {
        "success": True,
        "message": f"Account '{account_name}' created.",
        **payload_data,
    }


@app.patch("/api/accounts/{account_id}")
async def rename_account_api(account_id: str, payload: AccountRenameRequest):
    """Rename an existing account."""
    account = get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    result = rename_account(account_id, payload.name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to rename account."))

    payload_data = build_accounts_payload()
    return {
        "success": True,
        "message": "Account renamed successfully.",
        **payload_data,
    }


@app.delete("/api/accounts/{account_id}")
async def delete_account_api(account_id: str):
    """Delete an account if it has no vehicles."""
    account = get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    result = delete_account(account_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete account."))

    payload_data = build_accounts_payload()
    return {
        "success": True,
        "message": f"Account '{account.name}' deleted.",
        **payload_data,
    }


@app.post("/api/accounts/{account_id}/default")
async def set_default_account_api(account_id: str):
    """Mark an account as the default selection."""
    account = get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    result = set_default_account(account_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to set account as default."))

    payload_data = build_accounts_payload()
    return {
        "success": True,
        "message": f"'{account.name}' set as default account.",
        **payload_data,
    }


@app.post("/api/vehicles/{vehicle_id}/transfer")
async def transfer_vehicle_api(request: Request, vehicle_id: int, payload: VehicleTransferRequest):
    """Move a vehicle to another account."""
    account_context = get_account_context(request)
    account_id = account_context["account_id"] if account_context["scope"] != "all" else None

    vehicle = get_vehicle_by_id(vehicle_id, account_id=account_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    target_account = get_account_by_id(payload.account_id)
    if not target_account:
        raise HTTPException(status_code=404, detail="Target account not found.")

    result = transfer_vehicle_to_account(vehicle_id, payload.account_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to transfer vehicle."))

    vehicle_obj = result.get("vehicle", vehicle)
    message = result.get("message", f"Vehicle moved to {target_account.name}.")
    payload_data = build_accounts_payload()
    return {
        "success": True,
        "message": message,
        "vehicle": {
            "id": vehicle_obj.id,
            "account_id": vehicle_obj.account_id,
        },
        **payload_data,
    }


@app.get("/api/vehicles")
async def list_vehicles_api(
    accountId: Optional[str] = Query(None),
    accountName: Optional[str] = Query(None),
):
    """List vehicles filtered by account when provided."""
    account_id = resolve_account_filter(accountId, accountName)
    vehicles = get_all_vehicles(account_id=account_id)
    return {
        "success": True,
        "account_id": account_id,
        "vehicles": [serialize_vehicle_for_api(vehicle) for vehicle in vehicles],
    }


@app.get("/api/maintenance")
async def list_maintenance_api(
    accountId: Optional[str] = Query(None),
    accountName: Optional[str] = Query(None),
):
    """List maintenance records filtered by account when provided."""
    account_id = resolve_account_filter(accountId, accountName)
    records = get_all_maintenance_records(account_id=account_id)
    return {
        "success": True,
        "account_id": account_id,
        "records": [serialize_maintenance_record(record) for record in records],
    }

@app.delete("/api/future-maintenance/{future_maintenance_id}")
async def delete_future_maintenance_api(future_maintenance_id: int):
    """Delete a future maintenance reminder"""
    try:
        from data_operations import delete_future_maintenance
        
        result = delete_future_maintenance(future_maintenance_id)
        return result
        
    except Exception as e:
        print(f"Error in delete_future_maintenance_api: {e}")
        return {
            "success": False,
            "error": f"Failed to delete future maintenance: {str(e)}"
        }

@app.get("/api/notifications")
async def get_notifications_api():
    """Get all maintenance notifications (oil changes + future maintenance)"""
    try:
        from data_operations import (
            get_all_vehicles,
            get_triggered_future_maintenance,
            get_vehicle_current_mileage,
            get_oil_status_for_all,
        )
        
        notifications = []
        total_count = 0
        has_overdue = False
        
        # Get all vehicles to map vehicle_id to account_id
        vehicles = get_all_vehicles()
        vehicle_to_account = {vehicle.id: vehicle.account_id for vehicle in vehicles}
        
        # Oil change notifications using unified status helper
        oil_statuses = get_oil_status_for_all()
        for status in oil_statuses:
            if status["state"] not in ("soon", "due"):
                continue
            urgency = "high" if status["state"] == "due" else "medium"
            if urgency == "high":
                has_overdue = True
            
            vehicle_id = status['vehicle_id']
            account_id = vehicle_to_account.get(vehicle_id)
            
            # Build link_url: always include accountId, include vehicleId if available
            # If account_id is None, use empty string or omit it (shouldn't happen for vehicles)
            link_url = f"/maintenance?accountId={account_id}" if account_id else "/maintenance"
            if vehicle_id:
                link_url += f"&vehicleId={vehicle_id}" if account_id else f"?vehicleId={vehicle_id}"
            
            notifications.append(
                {
                    "type": "Oil Change",
                    "vehicle": status["vehicle_name"],
                    "urgency": urgency,
                    "link_url": link_url,
                }
            )
            total_count += 1
        
        for vehicle in vehicles:
            mileage_info = get_vehicle_current_mileage(vehicle.id)
            current_mileage = mileage_info.get('current_mileage', 0) or 0
            
            try:
                future_maintenance = get_triggered_future_maintenance(vehicle.id, current_mileage)
                for item in future_maintenance:
                    maintenance_type = (item.get('maintenance_type') or "").lower()
                    if "oil" in maintenance_type:
                        # Oil reminders already handled via unified helper
                        continue
                    if item['urgency'] in ['high', 'medium']:  # Only show overdue and due soon
                        if item['urgency'] == 'high':
                            has_overdue = True
                        
                        # Build link_url: always include accountId, include vehicleId if available
                        # Vehicles always have account_id (required field), but handle gracefully if missing
                        link_url = f"/maintenance?accountId={vehicle.account_id}" if vehicle.account_id else "/maintenance"
                        if vehicle.id:
                            link_url += f"&vehicleId={vehicle.id}" if vehicle.account_id else f"?vehicleId={vehicle.id}"
                        
                        notifications.append({
                            'type': item['maintenance_type'],
                            'vehicle': f"{vehicle.year} {vehicle.make} {vehicle.model}",
                            'urgency': item['urgency'],
                            'link_url': link_url
                        })
                        total_count += 1
            except Exception as e:
                continue
        
        return {
            "success": True,
            "notifications": notifications,
            "total_count": total_count,
            "has_overdue": has_overdue
        }
        
    except Exception as e:
        print(f"Error in get_notifications_api: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to get notifications: {str(e)}",
            "notifications": [],
            "total_count": 0,
            "has_overdue": False
        }

@app.get("/cleanup-oil-analysis", response_class=HTMLResponse)
async def cleanup_oil_analysis():
    """Clean up oil analysis records for testing"""
    try:
        from data_operations import get_all_maintenance_records, delete_maintenance_record
        
        # Get all maintenance records
        all_records = get_all_maintenance_records()
        
        # Find oil analysis records (records with oil analysis data)
        oil_analysis_records = [
            record for record in all_records 
            if (record.oil_analysis_date or record.oil_analysis_cost or 
                record.iron_level or record.aluminum_level or record.copper_level or
                "analysis" in record.description.lower())
        ]
        
        deleted_count = 0
        errors = []
        
        # Delete each oil analysis record
        for record in oil_analysis_records:
            try:
                result = delete_maintenance_record(record.id)
                if result.get("success", False):
                    deleted_count += 1
                else:
                    errors.append(f"Failed to delete record {record.id}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                errors.append(f"Error deleting record {record.id}: {str(e)}")
        
        # Generate HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Oil Analysis Cleanup</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #27ae60; background: #d5f4e6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .error {{ color: #e74c3c; background: #fadbd8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .info {{ color: #3498db; background: #ebf3fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Oil Analysis Cleanup Results</h1>
                
                <div class="info">
                    <h3>Found {len(oil_analysis_records)} oil analysis records</h3>
                </div>
                
                <div class="success">
                    <h3>✅ Successfully deleted: {deleted_count} records</h3>
                </div>
                
                {f'<div class="error"><h3>❌ Errors: {len(errors)}</h3><ul>{"".join(f"<li>{error}</li>" for error in errors)}</ul></div>' if errors else ''}
                
                <div class="info">
                    <h3>Deleted Records:</h3>
                    <ul>
                        {"".join(f"<li>ID {record.id}: {record.description} (Mileage: {record.mileage:,})</li>" for record in oil_analysis_records)}
                    </ul>
                </div>
                
                <p><a href="/oil-analysis/1">← Back to Oil Analysis</a></p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Cleanup Error</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h1>Error during cleanup</h1>
            <p style="color: red;">Error: {str(e)}</p>
            <p><a href="/">← Back to Home</a></p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)

@app.get("/debug-oil-linking/{vehicle_id}")
async def debug_oil_linking(vehicle_id: int):
    """Debug oil change linking issues"""
    try:
        from data_operations import get_maintenance_records_by_vehicle
        
        # Get all maintenance records for this vehicle
        records = get_maintenance_records_by_vehicle(vehicle_id)
        
        # Find oil analysis records
        oil_analysis_records = [
            record for record in records 
            if (record.oil_analysis_report or record.oil_analysis_date or record.oil_analysis_cost or
                record.iron_level or record.aluminum_level or record.copper_level or record.viscosity or record.tbn or
                record.linked_oil_change_id is not None)
        ]
        
        # Find oil change records  
        oil_change_records = [
            record for record in records 
            if record.is_oil_change
        ]
        
        # Create debug info
        debug_info = {
            "vehicle_id": vehicle_id,
            "total_records": len(records),
            "oil_analysis_count": len(oil_analysis_records),
            "oil_change_count": len(oil_change_records),
            "oil_analysis_records": [
                {
                    "id": r.id,
                    "mileage": r.mileage,
                    "description": r.description,
                    "oil_analysis_date": str(r.oil_analysis_date) if r.oil_analysis_date else None,
                    "is_oil_change": r.is_oil_change
                } for r in oil_analysis_records
            ],
            "oil_change_records": [
                {
                    "id": r.id, 
                    "mileage": r.mileage,
                    "description": r.description,
                    "is_oil_change": r.is_oil_change,
                    "date": str(r.date)
                } for r in oil_change_records
            ],
            "mileage_matches": []
        }
        
        # Check for mileage matches
        for analysis in oil_analysis_records:
            matches = [oc for oc in oil_change_records if oc.mileage == analysis.mileage]
            if matches:
                debug_info["mileage_matches"].append({
                    "analysis_id": analysis.id,
                    "analysis_mileage": analysis.mileage,
                    "matching_oil_changes": [{"id": oc.id, "mileage": oc.mileage} for oc in matches]
                })
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/oil-management", response_class=HTMLResponse)
async def oil_management_new(request: Request):
    """New Oil Management page with collapsible cards and smart linking"""
    try:
        from data_operations import (
            get_all_vehicles,
            get_maintenance_records_by_vehicle,
            get_oil_status_for_all,
        )
        
        account_context = get_account_context(request)
        account_id = account_context["account_id"] if account_context["scope"] != "all" else None

        # Get vehicles scoped to the active account (or all)
        vehicles = get_all_vehicles(account_id=account_id)
        oil_status_list = get_oil_status_for_all(account_id=account_id)
        oil_status_map = {status["vehicle_id"]: status for status in oil_status_list}

        def _format_date(value):
            if isinstance(value, date):
                return value.strftime("%m/%d/%Y")
            return value

        def _safe_int(value):
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return value

        vehicles_oil_data = []
        
        for vehicle in vehicles:
            # Get all maintenance records for this vehicle under the same account scope
            records = get_maintenance_records_by_vehicle(vehicle.id, account_id=account_id)
            
            # Filter oil changes (records marked as oil changes)
            oil_changes = [r for r in records if r.is_oil_change]
            oil_changes.sort(key=lambda x: x.date, reverse=True)  # Most recent first
            
            # Get future maintenance records for oil changes
            from database import get_session
            from models import FutureMaintenance
            from sqlmodel import select
            
            session = next(get_session())
            try:
                future_maintenance = session.execute(
                    select(FutureMaintenance)
                    .where(FutureMaintenance.vehicle_id == vehicle.id)
                    .where(FutureMaintenance.is_active == True)
                ).scalars().all()
                future_oil_changes = [fm for fm in future_maintenance if fm.maintenance_type == "Oil Change"]
            finally:
                session.close()
            
            # Filter oil analysis records
            oil_analysis = [
                r for r in records 
                if (r.oil_analysis_date or r.oil_analysis_cost or 
                    r.iron_level or r.aluminum_level or r.copper_level or
                    (r.description and "analysis" in r.description.lower()))
            ]
            oil_analysis.sort(key=lambda x: x.date, reverse=True)  # Most recent first
            
            # Determine analysis status
            analysis_status = 'none'
            if oil_analysis:
                # Check if any analysis is linked to oil changes
                linked_analysis = []
                for analysis in oil_analysis:
                    matching_oil_changes = [oc for oc in oil_changes if oc.mileage == analysis.mileage]
                    if matching_oil_changes:
                        linked_analysis.append(analysis)
                
                if linked_analysis:
                    analysis_status = 'linked'
                else:
                    analysis_status = 'available'
            
            # Get latest oil change for summary
            latest_oil_change = oil_changes[0] if oil_changes else None
            latest_mileage = latest_oil_change.mileage if latest_oil_change else 0
            latest_date = latest_oil_change.date if latest_oil_change else None
            
            # Determine the most recent activity date for this vehicle
            most_recent_activity = None
            if oil_changes:
                most_recent_activity = oil_changes[0].date
            if oil_analysis and (not most_recent_activity or oil_analysis[0].date > most_recent_activity):
                most_recent_activity = oil_analysis[0].date

            status = oil_status_map.get(vehicle.id, {})
            current_miles = _safe_int(status.get("current_miles"))
            last_oil_miles = status.get("last_oil_miles")
            interval_miles = status.get("interval_miles")
            miles_to_due = status.get("miles_to_due")
            next_due_miles = None

            if interval_miles and last_oil_miles is not None:
                try:
                    next_due_miles = int(last_oil_miles) + int(interval_miles)
                except (TypeError, ValueError):
                    next_due_miles = None
            elif current_miles is not None and miles_to_due is not None:
                try:
                    next_due_miles = int(current_miles) + int(miles_to_due)
                except (TypeError, ValueError):
                    next_due_miles = None

            vehicles_oil_data.append({
                'vehicle': vehicle,
                'oil_changes': oil_changes,
                'future_oil_changes': future_oil_changes,
                'oil_analysis': oil_analysis,
                'latest_oil_change': latest_oil_change,
                'latest_mileage': latest_mileage,
                'latest_date': latest_date,
                'analysis_status': analysis_status,
                'most_recent_activity': most_recent_activity,
                'oil_status': {
                    'state': status.get('state', 'ok'),
                    'current_miles': current_miles,
                    'last_change_date': _format_date(status.get('last_oil_date')),
                    'next_due_miles': next_due_miles,
                    'next_due_date': _format_date(status.get('due_date')),
                },
            })
        
        # Find the vehicle with the most recent activity for default expansion
        most_recent_vehicle_id = None
        if vehicles_oil_data:
            # Find vehicle with most recent activity
            most_recent_activity_date = None
            for vehicle_data in vehicles_oil_data:
                if vehicle_data['most_recent_activity']:
                    if not most_recent_activity_date or vehicle_data['most_recent_activity'] > most_recent_activity_date:
                        most_recent_activity_date = vehicle_data['most_recent_activity']
                        most_recent_vehicle_id = vehicle_data['vehicle'].id
        
        # Sort by most recent activity by default (most recent first)
        vehicles_oil_data.sort(key=lambda x: x['most_recent_activity'] or date(1900, 1, 1), reverse=True)
        
        # Convert data to JSON-serializable format
        json_safe_data = []
        for vehicle_data in vehicles_oil_data:
            # Convert vehicle data
            json_vehicle_data = {
                'vehicle': {
                    'id': vehicle_data['vehicle'].id,
                    'name': vehicle_data['vehicle'].name
                },
                'latest_mileage': vehicle_data['latest_mileage'],
                'latest_date_str': vehicle_data['latest_date'].strftime('%Y-%m-%d') if vehicle_data['latest_date'] else None,
                'analysis_status': vehicle_data['analysis_status'],
                'oil_changes': [],
                'oil_analysis': []
            }
            
            # Convert latest oil change
            if vehicle_data['latest_oil_change']:
                latest = vehicle_data['latest_oil_change']
                json_vehicle_data['latest_oil_change'] = {
                    'id': latest.id,
                    'mileage': latest.mileage,
                    'date': latest.date.strftime('%Y-%m-%d'),
                    'oil_type': latest.oil_type,
                    'oil_brand': latest.oil_brand,
                    'cost': float(latest.cost) if latest.cost else None
                }
            else:
                json_vehicle_data['latest_oil_change'] = None
                
            # Convert oil changes
            for oil_change in vehicle_data['oil_changes']:
                json_vehicle_data['oil_changes'].append({
                    'id': oil_change.id,
                    'mileage': oil_change.mileage,
                    'date': oil_change.date.strftime('%Y-%m-%d'),
                    'oil_type': oil_change.oil_type,
                    'oil_brand': oil_change.oil_brand,
                    'cost': float(oil_change.cost) if oil_change.cost else None
                })
                
            # Convert analysis records
            for analysis in vehicle_data['oil_analysis']:
                json_vehicle_data['oil_analysis'].append({
                    'id': analysis.id,
                    'mileage': analysis.mileage,
                    'date': analysis.date.strftime('%Y-%m-%d'),
                    'oil_analysis_report': analysis.oil_analysis_report
                })
                
            json_safe_data.append(json_vehicle_data)
        
        return templates.TemplateResponse("oil_management_new.html", {
            "request": request,
            "vehicles_oil_data": vehicles_oil_data,
            "vehicles_json_data": json_safe_data,
            "most_recent_vehicle_id": most_recent_vehicle_id,
            "account_context": account_context,
        })
        
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>Error Loading Oil Management</h1>
        <p>Error: {str(e)}</p>
        <p><a href="/">← Back to Home</a></p>
        """)

@app.get("/uploads/{filename}")
async def serve_photo(filename: str):
    """Serve uploaded photos"""
    import os
    from fastapi.responses import FileResponse
    
    file_path = f"uploads/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Photo not found")

@app.get("/oil-analysis/pdf/{record_id}")
async def view_oil_analysis_pdf(record_id: int):
    """View uploaded oil analysis PDF"""
    try:
        from data_operations import get_maintenance_by_id
        import os
        from fastapi.responses import FileResponse
        
        record = get_maintenance_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Oil analysis record not found")
        
        if not record.oil_analysis_report:
            raise HTTPException(status_code=404, detail="No PDF report found")
        
        # Check if file exists
        if not os.path.exists(record.oil_analysis_report):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            record.oil_analysis_report,
            media_type="application/pdf",
            filename=f"oil_analysis_{record_id}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve PDF: {str(e)}")

@app.get("/migrate-database-full", response_class=HTMLResponse)
async def migrate_database_endpoint():
    """Run database migration - adds missing columns for oil analysis features"""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError, ProgrammingError
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return HTMLResponse("""
                <html><body style="font-family: Arial; padding: 20px;">
                <h2>❌ Migration Failed</h2>
                <p>DATABASE_URL not found. This endpoint only works on live server.</p>
                </body></html>
            """)
        
        # Handle different database URL formats
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        engine = create_engine(database_url)
        results = []
        
        with engine.connect() as conn:
            # Check existing columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'maintenancerecord'
                ORDER BY ordinal_position
            """))
            
            existing_columns = [row[0] for row in result]
            results.append(f"📋 Found {len(existing_columns)} existing columns")
            
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
                        results.append(f'✅ Added: {col_name}')
                        added_count += 1
                    except (OperationalError, ProgrammingError) as e:
                        results.append(f'⚠️ Error adding {col_name}: {str(e)}')
                else:
                    results.append(f'⏭️ Already exists: {col_name}')
            
            # Commit changes
            conn.commit()
            
            results.append(f"")
            results.append(f"🎉 Migration completed!")
            results.append(f"📊 Added {added_count} new columns")
            results.append(f"✅ Database is now ready for all features!")
            
        # Create HTML response
        html_content = f"""
        <html>
        <head>
            <title>Database Migration Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #28a745; margin-bottom: 20px; }}
                .result {{ margin: 5px 0; padding: 8px; border-radius: 4px; }}
                .success {{ background: #d4edda; color: #155724; }}
                .warning {{ background: #fff3cd; color: #856404; }}
                .info {{ background: #d1ecf1; color: #0c5460; }}
                .final {{ background: #d4edda; color: #155724; font-weight: bold; font-size: 16px; }}
                .button {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🚀 Database Migration Results</h2>
        """
        
        for result in results:
            if result.startswith('✅'):
                html_content += f'<div class="result success">{result}</div>'
            elif result.startswith('⚠️'):
                html_content += f'<div class="result warning">{result}</div>'
            elif result.startswith('🎉') or result.startswith('📊') or result.startswith('✅ Database'):
                html_content += f'<div class="result final">{result}</div>'
            elif result.strip():
                html_content += f'<div class="result info">{result}</div>'
            else:
                html_content += '<br>'
        
        html_content += f"""
                <a href="/" class="button">🏠 Go to Home Page</a>
                <a href="/vehicles" class="button">🚗 View Vehicles</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_content)
        
    except Exception as e:
        error_html = f"""
        <html><body style="font-family: Arial; padding: 20px;">
        <h2>❌ Migration Failed</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">🏠 Go to Home Page</a>
        </body></html>
        """
        return HTMLResponse(error_html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
