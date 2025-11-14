.PHONY: dev dev-migrate test

# Run the dev server (uses .env -> vehicle_maintenance_dev)
dev:
	uvicorn main:app --reload

# Run DB migrations against the current DATABASE_URL
dev-migrate:
	python3 migrate_tire_meta.py

# Run tests
test:
	pytest -q

