from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional
import os
import json
from datetime import date, datetime

# Simple imports without complex error handling
from app.database import engine, init_db, get_session
from app.models import Vehicle, MaintenanceRecord
from app.importer import import_csv, ImportResult

# Create FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Static files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Vehicle Maintenance Tracker...")
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    print("✅ Application startup complete!")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return {"status": "ok", "message": "Vehicle Maintenance Tracker is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "healthy", "message": "Vehicle Maintenance Tracker is running"}

@app.get("/vehicles", response_class=HTMLResponse)
async def list_vehicles(request: Request, session: Session = Depends(get_session)):
    """List all vehicles"""
    vehicles = session.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.maintenance_records))
        .order_by(Vehicle.name)
    ).scalars().all()
    return templates.TemplateResponse("vehicles_list.html", {"request": request, "vehicles": vehicles})

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
    vehicle = Vehicle(name=name, year=year, make=make, model=model, vin=vin)
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return RedirectResponse(url="/vehicles", status_code=303)

@app.get("/maintenance", response_class=HTMLResponse)
async def list_maintenance(
    request: Request, 
    vehicle_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """List maintenance records, optionally filtered by vehicle"""
    from sqlalchemy.orm import selectinload
    
    query = select(MaintenanceRecord).options(selectinload(MaintenanceRecord.vehicle))
    
    if vehicle_id:
        query = query.where(MaintenanceRecord.vehicle_id == vehicle_id)
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
    else:
        vehicle = None
    
    records = session.execute(query.order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.mileage.desc())).scalars().all()
    
    return templates.TemplateResponse("maintenance_list.html", {"request": request, "records": records, "vehicle": vehicle})

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
        record_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        record_date = date(1900, 1, 1)  # Placeholder date
    
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

@app.get("/import", response_class=HTMLResponse)
async def import_form(request: Request):
    """Form to import CSV data"""
    return templates.TemplateResponse("import.html", {"request": request})

@app.post("/import")
async def import_data(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Import CSV data"""
    try:
        result = import_csv(file.file, session)
        return templates.TemplateResponse("import_result.html", {"request": Request, "result": result})
    except Exception as e:
        return {"error": str(e)}
