from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class EventBase(BaseModel):
    camera_id: str
    timestamp: Optional[datetime] = None
    event_type: str
    severity: str = "info"
    description: str
    object_class: Optional[str] = None
    object_count: int = 1
    bbox: Optional[Any] = None
    confidence: float = 0.9
    thumbnail_url: Optional[str] = None
    clip_url: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class SearchQuery(BaseModel):
    query: str
    camera_id: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    use_vector_search: bool = True
    limit: int = 20
