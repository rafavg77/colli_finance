from datetime import datetime
from pydantic import BaseModel


# ListenerCred schemas
class ListenerCredBase(BaseModel):
    status: str
    google_credentials: dict | None = None
    google_access_token: dict | None = None


class ListenerCredCreate(BaseModel):
    status: str = "disabled"
    google_credentials: dict | None = None
    google_access_token: dict | None = None


class ListenerCredUpdate(BaseModel):
    status: str | None = None
    google_credentials: dict | None = None
    google_access_token: dict | None = None


class ListenerCredResponse(BaseModel):
    id: int
    user_id: int
    status: str
    google_credentials: dict | None
    google_access_token: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ListenerTemplate schemas
class ListenerTemplateBase(BaseModel):
    bank_id: int
    template_code: str
    email_sender: str
    subject_pattern: str | None = None
    amount_pattern: str | None = None
    description_pattern: str | None = None
    date_pattern: str | None = None
    time_pattern: str | None = None
    transaction_type: str
    template_metadata: dict | None = None
    is_active: bool = True


class ListenerTemplateCreate(ListenerTemplateBase):
    pass


class ListenerTemplateUpdate(BaseModel):
    bank_id: int | None = None
    template_code: str | None = None
    email_sender: str | None = None
    subject_pattern: str | None = None
    amount_pattern: str | None = None
    description_pattern: str | None = None
    date_pattern: str | None = None
    time_pattern: str | None = None
    transaction_type: str | None = None
    template_metadata: dict | None = None
    is_active: bool | None = None


class ListenerTemplateResponse(BaseModel):
    id: int
    bank_id: int
    template_code: str
    email_sender: str
    subject_pattern: str | None
    amount_pattern: str | None
    description_pattern: str | None
    date_pattern: str | None
    time_pattern: str | None
    transaction_type: str
    template_metadata: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ListenerConfig schemas
class ListenerConfigBase(BaseModel):
    listener_cred_id: int
    listener_template_id: int
    card_id: int
    is_active: bool = True


class ListenerConfigCreate(ListenerConfigBase):
    pass


class ListenerConfigUpdate(BaseModel):
    listener_cred_id: int | None = None
    listener_template_id: int | None = None
    card_id: int | None = None
    is_active: bool | None = None


class ListenerConfigResponse(BaseModel):
    id: int
    listener_cred_id: int
    listener_template_id: int
    card_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
