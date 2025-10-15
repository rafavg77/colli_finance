from __future__ import annotations
from pathlib import Path
from typing import Callable
import asyncio
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
from app.core.logging_config import get_logger, configure_logging
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.routers import audit, auth, cards, categories, habitos, summary, transactions, users
from app.routers import transfers
from app.crud.category import CategoryCRUD

settings = get_settings()
logger = get_logger(__name__)
app = FastAPI(title=settings.app_name, version=settings.app_version)

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    start_time = time.perf_counter()
    
    # Log de inicio con estructura JSON
    logger.info(
        "HTTP request started", 
        extra={
            "details": {
                "event": "request_start",
                "extra": {
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": request.client.host if request.client else None
                }
            }
        }
    )
    
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            "Unhandled exception in request",
            extra={
                "details": {
                    "event": "request_error",
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(exc),
                        "error_type": type(exc).__name__
                    },
                }
            },
        )
        raise
    
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Determinar el nivel de log basado en el status code
    log_level = "error" if response.status_code >= 400 else "info"
    log_message = "HTTP request completed"
    
    if log_level == "error":
        logger.error(
            log_message,
            extra={
                "details": {
                    "event": "request_completed",
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                    },
                }
            },
        )
    else:
        logger.info(
            log_message,
            extra={
                "details": {
                    "event": "request_completed",
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

logger.info(
    "HTTP middleware registered successfully",
    extra={
        "details": {
            "event": "middleware_setup",
            "extra": {
                "middleware": "log_requests"
            }
        }
    }
)

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
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    redacted_url = make_url(settings.database_url).render_as_string(hide_password=True)
    logger.debug(
        "Alembic configuration prepared",
        extra={"details": {"event": "alembic_config", "extra": {"database_url": redacted_url}}},
    )
    return alembic_cfg


def sanitize_identifier(identifier: str) -> str:
    return identifier.replace('"', '""')


def create_database_if_not_exists() -> None:
    url = make_url(settings.database_url)
    if url.get_backend_name().startswith("postgresql"):
        database_name = url.database
        if not database_name:
            logger.warning(
                "Database name missing in URL",
                extra={"details": {"event": "database_setup", "extra": {"url": str(url)}}},
            )
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
                    logger.info(
                        "Database created",
                        extra={"details": {"event": "database_setup", "extra": {"database": database_name}}},
                    )
                else:
                    logger.debug(
                        "Database already exists",
                        extra={"details": {"event": "database_setup", "extra": {"database": database_name}}},
                    )
        finally:
            engine_admin.dispose()


async def reset_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Database reset executed", extra={"details": {"event": "database_reset"}})


async def apply_migrations() -> None:
    alembic_cfg = get_alembic_config()
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    logger.info("Migrations applied", extra={"details": {"event": "database_migrate"}})


async def seed_categories() -> None:
    async with AsyncSessionLocal() as session:
        for name in DEFAULT_CATEGORIES:
            existing = await CategoryCRUD.get_by_name(session, name)
            if not existing:
                await CategoryCRUD.create(session, name=name)
                logger.info(
                    "Default category created",
                    extra={"details": {"event": "seed_category", "extra": {"name": name}}},
                )
            else:
                logger.debug(
                    "Category already present",
                    extra={"details": {"event": "seed_category", "extra": {"name": name}}},
                )

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
    logger.info(
        "Startup sequence initiated",
        extra={"details": {"event": "startup", "extra": {"environment": settings.environment, "stage": "init"}}},
    )
    create_database_if_not_exists()
    if settings.reset_db_on_start:
        await reset_database()
    if settings.migrate_on_start:
        await apply_migrations()
    await seed_categories()
    # Re-aplicar configuración de loggers por si Uvicorn alteró propagación/handlers
    configure_logging()
    logger.info(
        "Startup completed",
        extra={"details": {"event": "startup", "extra": {"environment": settings.environment}}},
    )


@app.get("/health", tags=["System"])
async def healthcheck():
    logger.info("Health check", extra={"details": {"event": "health"}})
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(summary.router)
app.include_router(audit.router)
app.include_router(habitos.router)
app.include_router(transfers.router)