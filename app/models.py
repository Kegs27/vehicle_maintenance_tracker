from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date as date_type
from pydantic import ConfigDict

class Vehicle(SQLModel, table=True):
    """Vehicle model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    year: int
    make: str = Field(max_length=50)
    model: str = Field(max_length=50)
    vin: Optional[str] = Field(default=None, max_length=17)
    
    # Relationship to maintenance records
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="vehicle")

class MaintenanceRecord(SQLModel, table=True):
    """Maintenance record model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    date: date_type = Field()  # Always required, but can be placeholder date
    mileage: int
    description: str = Field(max_length=500)
    cost: Optional[float] = Field(default=None, nullable=True)
    date_estimated: bool = Field(default=False)
    
    # Relationship to vehicle
    vehicle: Vehicle = Relationship(back_populates="maintenance_records")
