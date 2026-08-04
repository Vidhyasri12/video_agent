from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SummaryRequest(BaseModel):
    camera_id: Optional[str] = None
    timeframe_type: str = "1h" # 1m, 1h, 24h, custom
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class SummaryResponse(BaseModel):
    id: str
    camera_id: Optional[str]
    timeframe_type: str
    start_time: datetime
    end_time: datetime
    summary_text: str
    metrics_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
