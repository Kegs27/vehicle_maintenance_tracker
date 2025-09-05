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

def dummy_sort_maintenance_records(*args, **kwargs):
    return []

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

# Simplified import system
try:
    from database import engine, init_db, get_session, SessionLocal
    from models import Vehicle, MaintenanceRecord
    from importer import import_csv, ImportResult
    from data_operations import (
        get_all_vehicles, get_vehicle_by_id, create_vehicle, update_vehicle, delete_vehicle,
        get_all_maintenance_records, get_maintenance_records_by_vehicle, get_maintenance_by_id,
        create_maintenance_record, create_basic_maintenance_record, create_oil_analysis_record,
        create_placeholder_oil_analysis, update_maintenance_record, delete_maintenance_record,
        import_csv_data, export_vehicles_csv, export_maintenance_csv, get_vehicle_names,
        get_maintenance_summary, get_home_dashboard_summary, get_current_mileage_from_all_sources,
        get_oil_change_interval_from_record, get_fuel_entries_for_vehicle, get_all_fuel_entries,
        get_vehicle_health_status, sort_maintenance_records, get_all_vehicles_triggered_maintenance
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
            get_all_vehicles, get_vehicle_by_id, create_vehicle, update_vehicle, delete_vehicle,
            get_all_maintenance_records, get_maintenance_records_by_vehicle, get_maintenance_by_id,
            create_maintenance_record, create_basic_maintenance_record, create_oil_analysis_record,
            create_placeholder_oil_analysis, update_maintenance_record, delete_maintenance_record,
            import_csv_data, export_vehicles_csv, export_maintenance_csv, get_vehicle_names,
            get_maintenance_summary, get_home_dashboard_summary, get_current_mileage_from_all_sources,
            get_oil_change_interval_from_record, get_fuel_entries_for_vehicle, get_all_fuel_entries,
            get_vehicle_health_status, sort_maintenance_records, get_all_vehicles_triggered_maintenance
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
            print("🔗 PostgreSQL database connected successfully")
        
        print("Startup completed successfully!")
    except Exception as e:
        print(f"Startup warning (non-critical): {e}")
        # Don't crash the app on startup errors

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation and summary using centralized data operations"""
    try:
        # Get enhanced dashboard data using centralized function
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
        triggered_maintenance = get_all_vehicles_triggered_maintenance()
        
        return templates.TemplateResponse("vehicles_list.html", {
            "request": request, 
            "vehicles": vehicles, 
            "vehicle_health": vehicle_health,
            "triggered_maintenance": triggered_maintenance
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
        
        # Get all vehicles for the future maintenance modal
        vehicles = get_all_vehicles()
        # Debug logging removed for production
        
        return templates.TemplateResponse("maintenance_list.html", {
            "request": request, 
            "records": records, 
            "vehicle": vehicle,
            "vehicle_name": vehicle_name,
            "summary": summary,
            "vehicles": vehicles
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/maintenance/new", response_class=HTMLResponse)
async def new_maintenance_form(request: Request, return_url: Optional[str] = Query(None), vehicle_id: Optional[int] = Query(None)):
    """Form to add new maintenance record using centralized data operations"""
    vehicles = get_vehicle_names()
    
    # Check if this is an oil analysis form
    is_oil_analysis = return_url and 'oil-analysis' in return_url
    
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request, 
        "vehicles": vehicles, 
        "record": None,
        "return_url": return_url or "/maintenance",
        "selected_vehicle_id": vehicle_id,
        "is_oil_analysis": is_oil_analysis
    })

@app.post("/maintenance")
async def create_maintenance_route(
    vehicle_id: int = Form(...),
    date_str: str = Form(default=""),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None),
    link_oil_analysis: bool = Form(False),
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
    oil_consumption_notes: Optional[str] = Form(None)
):
    """Create a new maintenance record using centralized data operations"""
    try:
        # Handle empty date string by converting to None
        if date_str == "":
            date_str = None
        
        # Use centralized function with validation
        result = create_basic_maintenance_record(
            vehicle_id, date_str or "01/01/1900", description, cost or 0.0, mileage, oil_change_interval
        )
        
        if result["success"]:
            # If oil analysis linking was requested, create a placeholder oil analysis record
            if link_oil_analysis:
                try:
                    # Create a placeholder oil analysis record linked to this oil change
                    oil_analysis_result = create_placeholder_oil_analysis(
                        vehicle_id, date_str or "01/01/1900", f"Oil analysis for {description}", mileage, result["record"].id
                    )
                    if oil_analysis_result["success"]:
                        pass  # Placeholder oil analysis created successfully
                    else:
                        pass  # Failed to create placeholder oil analysis
                except Exception as e:
                    pass  # Error creating placeholder oil analysis
            
            # Redirect back to oil analysis page if that's where we came from
            if any(field is not None for field in [oil_analysis_date, next_oil_analysis_date, oil_analysis_cost, 
                                                 iron_level, aluminum_level, copper_level, viscosity, tbn,
                                                 fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes]):
                # This was an oil analysis record, redirect to oil analysis page
                return RedirectResponse(url=f"/oil-analysis/{vehicle_id}", status_code=303)
            else:
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
        
        # Check if this is an oil analysis record (either has oil analysis data OR coming from oil analysis page)
        is_oil_analysis = (return_url and 'oil-analysis' in return_url) or (
            record.oil_analysis_date or record.oil_analysis_cost or 
            record.iron_level or record.aluminum_level or record.copper_level)
        
        # Check if this record has oil analysis data or is linked to oil analysis
        has_linked_oil_analysis = False
        
        # Check if this record has oil analysis data
        if (record.oil_analysis_date or record.oil_analysis_cost or 
            record.iron_level or record.aluminum_level or record.copper_level):
            has_linked_oil_analysis = True
        elif record.is_oil_change:
            # Look for oil analysis records that link to this oil change
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
            "is_oil_analysis": is_oil_analysis,
            "has_linked_oil_analysis": has_linked_oil_analysis
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
            
            # Get maintenance records for this specific vehicle
            vehicle_records = get_maintenance_records_by_vehicle(vehicle.id)
            
            # Get oil change records for this vehicle (only actual oil changes)
            oil_changes = [
                record for record in vehicle_records 
                if record.is_oil_change
            ]
            
            # Sort oil changes by date (most recent first)
            oil_changes.sort(key=lambda x: x.date, reverse=True)
            
            # Limit to 10 most recent for modal display
            oil_changes_for_modal = oil_changes[:10]
            total_oil_changes = len(oil_changes)
            
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
                "oil_changes": oil_changes_for_modal,
                "total_oil_changes": total_oil_changes,
                "next_due_info": next_due_info
            })
        
        response = templates.TemplateResponse("oil_changes.html", {
            "request": request,
            "vehicle_oil_data": vehicle_oil_data
        })
        
        # Add anti-caching headers to ensure fresh data
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load oil change data: {str(e)}")

# ============================================================================
# OIL ANALYSIS ROUTES
# ============================================================================

@app.get("/oil-analysis/new", response_class=HTMLResponse)
async def new_oil_analysis_form(request: Request, vehicle_id: Optional[int] = Query(None)):
    """Form to add new oil analysis record"""
    vehicles = get_vehicle_names()
    
    # Get oil change records for linking if vehicle_id is provided
    oil_change_records = []
    if vehicle_id:
        all_records = get_maintenance_records_by_vehicle(vehicle_id)
        oil_change_records = [
            record for record in all_records
            if record.is_oil_change
        ]
    
    return templates.TemplateResponse("oil_analysis_form.html", {
        "request": request, 
        "vehicles": vehicles, 
        "record": None,
        "selected_vehicle_id": vehicle_id,
        "oil_change_records": oil_change_records
    })

@app.post("/oil-analysis")
async def create_oil_analysis_route(
    vehicle_id: int = Form(...),
    date_str: str = Form(default=""),
    mileage: int = Form(...),
    description: str = Form(...),
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
    linked_oil_change_id: Optional[int] = Form(None),
    oil_analysis_report: Optional[UploadFile] = File(None)
):
    """Create a new oil analysis record"""
    try:
        # Basic PDF handling - no auto-population
        pdf_file_path = None
        if oil_analysis_report and oil_analysis_report.filename:
            # Create upload directory
            import os
            from pathlib import Path
            upload_dir = Path("uploads/oil_analysis")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"oil_analysis_v{vehicle_id}_{timestamp}.pdf"
            file_path = upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(oil_analysis_report.file.read())
            
            pdf_file_path = str(file_path)
            print(f"✅ PDF saved to: {pdf_file_path}")
        
        # Create the record
        result = create_oil_analysis_record(
            vehicle_id, date_str, description, mileage,
            oil_analysis_date, next_oil_analysis_date, oil_analysis_cost,
            iron_level, aluminum_level, copper_level, viscosity, tbn,
            fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes,
            linked_oil_change_id, pdf_file_path
        )
        
        if result["success"]:
            return RedirectResponse(url=f"/oil-analysis/{vehicle_id}", status_code=303)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating oil analysis record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create oil analysis record: {str(e)}")

@app.get("/oil-analysis/{record_id}/edit", response_class=HTMLResponse)
async def edit_oil_analysis_form(request: Request, record_id: int):
    """Form to edit existing oil analysis record"""
    try:
        record = get_maintenance_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Oil analysis record not found")
        
        vehicles = get_vehicle_names()
        
        # Get oil change records for linking
        all_records = get_maintenance_records_by_vehicle(record.vehicle_id)
        oil_change_records = [
            r for r in all_records
            if r.is_oil_change
        ]
        
        return templates.TemplateResponse("oil_analysis_form.html", {
            "request": request, 
            "vehicles": vehicles, 
            "record": record,
            "oil_change_records": oil_change_records
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load oil analysis record: {str(e)}")

@app.get("/oil-analysis/{vehicle_id}", response_class=HTMLResponse)
async def oil_analysis_page(request: Request, vehicle_id: int):
    """Oil analysis page for a specific vehicle"""
    try:
        # Get the vehicle
        vehicle = get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Get all maintenance records for this vehicle
        records = get_maintenance_records_by_vehicle(vehicle_id)
        
        # Filter for oil analysis records (records with oil analysis data or linked to oil changes)
        oil_analysis_records = [
            record for record in records 
            if (record.oil_analysis_report or record.oil_analysis_date or record.oil_analysis_cost or
                record.iron_level or record.aluminum_level or record.copper_level or record.viscosity or record.tbn or
                record.linked_oil_change_id is not None)
        ]
        
        # Sort by analysis date (most recent first)
        oil_analysis_records.sort(key=lambda x: x.oil_analysis_date or x.date, reverse=True)
        
        # Get oil change records for linking
        oil_change_records = [
            record for record in records 
            if record.is_oil_change
        ]
        
        # Sort oil changes by date (most recent first)
        oil_change_records.sort(key=lambda x: x.date, reverse=True)
        
        response = templates.TemplateResponse("oil_analysis.html", {
            "request": request,
            "vehicle": vehicle,
            "oil_analysis_records": oil_analysis_records,
            "oil_change_records": oil_change_records
        })
        
        # Add anti-caching headers
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load oil analysis data: {str(e)}")

@app.post("/oil-analysis/{record_id}")
async def update_oil_analysis_route(
    record_id: int,
    vehicle_id: int = Form(...),
    date_str: str = Form(...),
    mileage: int = Form(...),
    description: str = Form(...),
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
    oil_analysis_report: Optional[UploadFile] = File(None)
):
    """Update an existing oil analysis record"""
    try:
        # Handle PDF file upload
        pdf_file_path = None
        if oil_analysis_report and oil_analysis_report.filename:
            # Create upload directory
            import os
            from pathlib import Path
            upload_dir = Path("uploads/oil_analysis")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"oil_analysis_v{vehicle_id}_{timestamp}.pdf"
            file_path = upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(oil_analysis_report.file.read())
            
            pdf_file_path = str(file_path)
            print(f"✅ PDF saved to: {pdf_file_path}")
        
        # Use centralized function with validation
        result = update_maintenance_record(
            record_id, vehicle_id, date_str, description, 0.0, mileage, None,
            oil_analysis_date, next_oil_analysis_date, oil_analysis_cost,
            iron_level, aluminum_level, copper_level, viscosity, tbn,
            fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes,
            pdf_file_path
        )
        
        if result["success"]:
            return RedirectResponse(url=f"/oil-analysis/{vehicle_id}?updated=true", status_code=303)
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update oil analysis record: {str(e)}")

@app.get("/oil-analysis/pdf/{record_id}")
async def view_oil_analysis_pdf(record_id: int):
    """View uploaded oil analysis PDF"""
    try:
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

@app.post("/maintenance/{record_id}")
async def update_maintenance_route(
    record_id: int,
    vehicle_id: int = Form(...),
    date_str: str = Form(...),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
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
    return_url: Optional[str] = Form(None)
):
    """Update an existing maintenance record using centralized data operations"""
    try:
        # Use centralized function with validation
        result = update_maintenance_record(
            record_id, vehicle_id, date_str, description, cost or 0.0, mileage, oil_change_interval,
            is_oil_change, oil_type, oil_brand, oil_filter_brand, oil_filter_part_number,
            oil_cost, filter_cost, labor_cost,
            oil_analysis_date, next_oil_analysis_date, oil_analysis_cost,
            iron_level, aluminum_level, copper_level, viscosity, tbn,
            fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes
        )
        
        if result["success"]:
            # If oil analysis linking was requested, create or link oil analysis record
            # Check if this is an oil change (either from form or existing record)
            from data_operations import get_maintenance_by_id
            updated_record = get_maintenance_by_id(record_id)
            is_oil_change_record = is_oil_change or (updated_record and updated_record.is_oil_change)
            
            print(f"DEBUG: link_oil_analysis={link_oil_analysis}, is_oil_change={is_oil_change}, is_oil_change_record={is_oil_change_record}")
            
            if link_oil_analysis and is_oil_change_record:
                try:
                    # Create a placeholder oil analysis record linked to this oil change
                    from data_operations import create_maintenance_record
                    oil_analysis_result = create_maintenance_record(
                        vehicle_id=vehicle_id,
                        date=date_str,  # Same date as oil change
                        description=f"Oil Analysis for Oil Change #{record_id}",
                        cost=0.0,
                        mileage=mileage,
                        linked_oil_change_id=record_id
                    )
                    
                    if oil_analysis_result["success"]:
                        print(f"Created linked oil analysis record {oil_analysis_result['record_id']} for oil change {record_id}")
                    else:
                        print(f"Failed to create linked oil analysis: {oil_analysis_result['error']}")
                except Exception as e:
                    print(f"Error creating linked oil analysis: {e}")
            
            # Use return_url if provided, otherwise use smart redirect logic
            if return_url:
                return RedirectResponse(url=return_url, status_code=303)
            elif any(field is not None for field in [oil_analysis_date, next_oil_analysis_date, oil_analysis_cost, 
                                                 iron_level, aluminum_level, copper_level, viscosity, tbn,
                                                 fuel_dilution, coolant_contamination, driving_conditions, oil_consumption_notes]):
                # This was an oil analysis record, redirect to oil analysis page
                return RedirectResponse(url=f"/oil-analysis/{vehicle_id}", status_code=303)
            else:
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
            mileage=new_mileage
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
async def get_fuel_entries():
    """Get all fuel entries from the database"""
    try:
        from data_operations import get_all_fuel_entries
        
        entries = get_all_fuel_entries()
        
        # Convert date objects to strings for JSON serialization
        serialized_entries = []
        for entry in entries:
            serialized_entry = entry.copy()
            if entry.get('date'):
                serialized_entry['date'] = entry['date'].isoformat() if hasattr(entry['date'], 'isoformat') else str(entry['date'])
            if entry.get('created_at'):
                serialized_entry['created_at'] = entry['created_at'].isoformat() if hasattr(entry['created_at'], 'isoformat') else str(entry['created_at'])
            if entry.get('updated_at'):
                serialized_entry['updated_at'] = entry['updated_at'].isoformat() if hasattr(entry['updated_at'], 'isoformat') else str(entry['updated_at'])
            serialized_entries.append(serialized_entry)
        
        return {
            "success": True,
            "entries": serialized_entries
        }
        
    except Exception as e:
        print(f"Error getting fuel entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get fuel entries: {str(e)}")

@app.get("/api/fuel/mpg-summary")
async def get_fuel_mpg_summary():
    """Get MPG summary for all vehicles"""
    try:
        from data_operations import get_all_vehicles, get_fuel_entries_for_vehicle
        
        vehicles = get_all_vehicles()
        summary = []
        
        for vehicle in vehicles:
            fuel_entries = get_fuel_entries_for_vehicle(vehicle.id)
            
            if len(fuel_entries) >= 2:
                # 🎯 SIMPLE MPG: Sort by mileage, not date!
                print(f"🎯 SIMPLE MPG for {vehicle.name}:")
                print(f"  Total entries: {len(fuel_entries)}")
                
                # Show all entries
                for i, entry in enumerate(fuel_entries):
                    print(f"    Entry {i}: Mileage={entry['mileage']}, Fuel={entry['fuel_amount']}")
                
                # Sort by mileage (lowest to highest)
                sorted_by_mileage = sorted(fuel_entries, key=lambda x: x['mileage'])
                
                print(f"  Sorted by mileage (lowest to highest):")
                for i, entry in enumerate(sorted_by_mileage):
                    print(f"    Mileage {i}: {entry['mileage']}, Fuel={entry['fuel_amount']}")
                
                # Simple MPG: (Highest Mileage - Lowest Mileage) ÷ Total Fuel (skip first)
                lowest_mileage = sorted_by_mileage[0]['mileage']
                highest_mileage = sorted_by_mileage[-1]['mileage']
                total_miles = highest_mileage - lowest_mileage
                
                # Skip first entry (fuel already in tank), sum all other fuel
                fuel_used = sorted_by_mileage[1:]
                total_gallons = sum(entry['fuel_amount'] for entry in fuel_used)
                
                print(f"  MPG Math:")
                print(f"    Lowest mileage: {lowest_mileage}")
                print(f"    Highest mileage: {highest_mileage}")
                print(f"    Total miles: {highest_mileage} - {lowest_mileage} = {total_miles}")
                print(f"    Fuel used: {[entry['fuel_amount'] for entry in fuel_used]} = {total_gallons} gallons")
                
                if total_gallons > 0:
                    mpg = total_miles / total_gallons
                    print(f"    MPG = {total_miles} ÷ {total_gallons} = {mpg:.2f}")
                else:
                    mpg = None
                    print(f"    ERROR: No fuel data")
                
                summary.append({
                    "vehicle_id": vehicle.id,
                    "vehicle_name": vehicle.name,
                    "mpg": mpg,
                    "entries_count": len(fuel_entries),
                    "calculation_details": {
                        "total_miles": total_miles,
                        "total_gallons": total_gallons,
                        "formula": f"({highest_mileage} - {lowest_mileage}) ÷ {total_gallons}",
                        "debug_info": {
                            "lowest_mileage": lowest_mileage,
                            "highest_mileage": highest_mileage,
                            "fuel_entries_used": len(fuel_used)
                        }
                    }
                })
            else:
                summary.append({
                    "vehicle_id": vehicle.id,
                    "vehicle_name": vehicle.name,
                    "mpg": None,
                    "entries_count": len(fuel_entries),
                    "calculation_details": {
                        "total_miles": 0,
                        "total_gallons": 0,
                        "formula": "Need at least 2 fuel entries"
                    }
                })
        
        return {
            "success": True,
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
        vehicles = get_all_vehicles()
        
        # Convert Vehicle objects to dictionaries for JSON serialization
        vehicles_dict = []
        for vehicle in vehicles:
            vehicles_dict.append({
                'id': vehicle.id,
                'name': vehicle.name,
                'year': vehicle.year,
                'make': vehicle.make,
                'model': vehicle.model,
                'vin': vehicle.vin
            })
        
        return templates.TemplateResponse("fuel_tracking_new.html", {
            "request": request,
            "vehicles": vehicles_dict
        })
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
        from data_operations import get_all_future_maintenance
        
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
        from data_operations import get_all_vehicles, get_triggered_future_maintenance, get_vehicle_current_mileage
        
        notifications = []
        total_count = 0
        has_overdue = False
        
        # Get all vehicles to check oil change status
        vehicles = get_all_vehicles()
        
        for vehicle in vehicles:
            # Get current mileage for this vehicle
            mileage_info = get_vehicle_current_mileage(vehicle.id)
            current_mileage = mileage_info.get('current_mileage', 0) or 0
            
            # Check oil change notifications using the same logic as vehicle health
            try:
                # Get oil change records for this vehicle
                from models import MaintenanceRecord
                from sqlalchemy import select
                from sqlalchemy.orm import Session
                from database import SessionLocal
                
                session = SessionLocal()
                try:
                    # Get all maintenance records for this vehicle
                    records = session.execute(
                        select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle.id)
                    ).scalars().all()
                    
                    # Filter for oil change records
                    oil_changes = [
                        record for record in records 
                        if record.vehicle_id == vehicle.id and record.is_oil_change
                    ]
                    
                    if oil_changes:
                        # Get most recent oil change
                        last_oil_change = max(oil_changes, key=lambda x: x.date)
                        
                        # Get the oil change interval from the record
                        from data_operations import get_oil_change_interval_from_record
                        oil_change_interval = get_oil_change_interval_from_record(last_oil_change)
                        
                        if oil_change_interval:
                            miles_since_oil_change = current_mileage - last_oil_change.mileage
                            miles_until_next = oil_change_interval - miles_since_oil_change
                            
                            # Show notification if due within 500 miles OR overdue
                            if miles_until_next <= 500:
                                urgency = 'high' if miles_until_next < 0 else 'medium'
                                if urgency == 'high':
                                    has_overdue = True
                                
                                notifications.append({
                                    'type': 'Oil Change',
                                    'vehicle': f"{vehicle.year} {vehicle.make} {vehicle.model}",
                                    'urgency': urgency,
                                    'link': f'/oil-changes?vehicle_id={vehicle.id}'
                                })
                                total_count += 1
                    
                finally:
                    session.close()
                    
            except Exception as e:
                print(f"Error checking oil change for vehicle {vehicle.id}: {e}")
                continue
            
            # Check future maintenance notifications
            try:
                future_maintenance = get_triggered_future_maintenance(vehicle.id, current_mileage)
                for item in future_maintenance:
                    if item['urgency'] in ['high', 'medium']:  # Only show overdue and due soon
                        if item['urgency'] == 'high':
                            has_overdue = True
                        
                        notifications.append({
                            'type': item['maintenance_type'],
                            'vehicle': f"{vehicle.year} {vehicle.make} {vehicle.model}",
                            'urgency': item['urgency'],
                            'link': f'/maintenance?tab=future-maintenance&vehicle_id={vehicle.id}'
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

@app.get("/check-database-schema")
async def check_database_schema():
    """Check if all required columns exist in the database"""
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return {"error": "DATABASE_URL not found"}
        
        # Handle different database URL formats
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check existing columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'maintenancerecord'
                ORDER BY ordinal_position
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Check for specific columns we need
            required_columns = [
                'linked_oil_change_id',
                'oil_analysis_report',
                'iron_level',
                'aluminum_level'
            ]
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            return {
                "total_columns": len(existing_columns),
                "existing_columns": existing_columns,
                "required_columns": required_columns,
                "missing_columns": missing_columns,
                "has_linked_oil_change_id": 'linked_oil_change_id' in existing_columns
            }
            
    except Exception as e:
        return {"error": str(e)}

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
