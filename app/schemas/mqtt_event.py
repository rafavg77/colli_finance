from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class MqttTransactionData(BaseModel):
    """Individual transaction data within MQTT event"""
    amount: str | None = None
    description: str
    income: str = "0.00"
    expense: str = "0.00"
    type: str = Field(..., pattern="^(income|expense)$")
    operation_date: date
    
    @field_validator('income', 'expense', mode='before')
    @classmethod
    def empty_string_to_zero(cls, v):
        if v == "" or v is None:
            return "0.00"
        return v


class MqttCardData(BaseModel):
    """Card data with transactions within MQTT event"""
    id_tarjeta: int
    transaction: list[MqttTransactionData]


class MqttEmailEvent(BaseModel):
    """MQTT event payload schema for email listener topic"""
    id_usuario: int
    correo_usuario: str
    tarjetas: list[MqttCardData]
