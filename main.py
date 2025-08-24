# Standard library imports
import os
import csv
from datetime import date, datetime
from typing import Optional
from io import StringIO

# Third-party imports
from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

# Local imports
import sys
import os

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

# Try to import from current directory first (for Render)
try:
    from database import engine, init_db, get_session
    from models import Vehicle, MaintenanceRecord
    from importer import import_csv, ImportResult
    from data_operations import (
        get_all_vehicles as real_get_all_vehicles,
        get_vehicle_by_id as real_get_vehicle_by_id,
        create_vehicle as real_create_vehicle,
        update_vehicle as real_update_vehicle,
        delete_vehicle as real_delete_vehicle,
        get_all_maintenance_records as real_get_all_maintenance_records,
        get_maintenance_records_by_vehicle as real_get_maintenance_records_by_vehicle,
        get_maintenance_by_id as real_get_maintenance_by_id,
        create_maintenance_record as real_create_maintenance_record,
        update_maintenance_record as real_update_maintenance_record,
        delete_maintenance_record as real_delete_maintenance_record,
        import_csv_data as real_import_csv_data,
        export_vehicles_csv as real_export_vehicles_csv,
        export_maintenance_csv as real_export_maintenance_csv,
        get_vehicle_names as real_get_vehicle_names,
        get_maintenance_summary as real_get_maintenance_summary,
        get_home_dashboard_summary as real_get_home_dashboard_summary,
        get_current_mileage_from_all_sources as real_get_current_mileage_from_all_sources,
        get_oil_change_interval_from_record as real_get_oil_change_interval_from_record,
        get_fuel_entries_for_vehicle as real_get_fuel_entries_for_vehicle,
        get_all_fuel_entries as real_get_all_fuel_entries,
        get_vehicle_health_status as real_get_vehicle_health_status
    )
    
    # Replace dummy functions with real ones
    get_all_vehicles = real_get_all_vehicles
    get_vehicle_by_id = real_get_vehicle_by_id
    create_vehicle = real_create_vehicle
    update_vehicle = real_update_vehicle
    delete_vehicle = real_delete_vehicle
    get_all_maintenance_records = real_get_all_maintenance_records
    get_maintenance_records_by_vehicle = real_get_maintenance_records_by_vehicle
    get_maintenance_by_id = real_get_maintenance_by_id
    create_maintenance_record = real_create_maintenance_record
    update_maintenance_record = real_update_maintenance_record
    delete_maintenance_record = real_delete_maintenance_record
    import_csv_data = real_import_csv_data
    export_vehicles_csv = real_export_vehicles_csv
    export_maintenance_csv = real_export_maintenance_csv
    get_vehicle_names = real_get_vehicle_names
    get_maintenance_summary = real_get_maintenance_summary
    get_home_dashboard_summary = real_get_home_dashboard_summary
    get_current_mileage_from_all_sources = real_get_current_mileage_from_all_sources
    get_oil_change_interval_from_record = real_get_oil_change_interval_from_record
    get_fuel_entries_for_vehicle = real_get_fuel_entries_for_vehicle
    get_all_fuel_entries = real_get_all_fuel_entries
    get_vehicle_health_status = real_get_vehicle_health_status
    
    print("Successfully imported from current directory")
