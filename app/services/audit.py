from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.audit import AuditCRUD
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def register_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource: str,
    details: dict[str, Any] | None = None,
) -> None:
    await AuditCRUD.create(db, user_id=user_id, action=action, resource=resource, details=details)
    logger.debug(
        "Audit entry recorded",
        extra={
            "details": {
                "event": "audit_register",
                "extra": {"user_id": user_id, "action": action, "resource": resource},
            }
        },
    )
