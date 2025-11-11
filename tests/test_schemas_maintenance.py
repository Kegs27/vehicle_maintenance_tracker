from decimal import Decimal

import pytest

from schemas import MaintenanceCreate


def test_date_normalization_iso_to_us():
    schema = MaintenanceCreate(vehicle_id=1, date_str="2025-11-01")
    assert schema.date_str == "11/01/2025"


def test_date_normalization_blank_is_none():
    schema = MaintenanceCreate(vehicle_id=1, date_str="")
    assert schema.date_str is None


def test_money_parsing_dollars():
    schema = MaintenanceCreate(vehicle_id=1, cost="$41.48")
    assert schema.cost == Decimal("41.48")


@pytest.mark.parametrize("value", ["1", "true", "on", "yes", True])
def test_boolean_parsing_various_truthy(value):
    schema = MaintenanceCreate(vehicle_id=1, is_oil_change=value)
    assert schema.is_oil_change is True


def test_negative_mileage_rejected():
    with pytest.raises(Exception):
        MaintenanceCreate(vehicle_id=1, mileage=-1)


def test_blank_to_none_for_optional_fields():
    schema = MaintenanceCreate(vehicle_id=1, description="", oil_type="")
    assert schema.description in ("", None)
    assert schema.oil_type is None


def test_analysis_fields_any_present_tracked():
    schema = MaintenanceCreate(vehicle_id=1, oil_analysis_date="2025-11-02")
    assert schema.oil_analysis_date == "11/02/2025"

