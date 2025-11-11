from fastapi.testclient import TestClient
import pytest

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_account_context",
        lambda request: {
            "scope": "all",
            "account": None,
            "account_id": None,
            "accounts": [],
        },
    )
    monkeypatch.setattr(main, "get_all_vehicles", lambda account_id=None: [])
    monkeypatch.setattr(main, "get_vehicle_by_id", lambda vehicle_id, account_id=None: type("Vehicle", (), {"id": int(vehicle_id)})())
    monkeypatch.setattr(main.ops, "get_future_maintenance_by_id", lambda *a, **kw: None)
    monkeypatch.setattr(main.ops, "update_maintenance_record", lambda *a, **kw: {"success": True})
    monkeypatch.setattr(main.ops, "mark_future_maintenance_completed", lambda *a, **kw: None)
    monkeypatch.setattr(main.ops, "get_maintenance_records_by_vehicle", lambda *a, **kw: [])
    monkeypatch.setattr(
        main.ops,
        "create_maintenance_record",
        lambda *a, **kw: {"success": True, "record": type("Obj", (), {"id": 1})()},
    )
    monkeypatch.setattr(main, "create_maintenance_record", main.ops.create_maintenance_record)
    monkeypatch.setattr(main, "get_maintenance_by_id", lambda *a, **kw: None)


def test_post_maintenance_422_on_invalid_vehicle():
    payload = {"vehicle_id": "", "date_str": "2025-11-01"}
    response = client.post("/maintenance", data=payload)
    assert response.status_code == 422


def test_post_maintenance_success_minimal(monkeypatch):
    called = {}

    def fake_create_maintenance_record(*, vehicle_id, date, description=None, cost=0.0, mileage=None, **kwargs):
        called["vehicle_id"] = vehicle_id
        called["date"] = date
        called["kwargs"] = kwargs
        return {"success": True, "record": type("Obj", (), {"id": 123})()}

    def fake_get_vehicle_by_id(vehicle_id, account_id=None):
        return type("Vehicle", (), {"id": int(vehicle_id)})

    monkeypatch.setattr(main.ops, "create_maintenance_record", fake_create_maintenance_record)
    monkeypatch.setattr(main, "create_maintenance_record", fake_create_maintenance_record)
    monkeypatch.setattr(main, "get_vehicle_by_id", fake_get_vehicle_by_id)

    payload = {"vehicle_id": "1", "date_str": "2025-11-01", "mileage": "100"}
    response = client.post("/maintenance", data=payload, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/maintenance")
    assert called["vehicle_id"] == 1
    assert called["date"] == "11/01/2025"

