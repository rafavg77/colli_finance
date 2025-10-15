from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.user import UserCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.audit import register_audit
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await UserCRUD.get_by_phone(db, phone=payload.phone)
    if existing:
        logger.warning(
            "User registration rejected",
            extra={"details": {"event": "user_register_rejected", "extra": {"phone_suffix": payload.phone[-4:]}}},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El teléfono ya está registrado")
    user = await UserCRUD.create(
        db,
        name=payload.name,
        phone=payload.phone,
        telegram_id=payload.telegram_id,
        email=payload.email,
        password=payload.password,
    )
    await register_audit(db, user_id=user.id, action="create", resource="user", details={"user_id": user.id})
    logger.info(
        "User registered via users endpoint",
        extra={"details": {"event": "user_register", "extra": {"user_id": user.id, "phone_suffix": payload.phone[-4:]}}},
    )
    return user


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    logger.debug(
        "Profile retrieved",
        extra={"details": {"event": "user_profile_get", "extra": {"user_id": current_user.id}}},
    )
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await UserCRUD.update(db, current_user, **payload.dict(exclude_unset=True))
    await register_audit(db, user_id=user.id, action="update", resource="user", details={"user_id": user.id})
    logger.info(
        "User profile updated",
        extra={"details": {"event": "user_profile_update", "extra": {"user_id": user.id}}},
    )
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserCRUD.delete(db, current_user)
    await register_audit(db, user_id=current_user.id, action="delete", resource="user", details={"user_id": current_user.id})
    logger.warning(
        "User profile deleted",
        extra={"details": {"event": "user_profile_delete", "extra": {"user_id": current_user.id}}},
    )
    return None
