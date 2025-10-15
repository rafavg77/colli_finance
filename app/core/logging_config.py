import logging
from datetime import datetime, timezone
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from .config import get_settings


class UTCFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        log_record.setdefault("app", settings.app_name)
        log_record.setdefault("service", settings.service_name)
        log_record.setdefault("module", record.name)
        log_record["level"] = record.levelname.lower()
        if "details" not in log_record:
            log_record["details"] = {}


settings = get_settings()
_configured = False

# In case Uvicorn config runs after import, provide a helper to re-tune loggers
# without re-creating handlers. This is safe to call multiple times.


def configure_logging() -> logging.Logger:
    global _configured
    if _configured:
        # Re-ajustar niveles y propagación de loggers de librerías en cada llamada
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        _tune_library_loggers()
        return root_logger

    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()

    formatter = UTCFormatter("%(timestamp)s %(level)s %(message)s")

    # Stream handler para consola
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.addHandler(stream_handler)

    # Configurar loggers específicos de librerías
    _tune_library_loggers()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    _configured = True
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(module_name)


def _tune_library_loggers() -> None:
    """Ensure third-party loggers forward to our root handler.

    Uvicorn config can override logger handlers/propagation during startup.
    We clear their handlers and enable propagation so our root stream handler
    formats everything (including access logs) as JSON. Safe to call multiple times.
    """
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    # Access logs must not be disabled and should propagate
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"):
        lib_logger = logging.getLogger(name)
        lib_logger.disabled = False
        lib_logger.setLevel(level if name != "uvicorn.access" else logging.INFO)
        # Remove their own handlers and propagate to root
        lib_logger.handlers.clear()
        lib_logger.propagate = True

    # Common noisy libraries - keep at WARNING unless overridden
    logging.getLogger("h11").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)