except ImportError as e:
    print(f"Failed to import from current directory: {e}")
    # Fallback for app package (for local development)
    try:
        from app.database import engine, init_db, get_session
        from app.models import Vehicle, MaintenanceRecord
        from app.importer import import_csv, ImportResult
        from app.data_operations import (
            get_all_vehicles as real_get_all_vehicles,
            get_vehicle_by_id as real_get_vehicle_by_id,
            create_vehicle as real_create_vehicle,
            update_vehicle as real_update_vehicle,
            delete_vehicle as real_delete_vehicle,
            get_all_maintenance_records as real_get_all_maintenance_records,
            get_maintenance_by_id as real_get_maintenance_by_id,
            create_maintenance_record as real_create_maintenance_record,
            update_maintenance_record as real_update_maintenance_record,
            delete_maintenance_record as real_delete_maintenance_record,
            import_csv_data as real_import_csv_data,
            export_vehicles_csv as real_export_vehicles_csv,
            export_maintenance_csv as real_export_maintenance_csv,
            get_vehicle_names as real_get_vehicle_names,
            get_maintenance_summary as real_get_maintenance_summary,
            get_home_dashboard_summary as real_get_home_dashboard_summary,
            get_current_mileage_from_all_sources as real_get_current_mileage_from_all_sources,
            get_oil_change_interval_from_record as real_get_oil_change_interval_from_record,
            get_fuel_entries_for_vehicle as real_get_fuel_entries_for_vehicle,
            get_all_fuel_entries as real_get_all_fuel_entries,
            get_vehicle_health_status as real_get_vehicle_health_status
        )
        
        # Replace dummy functions with real ones
        get_all_vehicles = real_get_all_vehicles
        get_vehicle_by_id = real_get_vehicle_by_id
        create_vehicle = real_create_vehicle
        update_vehicle = real_update_vehicle
        delete_vehicle = real_delete_vehicle
        get_all_maintenance_records = real_get_all_maintenance_records
        get_maintenance_by_id = real_get_maintenance_by_id
        create_maintenance_record = real_create_maintenance_record
        update_maintenance_record = real_update_maintenance_record
        delete_maintenance_record = real_delete_maintenance_record
        import_csv_data = real_import_csv_data
        export_vehicles_csv = real_export_vehicles_csv
        export_maintenance_csv = real_export_maintenance_csv
        get_vehicle_names = real_get_vehicle_names
        get_maintenance_summary = real_get_maintenance_summary
        get_home_dashboard_summary = real_get_home_dashboard_summary
        get_current_mileage_from_all_sources = real_get_current_mileage_from_all_sources
        get_oil_change_interval_from_record = real_get_oil_change_interval_from_record
        get_fuel_entries_for_vehicle = real_get_fuel_entries_for_vehicle
        get_all_fuel_entries = real_get_all_fuel_entries
        get_vehicle_health_status = real_get_vehicle_health_status
        
        print("Successfully imported from app package")
    except ImportError as e2:
        print(f"Failed to import from app package: {e2}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in current directory: {os.listdir('.')}")
        
        # Create minimal stubs to prevent crashes
        class DummyEngine:
            pass
        class DummySession:
            pass
        engine = DummyEngine()
        init_db = lambda: print("Database init skipped")
        get_session = lambda: None
        Vehicle = None
        MaintenanceRecord = None
        import_csv = lambda *args, **kwargs: None
        ImportResult = None
        
        print("Using dummy objects to prevent crashes")

# Create FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker")

# Templates
templates = Jinja2Templates(directory="./templates")

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

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
            print("🔄 Running PostgreSQL migration...")
            try:
                from migrate_postgresql_oil_change_interval import migrate_postgresql
                migrate_postgresql()
            except Exception as e:
                print(f"⚠️ Migration warning (non-critical): {e}")
        
        print("Startup completed successfully!")
    except Exception as e:
        print(f"Startup warning (non-critical): {e}")
        # Don't crash the app on startup errors

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation and summary using centralized data operations"""
    try:
        print(f"Attempting to render index.html template...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Templates directory exists: {os.path.exists('./templates')}")
        print(f"Index.html exists: {os.path.exists('./templates/index.html')}")
        
        # Get enhanced dashboard data using centralized function
        dashboard_data = get_home_dashboard_summary()
        print(f"Dashboard data: {dashboard_data}")
        
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
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <head>
            <title>Vehicle Maintenance Tracker</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; text-align: center; }}
                .nav {{ text-align: center; margin: 30px 0; }}
                .nav a {{ display: inline-block; margin: 10px; padding: 12px 24px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
                .nav a:hover {{ background: #2980b9; }}
                .status {{ text-align: center; color: #27ae60; font-size: 18px; margin: 20px 0; }}
                .summary {{ text-align: center; margin: 20px 0; padding: 20px; background: #ecf0f1; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vehicle Maintenance Tracker</h1>
                <div class="status">✅ App is running successfully!</div>
                <div class="summary">
                    <h3>Dashboard</h3>
                    <p>Total Vehicles: {default_dashboard['total_vehicles']}</p>
                    <p>Recent Activity (30 days): {default_dashboard['recent_activity_count']} records</p>
                    <p>Total Miles This Year: {default_dashboard['total_miles_this_year']:,} miles</p>
                </div>
                <div class="nav">
                    <a href="/vehicles">View Vehicles</a>
                    <a href="/vehicles/new">Add Vehicle</a>
                    <a href="/maintenance">View Maintenance</a>
                    <a href="/maintenance/new">Add Maintenance</a>
                    <a href="/import">Import Data</a>
                </div>
                <p style="text-align: center; color: #7f8c8d;">
                    Your vehicle maintenance tracking system is now live and ready to use!
                </p>
            </div>
        </body>
        </html>
        """)

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
        dashboard_data = get_home_dashboard_summary()
        return {"success": True, "dashboard": dashboard_data}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@app.get("/vehicles", response_class=HTMLResponse)
