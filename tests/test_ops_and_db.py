import importlib


OPS_REQUIRED_FUNCTIONS = [
    "get_maintenance_by_id",
    "create_maintenance_record",
    "get_maintenance_records_by_vehicle",
]


def test_data_operations_exports_required():
    module = importlib.import_module("data_operations")
    missing = [name for name in OPS_REQUIRED_FUNCTIONS if not hasattr(module, name)]
    assert not missing, f"Missing ops functions: {missing}"

