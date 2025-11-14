import pathlib
import sys
from datetime import datetime

import pytest
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from pydantic import ValidationError

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import data_operations
from models import Account, Vehicle
from schemas import TireMeta


@pytest.fixture()
def test_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(data_operations, "SessionLocal", TestSessionLocal)
    return TestSessionLocal


def test_create_maintenance_with_tire_meta(test_session):
    session_factory = test_session

    with session_factory() as session:
        account = Account(name="Test Account", owner_user_id="tester")
        session.add(account)
        session.commit()
        session.refresh(account)

        vehicle = Vehicle(
            name="Test Vehicle",
            make="Test",
            model="Vehicle",
            year=2024,
            account_id=account.id,
        )
        session.add(vehicle)
        session.commit()
        session.refresh(vehicle)
        vehicle_id = vehicle.id

    tire = {
        "fl": {"in": 8, "mid": 8, "out": 7},
        "fr": {"in": 8, "mid": 8, "out": 7},
        "rl": {"in": 7, "mid": 7, "out": 6},
        "rr": {"in": 7, "mid": 7, "out": 6},
    }

    result = data_operations.create_maintenance_record(
        vehicle_id=vehicle_id,
        date="11/12/2025",
        description="Tire Rotation · test",
        cost=0.0,
        mileage=42000,
        tire_meta=tire,
    )

    assert result["success"]

    record = data_operations.get_maintenance_by_id(result["record"].id)
    assert record is not None
    assert record.tire_meta is not None
    assert record.tire_meta["fl"]["i"] == 8
    assert record.tire_meta["rr"]["o"] == 6
    assert record.tire_meta["units"] == "32nds"
    assert record.tire_meta["schema_version"] == 1
    measured_at = datetime.fromisoformat(record.tire_meta["measured_at"])
    assert measured_at.year >= 2024


def test_tire_meta_partial_data_normalizes(test_session):
    session_factory = test_session

    with session_factory() as session:
        account = Account(name="Test Account", owner_user_id="tester")
        session.add(account)
        session.commit()
        session.refresh(account)

        vehicle = Vehicle(
            name="Test Vehicle",
            make="Test",
            model="Vehicle",
            year=2024,
            account_id=account.id,
        )
        session.add(vehicle)
        session.commit()
        session.refresh(vehicle)
        vehicle_id = vehicle.id

    result = data_operations.create_maintenance_record(
        vehicle_id=vehicle_id,
        date="11/12/2025",
        description="Tire Rotation · partial",
        cost=0.0,
        mileage=42000,
        tire_meta={"fl": {"in": 9}},
    )

    assert result["success"]
    record = data_operations.get_maintenance_by_id(result["record"].id)
    assert record.tire_meta["fl"]["i"] == 9
    assert "fr" not in record.tire_meta


def test_tire_meta_validation_bounds():
    with pytest.raises(ValidationError):
        TireMeta.model_validate({"fl": {"in": -1}})

    with pytest.raises(ValidationError):
        TireMeta.model_validate({"fl": {"in": 21}})
