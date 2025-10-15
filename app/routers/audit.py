from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.audit import AuditCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.audit import AuditResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditResponse])
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = await AuditCRUD.list_logs(db, user_id=current_user.id)
    return logs
