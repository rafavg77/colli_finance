from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import UserCRUD
from app.core.security import verify_password, create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.audit import register_audit
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    phone = form_data.username
    password = form_data.password
    user = await UserCRUD.get_by_phone(db, phone=phone)
    if not user or not verify_password(password, user.password):
        logger.warning(
            "Login failed",
            extra={"details": {"event": "auth_login_failed", "extra": {"phone_suffix": phone[-4:]}}},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = create_access_token({"sub": str(user.id)})
    logger.info(
        "Login successful",
        extra={"details": {"event": "auth_login", "extra": {"user_id": user.id, "phone_suffix": phone[-4:]}}},
    )
    return Token(access_token=token)


@router.post("/login-phone", response_model=Token)
async def login_with_body(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await UserCRUD.get_by_phone(db, phone=payload.phone)
    if not user or not verify_password(payload.password, user.password):
        logger.warning(
            "Login failed",
            extra={"details": {"event": "auth_login_failed", "extra": {"phone_suffix": payload.phone[-4:]}}},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    token = create_access_token({"sub": str(user.id)})
    logger.info(
        "Login successful",
        extra={"details": {"event": "auth_login", "extra": {"user_id": user.id, "phone_suffix": payload.phone[-4:]}}},
    )
    return Token(access_token=token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await UserCRUD.get_by_phone(db, phone=payload.phone)
    if existing:
        logger.warning(
            "User registration rejected",
            extra={"details": {"event": "auth_register_rejected", "extra": {"phone_suffix": payload.phone[-4:]}}},
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
        "User registered",
        extra={"details": {"event": "auth_register", "extra": {"user_id": user.id, "phone_suffix": payload.phone[-4:]}}},
    )
    return user
