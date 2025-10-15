from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.habit import HabitCreate
from app.services.audit import register_audit

router = APIRouter(prefix="/habitos", tags=["habitos"])


@router.post("/registrar")
async def registrar_habito(
    payload: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await register_audit(
        db,
        user_id=current_user.id,
        action="habit_register",
        resource="habit",
        details={"nombre": payload.nombre, "descripcion": payload.descripcion},
    )
    return {"mensaje": "Hábito registrado", "habito": payload.dict()}
