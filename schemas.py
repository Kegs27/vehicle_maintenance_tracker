from decimal import Decimal, InvalidOperation
import re
from typing import Optional, Literal
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


def to_decimal(val):
  if val is None:
    return None
  text = str(val).strip()
  if text == "":
    return None
  try:
    cleaned = re.sub(r"[^\d.\-]", "", text)
    return Decimal(cleaned).quantize(Decimal("0.01"))
  except (InvalidOperation, ValueError):
    raise ValueError("Invalid currency amount")


def to_bool(val):
  if val is None:
    return False
  if isinstance(val, bool):
    return val
  normalized = str(val).strip().lower()
  return normalized in {"1", "true", "on", "yes"}


def normalize_date_str(val: Optional[str]) -> Optional[str]:
  if val is None:
    return None
  text = val.strip()
  if not text:
    return None
  iso_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
  if iso_match:
    year, month, day = iso_match.groups()
    return f"{month}/{day}/{year}"
  if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
    return text
  raise ValueError("Invalid date format (use MM/DD/YYYY or YYYY-MM-DD)")


class BaseForm(BaseModel):
  @field_validator("*", mode="before")
  @classmethod
  def blank_to_none(cls, value):
    if isinstance(value, str) and value.strip() == "":
      return None
    return value


class Tread(BaseModel):
  model_config = ConfigDict(extra="forbid", populate_by_name=True)

  i: Optional[int] = Field(default=None, alias="in")
  m: Optional[int] = Field(default=None, alias="mid")
  o: Optional[int] = Field(default=None, alias="out")

  @field_validator("i", "m", "o", mode="before")
  @classmethod
  def validate_depth(cls, value):
    if value is None:
      return None
    if isinstance(value, str):
      parsed = value.strip()
      if parsed == "":
        return None
      value = parsed
    try:
      number = float(value)
    except (TypeError, ValueError):
      raise ValueError("Tread depth must be numeric")
    if not number.is_integer():
      raise ValueError("Tread depth must be a whole number in 32nds")
    depth = int(number)
    if depth < 0 or depth > 20:
      raise ValueError("Tread depth must be between 0 and 20 (32nds)")
    return depth


class TireMeta(BaseModel):
  model_config = ConfigDict(extra="forbid", populate_by_name=True)

  fl: Optional[Tread] = None
  fr: Optional[Tread] = None
  rl: Optional[Tread] = None
  rr: Optional[Tread] = None
  units: Literal["32nds"] = "32nds"
  measured_at: Optional[datetime] = None
  pattern: Optional[Literal["front-to-rear", "cross", "five-tire", "custom", "unknown"]] = None
  schema_version: Literal[1] = 1

  def has_measurements(self) -> bool:
    for tire in (self.fl, self.fr, self.rl, self.rr):
      if not tire:
        continue
      if any(
          getattr(tire, attr) is not None
          for attr in ("i", "m", "o")
      ):
        return True
    return False


class MaintenanceCreate(BaseForm):
  vehicle_id: int = Field(..., description="Vehicle")
  date_str: Optional[str] = Field(None, description="MM/DD/YYYY or YYYY-MM-DD")
  mileage: Optional[int] = Field(None, ge=0)
  description: Optional[str] = Field(None, max_length=1000)
  cost: Optional[Decimal] = None
  oil_change_interval: Optional[int] = Field(None, ge=0)
  link_oil_analysis: bool = False

  is_oil_change: Optional[bool] = False
  oil_type: Optional[str] = None
  oil_brand: Optional[str] = None
  oil_filter_brand: Optional[str] = None
  oil_filter_part_number: Optional[str] = None
  oil_cost: Optional[Decimal] = None
  filter_cost: Optional[Decimal] = None
  labor_cost: Optional[Decimal] = None

  oil_analysis_date: Optional[str] = None
  next_oil_analysis_date: Optional[str] = None
  oil_analysis_cost: Optional[Decimal] = None
  iron_level: Optional[float] = None
  aluminum_level: Optional[float] = None
  copper_level: Optional[float] = None
  viscosity: Optional[float] = None
  tbn: Optional[float] = None
  fuel_dilution: Optional[float] = None
  coolant_contamination: Optional[bool] = None
  driving_conditions: Optional[str] = None
  oil_consumption_notes: Optional[str] = None

  photo_description: Optional[str] = None
  return_url: Optional[str] = None
  future_maintenance_id: Optional[int] = None

  @field_validator("date_str", mode="before")
  @classmethod
  def validate_date(cls, value):
    return normalize_date_str(value)

  @field_validator("oil_analysis_date", "next_oil_analysis_date", mode="before")
  @classmethod
  def validate_analysis_dates(cls, value):
    return normalize_date_str(value)

  @field_validator(
      "cost",
      "oil_cost",
      "filter_cost",
      "labor_cost",
      "oil_analysis_cost",
      mode="before",
  )
  @classmethod
  def validate_money(cls, value):
    return to_decimal(value)

  @field_validator("is_oil_change", "coolant_contamination", "link_oil_analysis", mode="before")
  @classmethod
  def validate_bools(cls, value):
    return to_bool(value)

  @model_validator(mode="after")
  def sanity_check(self):
    return self

