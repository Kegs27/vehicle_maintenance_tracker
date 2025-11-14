import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_oil_modal_contains_full_fields():
    response = client.get("/oil-management?open=add-oil")
    assert response.status_code == 200
    html = response.text

    required_tokens = [
        'name="vehicle_id"',
        'name="oil_brand"',
        'name="oil_filter_part_number"',
        'name="oil_cost"',
        'name="filter_cost"',
        'name="labor_cost"',
        'name="mileage"',
        'name="photo"',
        'name="photo_description"',
        'name="is_oil_change"',
    ]

    for token in required_tokens:
        assert token in html, f"Missing field: {token}"

    assert 'data-enhanced-form="true"' in html

