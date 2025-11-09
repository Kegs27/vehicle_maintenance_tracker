"""
Migration script to introduce Account model and backfill existing vehicles.
"""

from datetime import datetime
from typing import Dict
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, MetaData, String, Table, inspect, text, Boolean
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def _ensure_account_table(engine: Engine, inspector) -> None:
    """Create the account table if it does not already exist."""
    if "account" in inspector.get_table_names():
        return

    account_metadata = MetaData()
    account_table = Table(
        "account",
        account_metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(100), nullable=False),
        Column("owner_user_id", String(100), nullable=False, index=True),
        Column(
            "is_default",
            Boolean,
            nullable=False,
            server_default=text("FALSE") if engine.dialect.name.startswith("postgres") else text("0"),
        ),
        Column("created_at", DateTime(timezone=False), nullable=False, default=datetime.utcnow),
        Column("updated_at", DateTime(timezone=False), nullable=False, default=datetime.utcnow),
        sqlite_autoincrement=False,
    )
    account_metadata.create_all(engine, tables=[account_table])

    # Composite uniqueness per owner/name
    Index(
        "ix_account_owner_name_unique", account_table.c.owner_user_id, account_table.c.name, unique=True
    ).create(engine)


def _ensure_account_columns(engine: Engine) -> None:
    """Make sure existing account table has required columns."""
    inspector = inspect(engine)
    if "account" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("account")}
    if "is_default" not in columns:
        column_type = "BOOLEAN" if engine.dialect.name.startswith("postgres") else "INTEGER"
        default_value = "FALSE" if engine.dialect.name.startswith("postgres") else "0"
        with engine.begin() as conn:
            conn.execute(
                text(f"ALTER TABLE account ADD COLUMN is_default {column_type} DEFAULT {default_value} NOT NULL")
            )


def _ensure_vehicle_account_column(engine: Engine, inspector) -> None:
    """Add the account_id column to vehicle table when missing."""
    vehicle_columns = {column["name"] for column in inspector.get_columns("vehicle")}
    if "account_id" in vehicle_columns:
        return

    column_type = "UUID" if engine.dialect.name in ("postgresql", "postgresql+psycopg") else "TEXT"
    alter_sql = f"ALTER TABLE vehicle ADD COLUMN account_id {column_type}"
    with engine.begin() as conn:
        conn.execute(text(alter_sql))

    # Refresh inspector cache
    inspector = inspect(engine)
    vehicle_columns = {column["name"] for column in inspector.get_columns("vehicle")}
    if "account_id" not in vehicle_columns:
        raise RuntimeError("Failed to add account_id column to vehicle table")

    # Add index for faster lookups
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_vehicle_account_id ON vehicle(account_id)"))


def _ensure_vehicle_owner_account_index(engine: Engine) -> None:
    """Create composite index on (owner_user_id, account_id) when owner column exists."""
    # Only add the index if the vehicle table actually has owner_user_id column (future-proof)
    inspector = inspect(engine)
    vehicle_columns = {column["name"] for column in inspector.get_columns("vehicle")}
    if "owner_user_id" not in vehicle_columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_vehicle_owner_account ON vehicle(owner_user_id, account_id)"
            )
        )


def _ensure_seed_accounts(engine: Engine) -> Dict[str, str]:
    """
    Create baseline demo accounts and return mapping of account name -> id.
    """
    seed_accounts = ["Kory", "Kelley", "James Miller"]
    owner_user_id = "kory"
    account_ids: Dict[str, str] = {}

    with engine.begin() as conn:
        for name in seed_accounts:
            existing = conn.execute(
                text(
                    "SELECT id FROM account WHERE owner_user_id = :owner AND name = :name"
                ),
                {"owner": owner_user_id, "name": name},
            ).scalar()
            if existing:
                account_ids[name] = existing
                if name == "Kory":
                    conn.execute(
                        text(
                            "UPDATE account SET is_default = :is_default WHERE id = :id AND is_default <> :is_default"
                        ),
                        {"id": existing, "is_default": True},
                    )
                continue

            new_id = str(uuid4())
            conn.execute(
                text(
                    """
                    INSERT INTO account (id, name, owner_user_id, is_default, created_at, updated_at)
                    VALUES (:id, :name, :owner, :is_default, :created_at, :updated_at)
                    """
                ),
                {
                    "id": new_id,
                    "name": name,
                    "owner": owner_user_id,
                    "is_default": True if name == "Kory" else False,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            account_ids[name] = new_id

    return account_ids


def _backfill_vehicle_accounts(engine: Engine, account_ids: Dict[str, str]) -> None:
    """Assign existing vehicles to the default Kory account when missing."""
    kory_account_id = account_ids.get("Kory")
    if not kory_account_id:
        raise RuntimeError("Expected Kory account to exist for vehicle backfill")

    with engine.begin() as conn:
        # Update vehicles with NULL account_id to default account
        conn.execute(
            text(
                """
                UPDATE vehicle
                SET account_id = :account_id
                WHERE account_id IS NULL OR account_id = ''
                """
            ),
            {"account_id": kory_account_id},
        )


def run_migration_with_existing_engine(engine: Engine) -> bool:
    """Entry point used by the FastAPI app to run the migration."""
    try:
        inspector = inspect(engine)
        _ensure_account_table(engine, inspector)
        _ensure_account_columns(engine)
        _ensure_vehicle_account_column(engine, inspector)
        _ensure_vehicle_owner_account_index(engine)
        account_ids = _ensure_seed_accounts(engine)
        _backfill_vehicle_accounts(engine, account_ids)

        # Attempt to enforce NOT NULL constraint where supported (PostgreSQL)
        if engine.dialect.name.startswith("postgres"):
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE vehicle ALTER COLUMN account_id SET NOT NULL"))

        return True
    except SQLAlchemyError as exc:
        print(f"❌ Account migration failed: {exc}")
        return False
    except Exception as exc:
        print(f"❌ Unexpected account migration error: {exc}")
        return False


def run_migration() -> bool:
    """Standalone runner that creates its own engine (SQLite fallback)."""
    from database import engine  # Lazy import to avoid circular dependency

    return run_migration_with_existing_engine(engine)