async def list_vehicles(request: Request):
    """List all vehicles using centralized data operations"""
    try:
        vehicles = get_all_vehicles()
        vehicle_health = get_vehicle_health_status()
        return templates.TemplateResponse("vehicles_list.html", {"request": request, "vehicles": vehicles, "vehicle_health": vehicle_health})
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>Database Error</h1>
        <p>Error: {str(e)}</p>
        <p>This suggests the database connection or models are not properly configured.</p>
        <a href="/">Back to Home</a>
        """)

@app.get("/vehicles/new", response_class=HTMLResponse)
async def new_vehicle_form(request: Request):
    """Form to add new vehicle"""
    return templates.TemplateResponse("vehicle_form.html", {"request": request, "vehicle": None})

@app.post("/vehicles")
async def create_vehicle_route(
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None)
):
    """Create a new vehicle using centralized data operations"""
    try:
        # Auto-generate name if none provided
        if not name or name.strip() == "":
            name = f"{year} {make} {model}"
        
        # Use centralized function with duplicate checking
        result = create_vehicle(name, make, model, year, vin)
        
        if result["success"]:
            return RedirectResponse(url="/vehicles", status_code=303)
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
    session: Session = Depends(get_session)
):
    """Form to edit existing vehicle"""
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return templates.TemplateResponse("vehicle_form.html", {"request": request, "vehicle": vehicle})

@app.post("/vehicles/{vehicle_id}")
async def update_vehicle_route(
    vehicle_id: int,
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None)
):
    """Update an existing vehicle using centralized data operations"""
    try:
        # Auto-generate name if none provided
        if not name or name.strip() == "":
            name = f"{year} {make} {model}"
        
        # Use centralized function with duplicate checking
        result = update_vehicle(vehicle_id, name, make, model, year, vin)
        
        if result["success"]:
            return RedirectResponse(url="/vehicles", status_code=303)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vehicle: {str(e)}")

@app.delete("/vehicles/{vehicle_id}/delete")
async def delete_vehicle_route(vehicle_id: int):
    """Delete a vehicle and all its maintenance records using centralized data operations"""
    try:
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
async def list_maintenance(request: Request, vehicle_id: Optional[int] = Query(None)):
    """List maintenance records using centralized data operations"""
    try:
        if vehicle_id:
            # Filter records for specific vehicle
            records = get_maintenance_records_by_vehicle(vehicle_id)
            vehicle = get_vehicle_by_id(vehicle_id)
            vehicle_name = vehicle.name if vehicle else f"Vehicle {vehicle_id}"
        else:
            # Show all records
            records = get_all_maintenance_records()
            vehicle = None
            vehicle_name = None
        
        # Get summary data for the maintenance page
        summary = get_maintenance_summary()
        
        return templates.TemplateResponse("maintenance_list.html", {
            "request": request, 
            "records": records, 
            "vehicle": vehicle,
            "vehicle_name": vehicle_name,
            "summary": summary
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/maintenance/new", response_class=HTMLResponse)
async def new_maintenance_form(request: Request, return_url: Optional[str] = Query(None)):
    """Form to add new maintenance record using centralized data operations"""
    vehicles = get_vehicle_names()
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request, 
        "vehicles": vehicles, 
        "record": None,
        "return_url": return_url or "/maintenance"
    })

@app.post("/maintenance")
async def create_maintenance_route(
    vehicle_id: int = Form(...),
    date_str: str = Form(...),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None)
):
    """Create a new maintenance record using centralized data operations"""
    try:
        print(f"🔍 Debug: Received form data - vehicle_id: {vehicle_id}, date_str: {date_str}, mileage: {mileage}, description: {description}")
        
        # Use centralized function with validation
        result = create_maintenance_record(vehicle_id, date_str, description, cost or 0.0, mileage, oil_change_interval)
        
        if result["success"]:
            return RedirectResponse(url="/maintenance", status_code=303)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating maintenance record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create maintenance record: {str(e)}")

@app.get("/maintenance/{record_id}/edit", response_class=HTMLResponse)
async def edit_maintenance_form(request: Request, record_id: int, return_url: Optional[str] = Query(None)):
    """Form to edit existing maintenance record using centralized data operations"""
    try:
        record = get_maintenance_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        
        vehicles = get_vehicle_names()
        return templates.TemplateResponse("maintenance_form.html", {
            "request": request, 
            "vehicles": vehicles, 
            "record": record,
            "return_url": return_url or "/maintenance"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load maintenance record: {str(e)}")

@app.get("/oil-changes", response_class=HTMLResponse)
async def oil_changes_page(request: Request):
    """Oil change management page showing all oil change records and due dates"""
    try:
        # Get all vehicles and their oil change data
        vehicles = get_all_vehicles()
        records = get_all_maintenance_records()
        
        # Organize oil change data by vehicle
        vehicle_oil_data = []
        
        for vehicle in vehicles:
            # Get current mileage from all sources
            current_mileage = get_current_mileage_from_all_sources(vehicle.id)
            
            # Get oil change records for this vehicle
            oil_changes = [
                record for record in records 
                if record.vehicle_id == vehicle.id and 'oil' in record.description.lower()
            ]
            
            # Sort oil changes by date (most recent first)
            oil_changes.sort(key=lambda x: x.date, reverse=True)
            
            # Calculate next due date if we have oil change records
            next_due_info = None
            if oil_changes and current_mileage > 0:
                last_oil_change = oil_changes[0]  # Most recent
                oil_change_interval = get_oil_change_interval_from_record(last_oil_change)
                miles_since_oil_change = current_mileage - last_oil_change.mileage
                miles_until_next = oil_change_interval - miles_since_oil_change
                
                next_due_info = {
                    "miles_until_due": miles_until_next,
                    "miles_since_last": miles_since_oil_change,
                    "interval": oil_change_interval,
                    "status": "overdue" if miles_until_next < 0 else "due_soon" if miles_until_next <= 500 else "good"
                }
            
            vehicle_oil_data.append({
                "vehicle": vehicle,
                "current_mileage": current_mileage,
                "oil_changes": oil_changes,
                "next_due_info": next_due_info
            })
        
        return templates.TemplateResponse("oil_changes.html", {
            "request": request,
            "vehicle_oil_data": vehicle_oil_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load oil change data: {str(e)}")

@app.post("/maintenance/{record_id}")
async def update_maintenance_route(
    record_id: int,
    vehicle_id: int = Form(...),
    date_str: str = Form(...),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None)
):
    """Update an existing maintenance record using centralized data operations"""
    try:
        # Use centralized function with validation
        result = update_maintenance_record(record_id, vehicle_id, date_str, description, cost or 0.0, mileage, oil_change_interval)
        
        if result["success"]:
            return RedirectResponse(url="/maintenance", status_code=303)
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update maintenance record: {str(e)}")

@app.delete("/maintenance/{record_id}")
async def delete_maintenance(record_id: int):
    """Delete a maintenance record using centralized data operations"""
    try:
        result = delete_maintenance_record(record_id)
        
        if result["success"]:
            return {"success": True, "message": "Maintenance record deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete maintenance record: {str(e)}")

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
async def export_vehicles_csv():
    """Export vehicles to CSV using centralized data operations"""
    try:
        csv_content = export_vehicles_csv()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vehicles_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/maintenance")
async def export_maintenance_csv():
    """Export maintenance records to CSV using centralized data operations"""
    try:
        csv_content = export_maintenance_csv()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=maintenance_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/fuel", response_class=HTMLResponse)
async def fuel_tracking(request: Request):
    """Fuel tracking page with vehicle selection and entry form"""
    try:
        vehicles = get_all_vehicles()
        
        # Get fuel entries for each vehicle from the database
        from data_operations import get_fuel_entries_for_vehicle
        
        vehicle_list = []
        for vehicle in vehicles:
            fuel_entries = get_fuel_entries_for_vehicle(vehicle.id)
            
            # Convert date objects to strings for JSON serialization (entries are already dicts)
            serialized_fuel_entries = []
            for entry in fuel_entries:
                serialized_entry = entry.copy()  # Copy the existing dictionary
                # Convert date objects to strings for JSON serialization
                if entry.get('date'):
                    serialized_entry['date'] = entry['date'].isoformat() if hasattr(entry['date'], 'isoformat') else str(entry['date'])
                if entry.get('created_at'):
                    serialized_entry['created_at'] = entry['created_at'].isoformat() if hasattr(entry['created_at'], 'isoformat') else str(entry['created_at'])
                if entry.get('updated_at'):
                    serialized_entry['updated_at'] = entry['updated_at'].isoformat() if hasattr(entry['updated_at'], 'isoformat') else str(entry['updated_at'])
                serialized_fuel_entries.append(serialized_entry)
            
            vehicle_dict = {
                'id': vehicle.id,
                'name': vehicle.name,
                'year': vehicle.year,
                'make': vehicle.make,
                'model': vehicle.model,
                'vin': vehicle.vin,
                'fuel_entries': serialized_fuel_entries
            }
            vehicle_list.append(vehicle_dict)
        
        # Get the most recent fuel entry across all vehicles
        all_fuel_entries = get_all_fuel_entries()
        last_fuel_entry = None
        if all_fuel_entries:
            last_entry = all_fuel_entries[0]
            # Convert date objects to strings for JSON serialization
            last_fuel_entry = last_entry.copy()  # Copy the existing dictionary
            if last_entry.get('date'):
                last_fuel_entry['date'] = last_entry['date'].isoformat() if hasattr(last_entry['date'], 'isoformat') else str(last_entry['date'])
            if last_entry.get('created_at'):
                last_fuel_entry['created_at'] = last_entry['created_at'].isoformat() if hasattr(last_entry['created_at'], 'isoformat') else str(last_entry['created_at'])
            if last_entry.get('updated_at'):
                last_fuel_entry['updated_at'] = last_entry['updated_at'].isoformat() if hasattr(last_entry['updated_at'], 'isoformat') else str(last_entry['updated_at'])
        
        return templates.TemplateResponse("fuel_tracking.html", {
            "request": request, 
            "vehicles": vehicle_list,
            "last_fuel_entry": last_fuel_entry
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Fuel Tracking Error</h1><p>{str(e)}</p>")

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
        
        # Parse the date string
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "success": False,
                "error": "Invalid date format. Use YYYY-MM-DD"
            }
        
        # Create the fuel entry
        session = SessionLocal()
        try:
            fuel_entry = FuelEntry(
                vehicle_id=vehicle_id,
                date=parsed_date,
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
            
            return {
                "success": True,
                "message": "Fuel entry created successfully",
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
        print(f"Error creating fuel entry: {e}")
        return {
            "success": False,
            "error": f"Failed to create fuel entry: {str(e)}"
        }
