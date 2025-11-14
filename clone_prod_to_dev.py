#!/usr/bin/env python3
"""
Clone production PostgreSQL database to dev PostgreSQL database on Render.

- Uses PROD_DATABASE_URL if set, otherwise DATABASE_URL.
- Expects prod DB name like: vehicle_maintenance
- Dev DB will be: vehicle_maintenance_dev
"""

import os
from urllib.parse import urlparse

from sqlalchemy import text
from sqlmodel import create_engine


def get_prod_url() -> str:
    prod_url = os.environ.get("PROD_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not prod_url:
        raise SystemExit("❌ Set PROD_DATABASE_URL (or DATABASE_URL) to your *prod* connection string.")

    # Normalize driver prefix for SQLAlchemy/psycopg
    if prod_url.startswith("postgres://"):
        prod_url = prod_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif prod_url.startswith("postgresql://") and "+psycopg" not in prod_url:
        prod_url = prod_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return prod_url


def main() -> None:
    prod_url = get_prod_url()
    parsed = urlparse(prod_url)

    prod_db = parsed.path.lstrip("/") or "vehicle_maintenance"
    dev_db = prod_db + "_dev"

    # Connect to the 'postgres' maintenance DB on the same server so we can manage databases
    admin_url = prod_url.rsplit("/", 1)[0] + "/postgres"

    print(f"Using admin URL: {admin_url}")
    print(f"Prod DB: {prod_db}")
    print(f"Dev DB:  {dev_db}")

    engine = create_engine(admin_url)

    confirm = input(
        f"⚠️  This will DROP and RECREATE database '{dev_db}' as a clone of '{prod_db}'. Continue? (yes/no): "
    ).strip().lower()
    if confirm != "yes":
        print("❌ Clone cancelled.")
        return

    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        print(f"🔄 Dropping {dev_db} if it exists...")
        conn.execute(text(f"DROP DATABASE IF EXISTS {dev_db}"))

        print(f"📀 Creating {dev_db} from template {prod_db}...")
        conn.execute(
            text(f"CREATE DATABASE {dev_db} WITH TEMPLATE {prod_db} OWNER {parsed.username}")
        )

    print("🎉 Clone complete. Dev DB is now a copy of prod.")


if __name__ == "__main__":
    main()

