from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None
    exp: datetime | None = None


class LoginRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{11,15}$")
    password: str
