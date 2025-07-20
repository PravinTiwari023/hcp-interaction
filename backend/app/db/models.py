from sqlalchemy import create_engine, Column, Integer, String, Text, Date, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from ..core.config import settings

Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False)  # Direct HCP name field
    interaction_date = Column(Date, nullable=False)
    interaction_time = Column(String(10))  # Store time as HH:MM format
    interaction_type = Column(String(100))
    attendees = Column(Text)  # Who attended the meeting
    summary = Column(Text)  # Outcomes/results
    key_discussion_points = Column(Text)  # Topics discussed
    materials_shared = Column(Text)  # Materials provided
    samples_distributed = Column(Text)  # Samples given
    sentiment = Column(String(50))
    follow_up_actions = Column(Text)  # Next steps planned
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
