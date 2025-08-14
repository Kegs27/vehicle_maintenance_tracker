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

from database import engine, init_db, get_session
from models import Vehicle, MaintenanceRecord
from importer import import_csv, ImportResult

# Create FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files - only mount if the directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Continue startup even if database init fails
        # The app will handle database errors gracefully

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation"""
    return templates.TemplateResponse("index.html", {"request": request})

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

@app.get("/vehicles/{vehicle_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_form(request: Request, vehicle_id: int, session: Session = Depends(get_session)):
    """Form to edit vehicle"""
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
    """Update a vehicle"""
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.name = name
    vehicle.year = year
    vehicle.make = make
    vehicle.model = model
    vehicle.vin = vin
    
    session.add(vehicle)
    session.commit()
    return RedirectResponse(url="/vehicles", status_code=303)

@app.post("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    method: str = Query(...),
    session: Session = Depends(get_session)
):
    """Delete a vehicle and all its maintenance records"""
    if method != "DELETE":
        raise HTTPException(status_code=400, detail="Invalid method")
    
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Delete all maintenance records for this vehicle first
    maintenance_records = session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id)
    ).scalars().all()
    
    for record in maintenance_records:
        session.delete(record)
    
    # Delete the vehicle
    session.delete(vehicle)
    session.commit()
    
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
        # Filter by specific vehicle
        query = query.where(MaintenanceRecord.vehicle_id == vehicle_id)
        # Get vehicle info for the header
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
    else:
        vehicle = None
    
    records = session.execute(query.order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.mileage.desc())).scalars().all()
    
    # Sort records: integrate records with placeholder dates into chronological order based on mileage
    PLACEHOLDER_DATE = date(1900, 1, 1)
    PLACEHOLDER_MILEAGE = 0
    
    # Create a list of all records with their estimated chronological position
    records_with_timeline = []
    
    for record in records:
        if record.date != PLACEHOLDER_DATE:
            # Records with real dates get their actual date
            records_with_timeline.append((record, record.date, False))
        else:
            # Records without dates need to be positioned based on mileage
            records_with_timeline.append((record, None, True))
    
    # Sort records with real dates first
    records_with_real_dates = [(r, d, is_estimated) for r, d, is_estimated in records_with_timeline if not is_estimated]
    records_with_real_dates.sort(key=lambda x: x[1], reverse=True)  # Sort by date, newest first
    
    # For records without dates, estimate their chronological position based on mileage
    # Higher mileage = older (earlier in timeline), lower mileage = newer (later in timeline)
    records_without_dates = [(r, d, is_estimated) for r, d, is_estimated in records_with_timeline if is_estimated]
    records_without_dates.sort(key=lambda x: x[0].mileage, reverse=True)  # Sort by mileage, highest first
    
    # Now integrate records without dates into the chronological timeline
    integrated_records = []
    
    # Start with records that have real dates
    for record, record_date, is_estimated in records_with_real_dates:
        integrated_records.append(record)
    
    # Now insert records without dates based on their mileage
    for record, record_date, is_estimated in records_without_dates:
        # Find the right position to insert this record
        insert_position = 0
        
        # Find where this mileage fits in the chronological order
        for i, existing_record in enumerate(integrated_records):
            if existing_record.date != PLACEHOLDER_DATE:
                # For records with real dates, compare mileage
                if record.mileage >= existing_record.mileage:
                    insert_position = i
                    break
            else:
                # For records without dates, compare mileage directly
                if record.mileage >= existing_record.mileage:
                    insert_position = i
                    break
        
        # Insert at the found position
        integrated_records.insert(insert_position, record)
    
    # The final result is already in the right order
    sorted_records = integrated_records
    
    return templates.TemplateResponse("maintenance_list.html", {
        "request": request, 
        "sorted_records": sorted_records, 
        "filtered_vehicle": vehicle
    })

@app.get("/maintenance/new", response_class=HTMLResponse)
async def new_maintenance_form(request: Request, vehicle_id: Optional[int] = Query(None), session: Session = Depends(get_session)):
    """Show form to create new maintenance record"""
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request,
        "vehicles": vehicles,
        "record": None,
        "selected_vehicle_id": vehicle_id
    })

@app.post("/maintenance")
async def create_maintenance(
    request: Request,
    vehicle_id: int = Form(...),
    date: Optional[str] = Form(None),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    date_estimated: bool = Form(False),
    session: Session = Depends(get_session)
):
    """Create new maintenance record"""
    from datetime import date as date_class
    
    PLACEHOLDER_DATE = date_class(1900, 1, 1)
    PLACEHOLDER_MILEAGE = 0
    
    # Always provide both values, using placeholders when missing
    parsed_date = PLACEHOLDER_DATE
    if date and date.strip():
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    # If no mileage provided, use 0 as placeholder
    final_mileage = mileage if mileage is not None else PLACEHOLDER_MILEAGE
    
    maintenance_record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        date=parsed_date,
        mileage=final_mileage,
        description=description,
        cost=cost,
        date_estimated=(parsed_date == PLACEHOLDER_DATE or date_estimated)
    )
    
    session.add(maintenance_record)
    session.commit()
    
    return RedirectResponse(url="/maintenance", status_code=303)

@app.get("/maintenance/{record_id}/edit", response_class=HTMLResponse)
async def edit_maintenance_form(request: Request, record_id: int, session: Session = Depends(get_session)):
    """Form to edit maintenance record"""
    record = session.get(MaintenanceRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    return templates.TemplateResponse("maintenance_form.html", {"request": request, "record": record, "vehicles": vehicles})

@app.post("/maintenance/{record_id}")
async def update_maintenance(
    request: Request,
    record_id: int,
    vehicle_id: int = Form(...),
    date: Optional[str] = Form(None),
    mileage: Optional[int] = Form(None),
    description: str = Form(...),
    cost: Optional[float] = Form(None),
    date_estimated: bool = Form(False),
    session: Session = Depends(get_session)
):
    """Update existing maintenance record"""
    record = session.get(MaintenanceRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    from datetime import date as date_class
    
    PLACEHOLDER_DATE = date_class(1900, 1, 1)
    PLACEHOLDER_MILEAGE = 0
    
    # Always provide both values, using placeholders when missing
    parsed_date = PLACEHOLDER_DATE
    if date and date.strip():
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    # If no mileage provided, use 0 as placeholder
    final_mileage = mileage if mileage is not None else PLACEHOLDER_MILEAGE
    
    record.vehicle_id = vehicle_id
    record.date = parsed_date
    record.mileage = final_mileage
    record.description = description
    record.cost = cost
    record.date_estimated = (parsed_date == PLACEHOLDER_DATE or date_estimated)
    
    session.commit()
    
    return RedirectResponse(url="/maintenance", status_code=303)

@app.post("/maintenance/{record_id}/delete")
async def delete_maintenance_record(
    record_id: int,
    session: Session = Depends(get_session)
):
    """Delete a maintenance record"""
    record = session.get(MaintenanceRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    # Delete the maintenance record
    session.delete(record)
    session.commit()
    
    return RedirectResponse(url="/maintenance", status_code=303)

@app.get("/import", response_class=HTMLResponse)
async def import_form(request: Request, vehicle_id: Optional[int] = Query(None), session: Session = Depends(get_session)):
    """Show import form"""
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    
    return templates.TemplateResponse("import.html", {
        "request": request,
        "vehicles": vehicles,
        "selected_vehicle_id": vehicle_id
    })

@app.post("/import")
async def import_csv_endpoint(
    request: Request,
    vehicle_id: int = Form(...),
    file: UploadFile = File(...),
    handle_duplicates: str = Form("skip"),
    session: Session = Depends(get_session)
):
    """Import CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read file content
    content = await file.read()
    
    # Import CSV
    result = ImportResult()
    try:
        result = import_csv(content, vehicle_id, session, handle_duplicates)
    except Exception as e:
        result.errors.append(f"Import failed: {str(e)}")
    
    return templates.TemplateResponse("import_result.html", {
        "request": request,
        "result": result
    })

@app.post("/api/export/vehicles")
async def export_vehicles_data(request: Request, session: Session = Depends(get_session)):
    """Export data for selected vehicles"""
    try:
        # Parse the request body
        body = await request.body()
        data = json.loads(body)
        vehicle_ids = data.get("vehicle_ids", [])
        
        if not vehicle_ids:
            raise HTTPException(status_code=400, detail="No vehicle IDs provided")
        
        # Get selected vehicles with their maintenance records
        vehicles_data = []
        
        for vehicle_id in vehicle_ids:
            vehicle = session.get(Vehicle, vehicle_id)
            if vehicle:
                # Get maintenance records
                maintenance_records = session.execute(
                    select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vehicle_id)
                ).scalars().all()
                
                vehicles_data.append({
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "year": vehicle.year,
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "vin": vehicle.vin,
                    "maintenance_records": [
                        {
                            "date": record.date.isoformat() if record.date else None,
                            "mileage": record.mileage,
                            "description": record.description,
                            "cost": record.cost
                        }
                        for record in maintenance_records
                    ],
                    "oil_change_records": []  # We'll need to implement this separately
                })
        
        return vehicles_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
