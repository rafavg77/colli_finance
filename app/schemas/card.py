from datetime import datetime
from pydantic import BaseModel


class CardBase(BaseModel):
    bank_name: str
    type: str
    card_name: str
    alias: str | None = None


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    bank_name: str | None = None
    type: str | None = None
    card_name: str | None = None
    alias: str | None = None


class CardResponse(CardBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
