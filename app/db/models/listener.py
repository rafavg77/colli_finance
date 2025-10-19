from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ListenerCred(Base):
    __tablename__ = "listener_cred"
    __table_args__ = (UniqueConstraint("user_id", name="uq_listener_cred_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="disabled")
    google_credentials = Column(JSONB, nullable=True)
    google_access_token = Column(JSONB, nullable=True)

    user = relationship("User", backref="listener_credential", uselist=False)
    configs = relationship("ListenerConfig", back_populates="credential", cascade="all, delete-orphan")


class ListenerTemplate(Base):
    __tablename__ = "listener_templates"
    __table_args__ = (UniqueConstraint("bank_id", "template_code", name="uq_listener_templates_bank_code"),)

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False, index=True)
    template_code = Column(String(100), nullable=False)
    email_sender = Column(String(255), nullable=False)
    subject_pattern = Column(Text, nullable=True)
    amount_pattern = Column(Text, nullable=True)
    description_pattern = Column(Text, nullable=True)
    date_pattern = Column(Text, nullable=True)
    time_pattern = Column(Text, nullable=True)
    transaction_type = Column(String(50), nullable=False)
    template_metadata = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    bank = relationship("Bank", backref="listener_templates")
    configs = relationship("ListenerConfig", back_populates="template", cascade="all, delete-orphan")


class ListenerConfig(Base):
    __tablename__ = "listener_config"
    __table_args__ = (UniqueConstraint("listener_cred_id", "listener_template_id", "card_id", name="uq_listener_config_binding"),)

    id = Column(Integer, primary_key=True, index=True)
    listener_cred_id = Column(Integer, ForeignKey("listener_cred.id", ondelete="CASCADE"), nullable=False)
    listener_template_id = Column(Integer, ForeignKey("listener_templates.id", ondelete="CASCADE"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)

    credential = relationship("ListenerCred", back_populates="configs")
    template = relationship("ListenerTemplate", back_populates="configs")
    card = relationship("Card", backref="listener_configs")
