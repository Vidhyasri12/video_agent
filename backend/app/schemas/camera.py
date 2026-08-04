from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class CameraBase(BaseModel):
    name: str
    location: str
    rtsp_url: Optional[str] = None
    video_file: Optional[str] = None
    status: Optional[str] = "online"
    fps: Optional[int] = 30
    zones: Optional[List[Any]] = []

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
