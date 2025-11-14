from sqlalchemy import text, inspect
from database import engine


def column_exists(engine, table, column):
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def run():
    with engine.begin() as conn:
        url = str(engine.url)
        if "postgresql" in url:
            print("Ensuring JSONB tire_meta on Postgres…")
            conn.execute(
                text(
                    """
DO $$
BEGIN
    ALTER TABLE maintenancerecord
        ADD COLUMN IF NOT EXISTS tire_meta JSONB;
EXCEPTION WHEN duplicate_column THEN
    NULL;
END $$;
"""
                )
            )
            conn.execute(
                text(
                    """
CREATE INDEX IF NOT EXISTS idx_maintenancerecord_tire_meta_gin
    ON maintenancerecord USING GIN (tire_meta);
"""
                )
            )
        else:
            if column_exists(engine, "maintenancerecord", "tire_meta"):
                print("✅ tire_meta already exists (SQLite)")
            else:
                print("Adding TEXT tire_meta to SQLite…")
                conn.execute(text("ALTER TABLE maintenancerecord ADD COLUMN tire_meta TEXT"))

    print("🎉 tire_meta migration complete")


if __name__ == "__main__":
    run()

