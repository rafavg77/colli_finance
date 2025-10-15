from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.audit import AuditCRUD


async def register_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource: str,
    details: dict[str, Any] | None = None,
) -> None:
    await AuditCRUD.create(db, user_id=user_id, action=action, resource=resource, details=details)
