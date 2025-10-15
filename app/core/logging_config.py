import logging
from datetime import datetime, timezone
from typing import Any, Dict

from logging_loki import LokiHandler
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
_configured_logger: logging.Logger | None = None


def configure_logging() -> logging.Logger:
    global _configured_logger
    if _configured_logger:
        return _configured_logger

    logger = logging.getLogger(settings.app_name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = UTCFormatter("%(timestamp)s %(level)s %(message)s")

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if settings.loki_url and not any(isinstance(handler, LokiHandler) for handler in logger.handlers):
        loki_handler = LokiHandler(
            url=settings.loki_url,
            tags={
                "app": settings.app_name,
                "env": settings.environment,
                "service": settings.service_name,
            },
            version="1",
        )
        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    logger.propagate = False
    _configured_logger = logger
    return logger


def get_logger(module_name: str) -> logging.Logger:
    logger = configure_logging()
    return logger.getChild(module_name)
