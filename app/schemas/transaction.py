from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class TransactionBase(BaseModel):
    card_id: int
    description: str
    category_id: int | None = None
    income: Decimal = Decimal("0.00")
    expenses: Decimal = Decimal("0.00")
    executed: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    card_id: int | None = None
    description: str | None = None
    category_id: int | None = None
    income: Decimal | None = None
    expenses: Decimal | None = None
    executed: bool | None = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    transfer_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
