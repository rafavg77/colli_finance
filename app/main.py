from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.url import make_url

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.routers import audit, auth, cards, categories, habitos, summary, transactions, users
from app.crud.category import CategoryCRUD

settings = get_settings()
logger = configure_logging()
app = FastAPI(title=settings.app_name, version="1.0.0")


DEFAULT_CATEGORIES = [
    "Despensa",
    "Salud",
    "Diversión",
    "Alimenos",
    "Educación",
    "Transporte",
    "Servios",
]


def get_alembic_config() -> Config:
    root_path = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(root_path / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(root_path / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))
    return alembic_cfg


def sanitize_identifier(identifier: str) -> str:
    return identifier.replace('"', '""')


def create_database_if_not_exists() -> None:
    url = make_url(settings.database_url)
    if url.get_backend_name().startswith("postgresql"):
        database_name = url.database
        if not database_name:
            return
        admin_url = url.set(database="postgres", drivername=url.drivername.replace("+asyncpg", ""))
        engine_admin = create_engine(admin_url)
        try:
            with engine_admin.connect() as connection:
                result = connection.execute(
                    text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": database_name}
                ).scalar()
                if not result:
                    connection.execution_options(isolation_level="AUTOCOMMIT").execute(
                        text(f"CREATE DATABASE \"{sanitize_identifier(database_name)}\"")
                    )
        finally:
            engine_admin.dispose()


async def reset_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def apply_migrations() -> None:
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")


async def seed_categories() -> None:
    async with AsyncSessionLocal() as session:
        for name in DEFAULT_CATEGORIES:
            existing = await CategoryCRUD.get_by_name(session, name)
            if not existing:
                await CategoryCRUD.create(session, name=name)


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            "Unhandled exception",
            extra={
                "details": {
                    "event": "request_error",
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                    },
                }
            },
        )
        raise
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "HTTP request completed",
        extra={
            "details": {
                "event": "request",
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "extra": {
                    "method": request.method,
                    "path": request.url.path,
                },
            }
        },
    )
    return response


@app.exception_handler(Exception)
async def json_exception_handler(request: Request, exc: Exception):  # noqa: ANN201
    logger.error(
        "Application error",
        extra={
            "details": {
                "event": "exception",
                "extra": {
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                },
            }
        },
    )
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


@app.on_event("startup")
async def startup_event() -> None:
    create_database_if_not_exists()
    if settings.reset_db_on_start:
        await reset_database()
    if settings.migrate_on_start:
        await apply_migrations()
    await seed_categories()
    logger.info(
        "Startup completed",
        extra={"details": {"event": "startup", "extra": {"environment": settings.environment}}},
    )


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(summary.router)
app.include_router(audit.router)
app.include_router(habitos.router)
