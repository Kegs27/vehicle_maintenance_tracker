from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional
import os
import json
from datetime import date, datetime

# Simple imports without complex error handling
from database import engine, init_db, get_session
from models import Vehicle, MaintenanceRecord
from importer import import_csv, ImportResult

# Create FastAPI app
app = FastAPI(title="Vehicle Maintenance Tracker")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

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

@app.get("/static/export-data.js")
async def serve_export_js():
    """Serve export-data.js with no-cache headers"""
    from fastapi.responses import FileResponse
    return FileResponse(
        "static/export-data.js",
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/debug/db")
async def debug_database(session: Session = Depends(get_session)):
    """Debug endpoint to check database contents"""
    try:
        # Check vehicles
        vehicles = session.execute(select(Vehicle)).scalars().all()
        vehicle_count = len(vehicles)
        
        # Check maintenance records
        records = session.execute(select(MaintenanceRecord)).scalars().all()
        record_count = len(records)
        
        # Check relationships
        vehicle_with_records = []
        for vehicle in vehicles:
            record_count_for_vehicle = len(vehicle.maintenance_records) if hasattr(vehicle, 'maintenance_records') else 0
            vehicle_with_records.append({
                "id": vehicle.id,
                "name": vehicle.name,
                "maintenance_count": record_count_for_vehicle
            })
        
        return {
            "status": "debug",
            "vehicles": vehicle_count,
            "maintenance_records": record_count,
            "vehicle_details": vehicle_with_records
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/vehicles")
async def debug_vehicles(session: Session = Depends(get_session)):
    """Debug endpoint to check vehicle data specifically"""
    try:
        vehicles = session.execute(select(Vehicle)).scalars().all()
        return {
            "status": "debug",
            "total_vehicles": len(vehicles),
            "vehicles": [
                {
                    "id": v.id,
                    "name": v.name,
                    "year": v.year,
                    "make": v.make,
                    "model": v.model,
                    "vin": v.vin
                } for v in vehicles
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    vehicle = session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    vehicle.name = name
    vehicle.year = year
    vehicle.make = make
    vehicle.model = model
    vehicle.vin = vin
    
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
    
    # Query maintenance records with vehicle relationships
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
async def new_maintenance_form(
    request: Request, 
    vehicle_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Form to add new maintenance record"""
    vehicles = session.execute(select(Vehicle).order_by(Vehicle.name)).scalars().all()
    
    # Check if a specific vehicle was selected
    selected_vehicle_id = vehicle_id
    
    return templates.TemplateResponse("maintenance_form.html", {
        "request": request, 
        "vehicles": vehicles, 
        "record": None,
        "selected_vehicle_id": selected_vehicle_id
    })

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
    # Load vehicles for the dropdown
    vehicles = session.execute(
        select(Vehicle)
        .order_by(Vehicle.name)
    ).scalars().all()
    
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
        # Read the file content as bytes
        file_content = await file.read()
        result = import_csv(file_content, vehicle_id, session, handle_duplicates)
        return templates.TemplateResponse("import_result.html", {"request": request, "result": result})
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/export/vehicles")
async def export_vehicles_csv(
    vehicle_ids: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Export vehicles to CSV"""
    from io import StringIO
    import csv
    
    try:
        # Parse vehicle IDs if provided
        if vehicle_ids:
            vehicle_id_list = [int(id.strip()) for id in vehicle_ids.split(',') if id.strip()]
            vehicles = session.execute(
                select(Vehicle).where(Vehicle.id.in_(vehicle_id_list))
            ).scalars().all()
        else:
            vehicles = session.execute(select(Vehicle)).scalars().all()
        
        # Debug logging
        print(f"Vehicles export query returned {len(vehicles)} vehicles")
        if vehicles:
            print(f"First vehicle: {vehicles[0]}")
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Year', 'Make', 'Model', 'VIN'])
        
        # Write data
        for vehicle in vehicles:
            print(f"Processing vehicle: {vehicle.name}, {vehicle.year} {vehicle.make} {vehicle.model}")
            writer.writerow([
                vehicle.name,
                vehicle.year,
                vehicle.make,
                vehicle.model,
                vehicle.vin or ''
            ])
        
        # Prepare response
        csv_content = output.getvalue()
        output.close()
        
        filename = f"vehicles_export_{vehicle_ids if vehicle_ids else 'all'}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in vehicles export: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/maintenance")
async def export_maintenance_csv(
    vehicle_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Export maintenance records to CSV"""
    from io import StringIO
    import csv
    
    try:
        # Query maintenance records with vehicle information using a join
        if vehicle_id:
            # Single vehicle export
            query = select(MaintenanceRecord, Vehicle).join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id).where(MaintenanceRecord.vehicle_id == vehicle_id)
            records_with_vehicles = session.execute(query.order_by(MaintenanceRecord.date.desc())).all()
        else:
            # All records export
            query = select(MaintenanceRecord, Vehicle).join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
            records_with_vehicles = session.execute(query.order_by(MaintenanceRecord.date.desc())).all()
        
        # Debug logging
        print(f"Maintenance export query returned {len(records_with_vehicles)} records")
        if records_with_vehicles:
            print(f"First record: {records_with_vehicles[0]}")
        
        # Debug: Check for orphaned records
        print(f"Total records found: {len(records_with_vehicles)}")
        for i, (record, vehicle) in enumerate(records_with_vehicles):
            if not vehicle:
                print(f"WARNING: Record {i} has no vehicle: record_id={record.id}, vehicle_id={record.vehicle_id}")
            else:
                print(f"Record {i}: vehicle_id={record.vehicle_id}, vehicle_name={vehicle.name}")
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Vehicle', 'Date', 'Mileage', 'Description', 'Cost', 'Notes'])
        
        # Write data
        for record, vehicle in records_with_vehicles:
            vehicle_name = f"{vehicle.year} {vehicle.make} {vehicle.model}" if vehicle else "Unknown Vehicle"
            date_str = record.date.strftime('%m/%d/%Y') if record.date and record.date.year > 1900 else "No date"
            mileage_str = f"{record.mileage:,}" if record.mileage and record.mileage > 0 else "0"
            cost_str = f"${record.cost:.2f}" if record.cost else ""
            
            print(f"Processing record: vehicle={vehicle_name}, date={date_str}, mileage={mileage_str}, description={record.description[:50]}...")
            
            writer.writerow([
                vehicle_name,
                date_str,
                mileage_str,
                record.description,
                cost_str,
                ""  # Notes column (empty for now)
            ])
        
        # Prepare response
        csv_content = output.getvalue()
        output.close()
        
        filename = f"maintenance_export_{vehicle_id if vehicle_id else 'all'}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in maintenance export: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/vehicles/pdf")
async def export_vehicles_pdf(
    vehicle_ids: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Export vehicles to PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    
    try:
        # Parse vehicle IDs if provided
        if vehicle_ids:
            vehicle_id_list = [int(id.strip()) for id in vehicle_ids.split(',') if id.strip()]
            vehicles = session.execute(
                select(Vehicle).where(Vehicle.id.in_(vehicle_id_list))
            ).scalars().all()
        else:
            vehicles = session.execute(select(Vehicle)).scalars().all()
        
        # Create PDF content
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        title = Paragraph("Vehicle Inventory Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Create table data
        table_data = [['Name', 'Year', 'Make', 'Model', 'VIN']]
        for vehicle in vehicles:
            table_data.append([
                vehicle.name,
                str(vehicle.year),
                vehicle.make,
                vehicle.model,
                vehicle.vin or 'N/A'
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Add summary
        summary = Paragraph(f"Total Vehicles: {len(vehicles)}", styles['Normal'])
        elements.append(summary)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"vehicles_report_{vehicle_ids if vehicle_ids else 'all'}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in vehicles PDF export: {e}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.get("/api/export/maintenance/pdf")
async def export_maintenance_pdf(
    vehicle_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Export maintenance records to PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    
    try:
        # Query maintenance records with vehicle information using a join
        if vehicle_id:
            # Single vehicle export
            query = select(MaintenanceRecord, Vehicle).join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id).where(MaintenanceRecord.vehicle_id == vehicle_id)
            records_with_vehicles = session.execute(query.order_by(MaintenanceRecord.date.desc())).all()
        else:
            # All records export
            query = select(MaintenanceRecord, Vehicle).join(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
            records_with_vehicles = session.execute(query.order_by(MaintenanceRecord.date.desc())).all()
        
        # Debug: Check for orphaned records
        print(f"Total records found: {len(records_with_vehicles)}")
        for i, (record, vehicle) in enumerate(records_with_vehicles):
            if not vehicle:
                print(f"WARNING: Record {i} has no vehicle: record_id={record.id}, vehicle_id={record.vehicle_id}")
            else:
                print(f"Record {i}: vehicle_id={record.vehicle_id}, vehicle_name={vehicle.name}")
        
        # Create PDF content with portrait orientation for better table layout
        buffer = BytesIO()
        from reportlab.lib.pagesizes import letter
        print(f"PDF page dimensions: {letter[0]} x {letter[1]} points")
        print(f"Available width: {letter[0] - inch} points ({letter[0]/72 - 1:.1f} inches)")
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        if vehicle_id:
            # Get vehicle info for single vehicle report
            vehicle_query = select(Vehicle).where(Vehicle.id == vehicle_id)
            vehicle = session.execute(vehicle_query).scalar_one_or_none()
            vehicle_title = f"Maintenance Report - {vehicle.year} {vehicle.make} {vehicle.model}" if vehicle else "Maintenance Report"
            title = Paragraph(vehicle_title, title_style)
        else:
            title = Paragraph("Maintenance Records Report", title_style)
        
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Create table data with full descriptions
        table_data = [['Vehicle', 'Date', 'Mileage', 'Description', 'Cost']]
        for record, vehicle in records_with_vehicles:
            vehicle_name = f"{vehicle.year} {vehicle.make} {vehicle.model}" if vehicle else "Unknown Vehicle"
            date_str = record.date.strftime('%m/%d/%Y') if record.date and record.date.year > 1900 else "No date"
            mileage_str = f"{record.mileage:,}" if record.mileage and record.mileage > 0 else "0"
            cost_str = f"${record.cost:.2f}" if record.cost else "N/A"
            
            # Format description with line breaks for long text (over 40 characters)
            description = record.description
            if len(description) > 40:
                # Find good break points for four lines around 40 characters
                words = description.split()
                line1 = ""
                line2 = ""
                line3 = ""
                line4 = ""
                current_line = ""
                line_count = 1
                
                for word in words:
                    if len(current_line + " " + word) <= 40 and line_count < 4:
                        current_line += (" " + word) if current_line else word
                    else:
                        if line_count == 1:
                            line1 = current_line
                            current_line = word
                            line_count = 2
                        elif line_count == 2:
                            line2 = current_line
                            current_line = word
                            line_count = 3
                        elif line_count == 3:
                            line3 = current_line
                            current_line = word
                            line_count = 4
                        else:
                            # Fourth line - add remaining words
                            line4 = current_line + " " + " ".join(words[words.index(word):])
                            break
                else:
                    # Handle remaining text
                    if line_count == 1:
                        line1 = current_line
                    elif line_count == 2:
                        line2 = current_line
                    elif line_count == 3:
                        line3 = current_line
                    else:
                        line4 = current_line
                
                # Format with appropriate line breaks
                if line4:
                    formatted_description = f"{line1}\n{line2}\n{line3}\n{line4}"
                elif line3:
                    formatted_description = f"{line1}\n{line2}\n{line3}"
                elif line2:
                    formatted_description = f"{line1}\n{line2}"
                else:
                    formatted_description = line1
            else:
                formatted_description = description
            
            # Debug: Print each row being added
            print(f"Adding row: Vehicle='{vehicle_name}', Date='{date_str}', Mileage='{mileage_str}', Description='{formatted_description[:50]}...', Cost='{cost_str}'")
            
            table_data.append([
                vehicle_name,
                date_str,
                mileage_str,
                formatted_description,  # Formatted description with line breaks if needed
                cost_str
            ])
        
        # Create table with columns sized for portrait page (8.5" wide, available width after margins: ~7.5")
        # Column widths: Vehicle(1.5) + Date(1.0) + Mileage(1.0) + Description(3.2) + Cost(0.8) = 7.5"
        table = Table(table_data, colWidths=[1.5*inch, 1.0*inch, 1.0*inch, 3.2*inch, 0.8*inch])
        
        # Debug: Print table dimensions
        print(f"Table columns: {len(table_data[0])}")
        print(f"Table data sample: {table_data[1] if len(table_data) > 1 else 'No data'}")
        print(f"Column widths: {[1.5, 1.0, 1.0, 3.2, 0.8]} inches")
        print(f"Total table width: {1.5 + 1.0 + 1.0 + 3.2 + 0.8} inches")
        
        # Enable automatic row height adjustment for better text wrapping
        table.hAlign = 'LEFT'
        table.allowSplitting = True
        
        # Set minimum row height to accommodate multi-line descriptions
        table.minRowHeight = 1.0*inch  # Minimum 1.0 inches per row for four lines
        
        # Force each row to be tall enough for four lines of text
        for i in range(1, len(table_data)):  # Skip header row
            table._argH[i] = 1.0*inch  # Set explicit height for each data row
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Use Helvetica for all data rows
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top align for better text wrapping
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Left align description column
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align vehicle column
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Center align date
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Right align mileage
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # Right align cost
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),  # Alternating row colors
            ('TOPPADDING', (0, 0), (-1, -1), 15),  # Increase top padding for more row height
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),  # Increase bottom padding for more row height
            ('LEFTPADDING', (0, 0), (-1, -1), 10),  # Increase left padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Increase right padding
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrapping for all cells
            ('SPLITLONGWORDS', (0, 0), (-1, -1), True),  # Split long words if needed
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Add summary
        total_cost = sum(record.cost for record, _ in records_with_vehicles if record.cost)
        summary = Paragraph(f"Total Records: {len(records_with_vehicles)} | Total Cost: ${total_cost:,.2f}", styles['Normal'])
        elements.append(summary)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"maintenance_report_{vehicle_id if vehicle_id else 'all'}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in maintenance PDF export: {e}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")
# Force rebuild Fri Aug 15 21:27:44 EDT 2025
