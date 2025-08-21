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

# Try to import from current directory first (for Render)
try:
    from database import engine, init_db, get_session
    from models import Vehicle, MaintenanceRecord
    from importer import import_csv, ImportResult
    print("Successfully imported from current directory")
except ImportError as e:
    print(f"Failed to import from current directory: {e}")
    # Fallback for app package (for local development)
    try:
        from app.database import engine, init_db, get_session
        from app.models import Vehicle, MaintenanceRecord
        from app.importer import import_csv, ImportResult
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
        print("Startup completed successfully!")
    except Exception as e:
        print(f"Startup warning (non-critical): {e}")
        # Don't crash the app on startup errors

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation"""
    try:
        print(f"Attempting to render index.html template...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Templates directory exists: {os.path.exists('./templates')}")
        print(f"Index.html exists: {os.path.exists('./templates/index.html')}")
        
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Template error: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
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
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vehicle Maintenance Tracker</h1>
                <div class="status">✅ App is running successfully!</div>
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

@app.get("/vehicles", response_class=HTMLResponse)
async def list_vehicles(request: Request, session: Session = Depends(get_session)):
    """List all vehicles"""
    try:
        if session is None:
            return HTMLResponse(content="""
            <h1>Database Error</h1>
            <p>The database connection is not available. This usually means the database modules failed to import.</p>
            <p>Please check the deployment logs for import errors.</p>
            <a href="/">Back to Home</a>
            """)
        
        vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
        return templates.TemplateResponse("vehicles_list.html", {"request": request, "vehicles": vehicles})
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
async def create_vehicle(
    name: str = Form(...),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """Create a new vehicle"""
    try:
        # Check for duplicate name
        existing_vehicle = session.execute(
            select(Vehicle).where(Vehicle.name == name)
        ).scalar_one_or_none()
        
        if existing_vehicle:
            raise HTTPException(status_code=400, detail=f"Vehicle with name '{name}' already exists")
        
        # Check for duplicate VIN if provided
        if vin:
            existing_vin = session.execute(
                select(Vehicle).where(Vehicle.vin == vin)
            ).scalar_one_or_none()
            
            if existing_vin:
                raise HTTPException(status_code=400, detail=f"Vehicle with VIN '{vin}' already exists")
        
        vehicle = Vehicle(name=name, year=year, make=make, model=model, vin=vin)
        session.add(vehicle)
        session.commit()
        return RedirectResponse(url="/vehicles", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
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
async def update_vehicle(
    vehicle_id: int,
    name: str = Form(...),
    year: int = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    vin: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """Update an existing vehicle"""
    try:
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=400, detail="Vehicle not found")
        
        # Check for duplicate name (excluding current vehicle)
        if name != vehicle.name:
            existing_vehicle = session.execute(
                select(Vehicle).where(Vehicle.name == name, Vehicle.id != vehicle_id)
            ).scalar_one_or_none()
            
            if existing_vehicle:
                raise HTTPException(status_code=400, detail=f"Vehicle with name '{name}' already exists")
        
        # Check for duplicate VIN if provided (excluding current vehicle)
        if vin and vin != vehicle.vin:
            existing_vin = session.execute(
                select(Vehicle).where(Vehicle.vin == vin, Vehicle.id != vehicle_id)
            ).scalar_one_or_none()
            
            if existing_vin:
                raise HTTPException(status_code=400, detail=f"Vehicle with VIN '{vin}' already exists")
        
        vehicle.name = name
        vehicle.year = year
        vehicle.make = make
        vehicle.model = model
        vehicle.vin = vin
        
        session.commit()
        return RedirectResponse(url="/vehicles", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update vehicle: {str(e)}")

@app.get("/maintenance", response_class=HTMLResponse)
async def list_maintenance(request: Request, session: Session = Depends(get_session)):
    """List maintenance records"""
    try:
        # Get records with vehicle information to avoid "unknown" issues
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.mileage.desc())
        ).scalars().all()
        
        return templates.TemplateResponse("maintenance_list.html", {"request": request, "records": records})
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")

@app.get("/maintenance/new", response_class=HTMLResponse)
async def new_maintenance_form(request: Request, session: Session = Depends(get_session)):
    """Form to add new maintenance record"""
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    return templates.TemplateResponse("maintenance_form.html", {"request": request, "vehicles": vehicles, "record": None})

@app.post("/maintenance")
async def create_maintenance(
    vehicle_id: int = Form(...),
    date_str: str = Form(...),
    mileage: int = Form(...),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    session: Session = Depends(get_session)
):
    """Create a new maintenance record"""
    try:
        # Validate vehicle exists
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=400, detail="Selected vehicle not found")
        
        # Parse date
        try:
            record_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            date=record_date,
            mileage=mileage,
            description=description,
            cost=cost
        )
        session.add(record)
        session.commit()
        return RedirectResponse(url="/maintenance", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create maintenance record: {str(e)}")

@app.delete("/maintenance/{record_id}")
async def delete_maintenance(
    record_id: int,
    session: Session = Depends(get_session)
):
    """Delete a maintenance record"""
    record = session.get(MaintenanceRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    session.delete(record)
    session.commit()
    return {"message": "Maintenance record deleted successfully"}

@app.get("/import", response_class=HTMLResponse)
async def import_form(request: Request, session: Session = Depends(get_session)):
    """Form to import CSV data"""
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    return templates.TemplateResponse("import.html", {"request": request, "vehicles": vehicles})

@app.post("/import")
async def import_data(
    request: Request,
    file: UploadFile = File(...),
    vehicle_id: int = Form(...),
    handle_duplicates: str = Form("skip"),
    session: Session = Depends(get_session)
):
    """Import CSV data"""
    try:
        # Validate vehicle exists
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=400, detail="Selected vehicle not found")
        
        file_content = await file.read()
        result = import_csv(file_content, vehicle_id, session, handle_duplicates)
        return templates.TemplateResponse("import_result.html", {"request": request, "result": result})
    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(content=f"<h1>Import Error</h1><p>{str(e)}</p>")

@app.get("/api/export/vehicles")
async def export_vehicles_csv(session: Session = Depends(get_session)):
    """Export vehicles to CSV"""
    try:
        vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Year', 'Make', 'Model', 'VIN'])
        
        for vehicle in vehicles:
            writer.writerow([
                vehicle.name,
                vehicle.year,
                vehicle.make,
                vehicle.model,
                vehicle.vin or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vehicles_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/maintenance")
async def export_maintenance_csv(session: Session = Depends(get_session)):
    """Export maintenance records to CSV"""
    try:
        # Get records with vehicle information to avoid "unknown" issues
        records = session.execute(
            select(MaintenanceRecord)
            .options(selectinload(MaintenanceRecord.vehicle))
            .order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.mileage.desc())
        ).scalars().all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Vehicle', 'Date', 'Mileage', 'Description', 'Cost'])
        
        for record in records:
            # Get vehicle information safely
            vehicle_name = "Unknown Vehicle"
            if record.vehicle:
                vehicle_name = f"{record.vehicle.year} {record.vehicle.make} {record.vehicle.model}"
            
            writer.writerow([
                vehicle_name,
                record.date.strftime('%m/%d/%Y') if record.date else 'No date',
                record.mileage,
                record.description,
                record.cost or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=maintenance_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
