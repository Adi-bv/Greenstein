from sqlalchemy import Column, Integer, String, DateTime, func
from .base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
