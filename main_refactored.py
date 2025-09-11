"""
Refactored main FastAPI application with improved structure and error handling.
"""
import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Import our refactored data operations
from data_operations_refactored import (
    get_all_vehicles, get_vehicle_by_id_safe, create_vehicle, update_vehicle, delete_vehicle,
    get_all_maintenance_records, get_maintenance_records_by_vehicle, get_maintenance_by_id_safe,
    create_maintenance_record, update_maintenance_record, delete_maintenance_record,
    get_all_future_maintenance, get_future_maintenance_by_id_safe, mark_future_maintenance_completed,
    get_maintenance_summary, import_csv_data, export_vehicles_csv, export_maintenance_csv
)

# Initialize FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker", version="2.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_vehicle_names() -> list:
    """Get list of vehicle names for form dropdowns."""
    result = get_all_vehicles()
    if result["success"]:
        return [(vehicle.id, vehicle.name) for vehicle in result["vehicles"]]
    return []

def determine_form_type(record, return_url: Optional[str], form_type: Optional[str]) -> str:
    """Determine what type of form to show based on context."""
    if record:
        return "edit"
    elif return_url and "oil-management" in return_url:
        return "oil_change"
    elif form_type:
        return form_type
    else:
        return "maintenance"

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with summary statistics."""
    try:
        summary_result = get_maintenance_summary()
        if summary_result["success"]:
            summary = summary_result["summary"]
        else:
            summary = {"total_vehicles": 0, "total_records": 0, "total_cost": 0, "avg_cost": 0}
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "summary": summary
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms."""
    return {"status": "healthy", "message": "Vehicle Maintenance Tracker is running"}

# ============================================================================
# VEHICLE ROUTES
# ============================================================================

@app.get("/vehicles", response_class=HTMLResponse)
async def list_vehicles(request: Request):
    """List all vehicles."""
    try:
        result = get_all_vehicles()
        if result["success"]:
            vehicles = result["vehicles"]
        else:
            vehicles = []
        
        return templates.TemplateResponse("vehicles_list.html", {
            "request": request,
            "vehicles": vehicles
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/vehicles/new", response_class=HTMLResponse)
async def new_vehicle_form(request: Request, return_url: Optional[str] = Query(None)):
    """Form to create a new vehicle."""
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request,
        "vehicle": None,
        "return_url": return_url or "/vehicles"
    })

@app.get("/vehicles/{vehicle_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_form(request: Request, vehicle_id: int, return_url: Optional[str] = Query(None)):
    """Form to edit existing vehicle."""
    result = get_vehicle_by_id_safe(vehicle_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return templates.TemplateResponse("vehicle_form.html", {
        "request": request,
        "vehicle": result["vehicle"],
        "return_url": return_url or "/vehicles"
    })

@app.post("/vehicles")
async def create_vehicle_route(
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None)
):
    """Create a new vehicle."""
    # Auto-generate name if none provided
    if not name or name.strip() == "":
        name = f"{year} {make} {model}"
    
    result = create_vehicle(name, make, model, year, vin)
    
    if result["success"]:
        return RedirectResponse(url=return_url or "/vehicles", status_code=303)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/vehicles/{vehicle_id}")
async def update_vehicle_route(
    vehicle_id: int,
    name: Optional[str] = Form(None),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None)
):
    """Update an existing vehicle."""
    # Auto-generate name if none provided
    if not name or name.strip() == "":
        name = f"{year} {make} {model}"
    
    result = update_vehicle(vehicle_id, name, make, model, year, vin)
    
    if result["success"]:
        return RedirectResponse(url=return_url or "/vehicles", status_code=303)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.delete("/vehicles/{vehicle_id}/delete")
async def delete_vehicle_route(vehicle_id: int):
    """Delete a vehicle and all its maintenance records."""
    result = delete_vehicle(vehicle_id)
    
    if result["success"]:
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail=result["error"])

# ============================================================================
# MAINTENANCE ROUTES
# ============================================================================

