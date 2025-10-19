from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    cards = relationship("Card", back_populates="bank")
