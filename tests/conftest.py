import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import contextlib
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load env vars so tests can read DATABASE_URL_TEST or other overrides
load_dotenv()

# Normalize env for tests before importing the app (pydantic Settings requires dev/prod)
if os.getenv("DATABASE_USE") in (None, "test"):
    os.environ["DATABASE_USE"] = "dev"

from app.main import app
from app.core.config import get_settings
from app.db.session import get_db


@pytest.fixture(scope="session")
def test_database_url() -> str:
    # Prefer explicit env var if provided
    env_url = os.getenv("DATABASE_URL_TEST")
    if env_url:
        url = make_url(env_url)
        # Normalize to async driver for the async engine if needed
        if url.drivername.startswith("postgresql") and "+asyncpg" not in url.drivername:
            url = url.set(drivername="postgresql+asyncpg")
        return str(url.render_as_string(hide_password=False))

    # Fallback: derive from app DATABASE_URL by appending _test
    settings = get_settings()
    base = make_url(settings.database_url)
    test_db_name = f"{base.database}_test"
    return str(base.set(database=test_db_name).render_as_string(hide_password=False))


@pytest.fixture(scope="session", autouse=True)
def _create_test_database(test_database_url: str):
    # Create/drop the test database using psycopg2 in AUTOCOMMIT mode to avoid transaction issues
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    url = make_url(test_database_url)
    admin = url.set(database="postgres", drivername=url.drivername.replace("+asyncpg", ""))

    dsn = (
        f"dbname={admin.database} user={admin.username} password={admin.password} "
        f"host={admin.host} port={admin.port}"
    )
    db_name = url.database

    conn = psycopg2.connect(dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db_name,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        conn.close()

    yield

    conn = psycopg2.connect(dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            # terminate connections and drop db
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                (db_name,),
            )
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    finally:
        conn.close()


@pytest.fixture()
async def test_engine(migrated_db, test_database_url: str):
    # Create a new engine per test to ensure it's tied to the current event loop
    eng = create_async_engine(test_database_url, pool_pre_ping=True)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest.fixture(scope="session")
async def migrated_db(test_database_url: str):
    # Run Alembic migrations programmatically against the test DB
    from alembic.config import Config
    from alembic import command
    from pathlib import Path

    # Prepare alembic config pointing to our repo files
    root = Path(__file__).resolve().parents[1]
    # Disable interpolation so % in URLs (passwords) don't break configparser
    from configparser import ConfigParser, BasicInterpolation
    alembic_cfg = Config(str(root / "alembic.ini"))
    alembic_cfg.file_config._interpolation = BasicInterpolation()
    alembic_cfg.set_main_option("script_location", str(root / "alembic"))
    # Build URL from test_database_url; switch to psycopg2 when running sync, and escape % for configparser
    sync_url = make_url(test_database_url)
    if os.getenv("ALEMBIC_RUN_SYNC") == "1" and "+asyncpg" in sync_url.drivername:
        sync_url = sync_url.set(drivername="postgresql+psycopg2")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url.render_as_string(hide_password=False).replace('%','%%'))

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture()
async def async_session(test_engine, migrated_db) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)
    async with SessionLocal() as session:
        yield session


@pytest.fixture()
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    # Create a sessionmaker bound to the test engine; yield a fresh session per request
    SessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)

    async def _get_db_override() -> AsyncGenerator[AsyncSession, None]:
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()