@app.get("/maintenance", response_class=HTMLResponse)
async def list_maintenance(request: Request, vehicle_id: Optional[int] = Query(None)):
    """List maintenance records."""
    try:
        if vehicle_id:
            result = get_maintenance_records_by_vehicle(vehicle_id)
            if result["success"]:
                records = result["records"]
                vehicle_result = get_vehicle_by_id_safe(vehicle_id)
                vehicle = vehicle_result["vehicle"] if vehicle_result["success"] else None
                vehicle_name = vehicle.name if vehicle else f"Vehicle {vehicle_id}"
            else:
                records = []
                vehicle = None
                vehicle_name = None
        else:
            result = get_all_maintenance_records()
            if result["success"]:
                records = result["records"]
            else:
                records = []
            vehicle = None
            vehicle_name = None
        
        # Get summary data
        summary_result = get_maintenance_summary()
        summary = summary_result["summary"] if summary_result["success"] else {}
        
        # Get vehicles for future maintenance modal
        vehicles_result = get_all_vehicles()
        vehicles = vehicles_result["vehicles"] if vehicles_result["success"] else []
        
        # Get future maintenance records
        future_result = get_all_future_maintenance()
        future_maintenance = future_result["future_maintenance"] if future_result["success"] else []
        
        return templates.TemplateResponse("maintenance_list.html", {
            "request": request,
            "records": records,
            "vehicle": vehicle,
            "vehicle_name": vehicle_name,
            "summary": summary,
            "vehicles": vehicles,
            "future_maintenance": future_maintenance
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
    """Unified form handler for creating new maintenance, oil changes, and oil analysis."""
    vehicles = get_vehicle_names()
    
    # Determine what type of form to show
    detected_form_type = determine_form_type(None, return_url, form_type)
    
    # Pre-populate data from future maintenance if provided
    pre_populated_data = None
    if future_maintenance_id:
        result = get_future_maintenance_by_id_safe(future_maintenance_id)
        if result["success"]:
            future_maintenance = result["future_maintenance"]
            pre_populated_data = {
                "description": f"Oil Change - {future_maintenance.notes or 'Regular maintenance'}",
                "estimated_cost": future_maintenance.estimated_cost,
                "target_mileage": future_maintenance.target_mileage,
                "target_date": future_maintenance.target_date,
                "notes": future_maintenance.notes,
                "future_maintenance_id": future_maintenance.id
            }
    
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request,
        "vehicles": vehicles,
        "record": None,
        "return_url": return_url or "/maintenance",
        "selected_vehicle_id": vehicle_id,
        "form_type": detected_form_type,
        "pre_populated_data": pre_populated_data,
        "future_maintenance_id": future_maintenance_id,
        "is_oil_analysis": detected_form_type == "oil_analysis",
        "is_oil_change": detected_form_type == "oil_change"
    })

@app.get("/maintenance/{record_id}/edit", response_class=HTMLResponse)
async def edit_maintenance_form(
    request: Request,
    record_id: int,
    return_url: Optional[str] = Query(None)
):
    """Form to edit existing maintenance record."""
    result = get_maintenance_by_id_safe(record_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    vehicles = get_vehicle_names()
    
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request,
        "vehicles": vehicles,
        "record": result["record"],
        "return_url": return_url or "/maintenance"
    })

