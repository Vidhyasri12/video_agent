from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    event_id: str
    alert_type: str
    severity: str = "high"
    status: str = "triggered"
    message: str
    notification_sent: bool = False

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
