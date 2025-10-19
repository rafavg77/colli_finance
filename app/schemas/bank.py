from datetime import datetime
from pydantic import BaseModel


class BankBase(BaseModel):
    name: str
    slug: str
    display_name: str
    is_active: bool


class BankSummary(BaseModel):
    id: int
    name: str
    slug: str
    display_name: str

    class Config:
        from_attributes = True


class BankResponse(BankBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