@app.post("/maintenance")
async def create_maintenance_route(
    vehicle_id: int = Form(...),
    date_str: str = Form(default=""),
    mileage: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None),
    is_oil_change: Optional[bool] = Form(None),
    oil_type: Optional[str] = Form(None),
    oil_brand: Optional[str] = Form(None),
    oil_filter_brand: Optional[str] = Form(None),
    oil_filter_part_number: Optional[str] = Form(None),
    oil_cost: Optional[float] = Form(None),
    filter_cost: Optional[float] = Form(None),
    labor_cost: Optional[float] = Form(None),
    photo: UploadFile = File(None),
    photo_description: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None),
    future_maintenance_id: Optional[int] = Form(None)
):
    """Create a new maintenance record."""
    try:
        # Handle photo upload
        photo_path = None
        if photo and photo.filename:
            import os
            import uuid
            
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(photo.filename)[1]
            unique_filename = f"photo_{uuid.uuid4().hex}{file_extension}"
            photo_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(photo_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
        
        # Create maintenance record
        result = create_maintenance_record(
            vehicle_id=vehicle_id,
            date_str=date_str,
            description=description,
            cost=cost,
            mileage=mileage,
            oil_change_interval=oil_change_interval,
            is_oil_change=is_oil_change,
            oil_type=oil_type,
            oil_brand=oil_brand,
            oil_filter_brand=oil_filter_brand,
            oil_filter_part_number=oil_filter_part_number,
            oil_cost=oil_cost,
            filter_cost=filter_cost,
            labor_cost=labor_cost,
            photo_path=photo_path,
            photo_description=photo_description
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Mark future maintenance record as completed if this was completing a future maintenance
        if future_maintenance_id:
            mark_result = mark_future_maintenance_completed(future_maintenance_id)
            if mark_result["success"]:
                print(f"Marked future maintenance {future_maintenance_id} as completed")
            else:
                print(f"Error marking future maintenance as completed: {mark_result['error']}")
        
        return RedirectResponse(url=return_url or "/maintenance", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create maintenance record: {str(e)}")

@app.post("/maintenance/{record_id}")
async def update_maintenance_route(
    record_id: int,
    vehicle_id: int = Form(...),
    date_str: str = Form(default=""),
    mileage: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    cost: Optional[float] = Form(None),
    oil_change_interval: Optional[int] = Form(None),
    is_oil_change: Optional[bool] = Form(None),
    oil_type: Optional[str] = Form(None),
    oil_brand: Optional[str] = Form(None),
    oil_filter_brand: Optional[str] = Form(None),
    oil_filter_part_number: Optional[str] = Form(None),
    oil_cost: Optional[float] = Form(None),
    filter_cost: Optional[float] = Form(None),
    labor_cost: Optional[float] = Form(None),
    photo: UploadFile = File(None),
    photo_description: Optional[str] = Form(None),
    return_url: Optional[str] = Form(None)
):
    """Update an existing maintenance record."""
    try:
        # Handle photo upload
        photo_path = None
        if photo and photo.filename:
            import os
            import uuid
            
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(photo.filename)[1]
            unique_filename = f"photo_{uuid.uuid4().hex}{file_extension}"
            photo_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(photo_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
        
        # Update maintenance record
        result = update_maintenance_record(
            record_id=record_id,
            vehicle_id=vehicle_id,
            date_str=date_str,
            description=description,
            cost=cost,
            mileage=mileage,
            oil_change_interval=oil_change_interval,
            is_oil_change=is_oil_change,
            oil_type=oil_type,
            oil_brand=oil_brand,
            oil_filter_brand=oil_filter_brand,
            oil_filter_part_number=oil_filter_part_number,
            oil_cost=oil_cost,
            filter_cost=filter_cost,
            labor_cost=labor_cost,
            photo_path=photo_path,
            photo_description=photo_description
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return RedirectResponse(url=return_url or "/maintenance", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update maintenance record: {str(e)}")

@app.delete("/maintenance/{record_id}/delete")
async def delete_maintenance_route(record_id: int):
    """Delete a maintenance record."""
    result = delete_maintenance_record(record_id)
    
    if result["success"]:
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail=result["error"])

# ============================================================================
# OIL MANAGEMENT ROUTES
# ============================================================================

@app.get("/oil-management", response_class=HTMLResponse)
async def oil_management(request: Request):
    """Oil management page."""
    try:
        # Get all vehicles with their oil change data
        vehicles_result = get_all_vehicles()
        vehicles = vehicles_result["vehicles"] if vehicles_result["success"] else []
        
        # Get future maintenance for oil changes
        future_result = get_all_future_maintenance()
        future_maintenance = future_result["future_maintenance"] if future_result["success"] else []
        
        return templates.TemplateResponse("oil_management_new.html", {
            "request": request,
            "vehicles": vehicles,
            "future_maintenance": future_maintenance
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

# ============================================================================
# IMPORT/EXPORT ROUTES
# ============================================================================

@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Import page."""
    try:
        vehicles_result = get_all_vehicles()
        vehicles = vehicles_result["vehicles"] if vehicles_result["success"] else []
        
        return templates.TemplateResponse("import.html", {
            "request": request,
            "vehicles": vehicles
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.post("/import")
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    vehicle_id: int = Form(...),
    handle_duplicates: str = Form("skip")
):
    """Import CSV data."""
    try:
        # Validate vehicle exists
        vehicle_result = get_vehicle_by_id_safe(vehicle_id)
        if not vehicle_result["success"]:
            raise HTTPException(status_code=400, detail="Selected vehicle not found")
        
        file_content = await file.read()
        result = import_csv_data(file_content.decode('utf-8'), vehicle_id)
        
        if result["success"]:
            return templates.TemplateResponse("import_result.html", {
                "request": request,
                "result": result["result"]
            })
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(content=f"<h1>Import Error</h1><p>{str(e)}</p>")

@app.get("/api/export/vehicles")
async def export_vehicles_csv_route():
    """Export vehicles to CSV."""
    result = export_vehicles_csv()
    
    if result["success"]:
        return Response(
            content=result["csv_content"],
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vehicles_export.csv"}
        )
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/export/maintenance")
async def export_maintenance_csv_route(vehicle_id: Optional[int] = Query(None)):
    """Export maintenance records to CSV."""
    result = export_maintenance_csv(vehicle_id)
    
    if result["success"]:
        return Response(
            content=result["csv_content"],
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=maintenance_export.csv"}
        )
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    print("Starting Vehicle Maintenance Tracker...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Templates directory exists: {os.path.exists('templates')}")
    print(f"Static directory exists: {os.path.exists('static')}")
    print(f"App directory exists: {os.path.exists('app')}")
    print(f"App directory contents: {os.listdir('app') if os.path.exists('app') else 'N/A'}")
    
    # Initialize database
    try:
        from database import init_db
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    
    print("Startup completed successfully!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
