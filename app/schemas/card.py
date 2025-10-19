from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from app.schemas.bank import BankSummary


class CardBase(BaseModel):
    bank_id: int
    type: Literal["debit", "credit"]
    card_name: str
    alias: str | None = None
    billing_cycle_day: int | None = Field(None, ge=1, le=31)
    payment_due_day: int | None = Field(None, ge=1, le=31)
    grace_days: int | None = Field(None, ge=0, le=60)


class CardCreate(CardBase):
    @model_validator(mode="after")
    def _validate_credit_fields(self):
        if self.type == "credit":
            if self.billing_cycle_day is None or self.payment_due_day is None:
                raise ValueError("Las tarjetas de crédito requieren billing_cycle_day y payment_due_day")
        return self


class CardUpdate(BaseModel):
    bank_id: int | None = None
    type: Literal["debit", "credit"] | None = None
    card_name: str | None = None
    alias: str | None = None
    billing_cycle_day: int | None = Field(default=None, ge=1, le=31)
    payment_due_day: int | None = Field(default=None, ge=1, le=31)
    grace_days: int | None = Field(default=None, ge=0, le=60)


class CardResponse(CardBase):
    id: int
    user_id: int
    bank_name: str
    bank: BankSummary | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
