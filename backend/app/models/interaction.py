from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String, index=True, nullable=False)
    specialty = Column(String, nullable=True)
    product = Column(String, nullable=False)
    interaction_date = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)
    next_action = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
