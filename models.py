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
    
    # Relationship to fuel entries with cascade delete
    fuel_entries: List["FuelEntry"] = Relationship(
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

class FuelEntry(SQLModel, table=True):
    """Fuel entry model for tracking fill-ups"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    date: date_type = Field()
    mileage: int
    fuel_amount: float = Field(description="Fuel amount in gallons")
    fuel_cost: float = Field(description="Total fuel cost")
    fuel_type: str = Field(max_length=10, description="87, 89, 91, 93, diesel")
    driving_pattern: str = Field(max_length=20, description="highway, city, mixed")
    notes: Optional[str] = Field(default=None, max_length=500)
    odometer_photo: Optional[str] = Field(default=None, description="Base64 encoded image or file path")
    created_at: Optional[date_type] = Field(default_factory=date_type.today)
    updated_at: Optional[date_type] = Field(default_factory=date_type.today)
    
    # Relationship to vehicle
    vehicle: Vehicle = Relationship(back_populates="fuel_entries")
