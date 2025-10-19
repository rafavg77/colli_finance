from __future__ import annotations

import logging


from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url

from app.core.config import get_settings

LOGGER = logging.getLogger("pre_migration_cleanup")


def _get_sync_database_url() -> str:
    settings = get_settings()
    url = make_url(settings.database_url)
    if url.drivername.endswith("+asyncpg"):
        url = url.set(drivername=url.drivername.replace("+asyncpg", "+psycopg2"))
    return url.render_as_string(hide_password=False)


def _apply_revision_aliases(engine) -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print(f"Detected tables: {table_names}")
    if "alembic_version" not in table_names:
        return

    has_banks = "banks" in table_names

    target_version = "0005_banks_listener" if has_banks else "0004_add_attachments"

    with engine.connect() as connection:
        # Normalize legacy revision identifiers to the current ones and collapse duplicates.
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
            {"version": target_version},
        )
        connection.commit()


def main() -> None:
    try:
        sync_url = _get_sync_database_url()
        engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
        try:
            print("Running pre-migration cleanup")
            _apply_revision_aliases(engine)
            with engine.connect() as conn:
                versions = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            LOGGER.info(
                "Pre-migration cleanup completed",
                extra={"details": {"event": "pre_migration_cleanup", "extra": {"versions": versions}}},
            )
            print(f"Pre-migration cleanup versions: {versions}")
        finally:
            engine.dispose()
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Pre-migration cleanup failed", exc_info=exc)
        print(f"Pre-migration cleanup failed: {exc}")


if __name__ == "__main__":
    main()
