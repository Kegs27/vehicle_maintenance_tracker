from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date as date_type, datetime
from pydantic import ConfigDict
from uuid import uuid4


def generate_uuid() -> str:
    """Return a UUID4 string as a string value."""
    return str(uuid4())


class Account(SQLModel, table=True):
    """Family account grouping vehicles for a user."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True, max_length=36)
    name: str = Field(max_length=100, description="Display name for the account")
    owner_user_id: str = Field(max_length=100, index=True, description="Identifier of owning user")
    is_default: bool = Field(default=False, description="Whether this is the owner's default account")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    vehicles: List["Vehicle"] = Relationship(back_populates="account")


class Vehicle(SQLModel, table=True):
    """Vehicle model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(foreign_key="account.id", description="Account the vehicle belongs to")
    name: str = Field(max_length=100, unique=True)  # Prevent duplicate vehicle names
    year: int
    make: str = Field(max_length=50)
    model: str = Field(max_length=50)
    vin: Optional[str] = Field(default=None, max_length=17, unique=True)  # Prevent duplicate VINs
    
    # Email notification fields (temporarily commented out until database migration)
    # email_notification_email: Optional[str] = Field(default=None, max_length=255, description="Email address for maintenance notifications")
    # email_notifications_enabled: bool = Field(default=False, description="Whether email notifications are enabled for this vehicle")
    # email_reminder_frequency: int = Field(default=7, description="Days between email reminders")
    # last_email_sent: Optional[date_type] = Field(default=None, description="Date of last email sent")
    
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
    
    # Relationship to future maintenance with cascade delete
    future_maintenance: List["FutureMaintenance"] = Relationship(
        back_populates="vehicle",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    account: Account = Relationship(back_populates="vehicles")

class MaintenanceRecord(SQLModel, table=True):
    """Maintenance record model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    date: date_type = Field()  # Always required, but can be placeholder date
    mileage: int
    description: Optional[str] = Field(default=None, max_length=500)
    cost: Optional[float] = Field(default=None, nullable=True)
    date_estimated: bool = Field(default=False)
    oil_change_interval: Optional[int] = Field(default=None, description="Miles until next oil change (for oil change records)")
    
    # Enhanced Oil Change Fields
    is_oil_change: bool = Field(default=False, description="Flag to identify oil change records")
    oil_type: Optional[str] = Field(default=None, max_length=20, description="Oil type (e.g., 5W-30, 10W-40)")
    oil_brand: Optional[str] = Field(default=None, max_length=50, description="Oil brand (e.g., Mobil 1, Castrol)")
    oil_filter_brand: Optional[str] = Field(default=None, max_length=50, description="Oil filter brand")
    oil_filter_part_number: Optional[str] = Field(default=None, max_length=50, description="Oil filter part number")
    oil_cost: Optional[float] = Field(default=None, description="Cost of oil only")
    filter_cost: Optional[float] = Field(default=None, description="Cost of filter only")
    labor_cost: Optional[float] = Field(default=None, description="Cost of labor")
    oil_analysis_report: Optional[str] = Field(default=None, description="Base64 encoded PDF or file path")
    oil_analysis_date: Optional[date_type] = Field(default=None, description="Date of oil analysis")
    next_oil_analysis_date: Optional[date_type] = Field(default=None, description="Next recommended oil analysis date")
    oil_analysis_cost: Optional[float] = Field(default=None, description="Cost of oil analysis")
    
    # Oil Analysis Metrics
    iron_level: Optional[float] = Field(default=None, description="Iron level from oil analysis (ppm)")
    aluminum_level: Optional[float] = Field(default=None, description="Aluminum level from oil analysis (ppm)")
    copper_level: Optional[float] = Field(default=None, description="Copper level from oil analysis (ppm)")
    viscosity: Optional[float] = Field(default=None, description="Oil viscosity from analysis")
    tbn: Optional[float] = Field(default=None, description="Total Base Number from oil analysis")
    fuel_dilution: Optional[float] = Field(default=None, description="Fuel dilution percentage")
    coolant_contamination: Optional[bool] = Field(default=None, description="Coolant contamination detected")
    driving_conditions: Optional[str] = Field(default=None, max_length=50, description="Driving conditions (severe, normal, towing)")
    oil_consumption_notes: Optional[str] = Field(default=None, max_length=500, description="Notes about oil consumption between changes")
    
    # Oil Analysis Linking
    linked_oil_change_id: Optional[int] = Field(default=None, description="ID of the oil change this analysis is linked to")
    
    # Photo Documentation
    photo_path: Optional[str] = Field(default=None, description="Path to uploaded photo file")
    photo_description: Optional[str] = Field(default=None, max_length=500, description="Description/tags for the photo")
    
    # Relationship to vehicle
    vehicle: Vehicle = Relationship(back_populates="maintenance_records")

class FuelEntry(SQLModel, table=True):
    """Fuel entry model for tracking fill-ups"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    date: date_type = Field()
    time: Optional[str] = Field(default=None, max_length=10, description="Time of fuel entry (HH:MM)")
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


class FutureMaintenance(SQLModel, table=True):
    """Future maintenance reminder model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    maintenance_type: str = Field(max_length=100, description="Type of maintenance (e.g., Oil Change, Brake Service)")
    target_mileage: Optional[int] = Field(default=None, description="Target mileage for maintenance")
    target_date: Optional[date_type] = Field(default=None, description="Target date for maintenance")
    mileage_reminder: int = Field(default=100, description="Miles before target to send reminder")
    date_reminder: int = Field(default=30, description="Days before target to send reminder")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated cost of maintenance")
    parts_link: Optional[str] = Field(default=None, max_length=500, description="Link to parts or part number")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Additional notes")
    is_recurring: bool = Field(default=False, description="Whether this is recurring maintenance")
    recurrence_interval_miles: Optional[int] = Field(default=None, description="Miles between recurring maintenance")
    recurrence_interval_months: Optional[int] = Field(default=None, description="Months between recurring maintenance")
    is_active: bool = Field(default=True, description="Whether this reminder is active")
    created_at: Optional[date_type] = Field(default_factory=date_type.today)
    updated_at: Optional[date_type] = Field(default_factory=date_type.today)
    
    # Email notification tracking (temporarily commented out until database migration)
    # email_sent: bool = Field(default=False, description="Whether email notification has been sent")
    # last_email_reminder: Optional[date_type] = Field(default=None, description="Date of last email reminder sent")
    
    # Relationship to vehicle
    vehicle: Vehicle = Relationship(back_populates="future_maintenance")


class EmailSubscription(SQLModel, table=True):
    """Email subscription model for vehicle notifications"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email_address: str = Field(max_length=255, description="Email address for notifications")
    vehicle_id: int = Field(foreign_key="vehicle.id", description="Vehicle to receive notifications for")
    is_active: bool = Field(default=True, description="Whether this subscription is active")
    reminder_frequency: int = Field(default=7, description="Days between email reminders")
    last_email_sent: Optional[date_type] = Field(default=None, description="Date of last email sent")
    created_at: Optional[date_type] = Field(default_factory=date_type.today)
    
    # Relationship to vehicle
    vehicle: Vehicle = Relationship()
