from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class InteractionBase(BaseModel):
    hcp_name: str
    interaction_date: date
    interaction_time: Optional[str] = None
    interaction_type: Optional[str] = None
    attendees: Optional[str] = None
    summary: Optional[str] = None
    key_discussion_points: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_actions: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[str] = None
    interaction_type: Optional[str] = None
    attendees: Optional[str] = None
    summary: Optional[str] = None
    key_discussion_points: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_actions: Optional[str] = None

class Interaction(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
