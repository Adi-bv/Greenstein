from sqlalchemy import Column, Integer, Text, DateTime, func
from sqlalchemy.types import JSON
from sqlalchemy.ext.mutable import MutableList

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)

    # Use MutableList to ensure changes to the list are tracked by SQLAlchemy
    interests = Column(MutableList.as_mutable(JSON), default=lambda: [])  

    # Storing a summary of past interactions as text
    interaction_summary = Column(Text, nullable=True, default='')

    # Add created_at and updated_at timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
