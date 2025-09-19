from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class IntentRequest(BaseModel):
    text: str
    actor_email: Optional[EmailStr] = None

class TimeWindow(BaseModel):
    start: datetime
    end: datetime

class IntentEntities(BaseModel):
    participants: List[EmailStr] = Field(default_factory=list)
    duration_min: int = 30
    window: Optional[TimeWindow] = None
    location: str = "Google Meet"

class IntentResponse(BaseModel):
    intent: str = "schedule_meeting"
    entities: IntentEntities
    proposed_slots: List[datetime] = Field(default_factory=list)
    status: str = "slots_proposed"

class EventCreate(BaseModel):
    title: str
    attendees: List[EmailStr]
    start: datetime
    end: datetime
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class LogEntry(BaseModel):
    timestamp: datetime
    actor: str
    action: str
    payload: dict
    status: str
