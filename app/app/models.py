from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date as date_type
from pydantic import ConfigDict

class Vehicle(SQLModel, table=True):
    """Vehicle model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)  # Prevent duplicate vehicle names
    year: int
    make: str = Field(max_length=50)
    model: str = Field(max_length=50)
    vin: Optional[str] = Field(default=None, max_length=17, unique=True)  # Prevent duplicate VINs
    
    # Relationship to maintenance records with cascade delete
    maintenance_records: List["MaintenanceRecord"] = Relationship(
        back_populates="vehicle", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

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
