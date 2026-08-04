import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base
import enum

class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"

class EventSeverity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=True)
    video_file = Column(String, nullable=True)
    status = Column(String, default=CameraStatus.ONLINE.value)
    fps = Column(Integer, default=30)
    zones = Column(JSON, default=list) # Polygons for line crossing & restricted zones
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")
    captions = relationship("Caption", back_populates="camera", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="camera", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, nullable=False, index=True) # fall, loitering, line_crossing, fire, smoke, helmet_violation, accident, crowd
    severity = Column(String, default=EventSeverity.INFO.value, index=True)
    description = Column(Text, nullable=False)
    object_class = Column(String, nullable=True) # person, vehicle, forklift, helmet, bag, fire, smoke
    object_count = Column(Integer, default=1)
    bbox = Column(JSON, nullable=True) # [x1, y1, x2, y2]
    confidence = Column(Float, default=0.9)
    thumbnail_url = Column(String, nullable=True)
    clip_url = Column(String, nullable=True)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("Camera", back_populates="events")
    alerts = relationship("Alert", back_populates="event", cascade="all, delete-orphan")

class Caption(Base):
    __tablename__ = "captions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration_start = Column(Float, default=0.0)
    duration_end = Column(Float, default=10.0)
    raw_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("Camera", back_populates="captions")

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=True)
    timeframe_type = Column(String, nullable=False) # 1m, 1h, 24h, custom
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    summary_text = Column(Text, nullable=False)
    metrics_json = Column(JSON, default=dict) # e.g. {"people_count": 142, "vehicles": 38, "safety_violations": 2}
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("Camera", back_populates="summaries")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String, default=EventSeverity.HIGH.value)
    status = Column(String, default="triggered") # triggered, acknowledged, resolved
    message = Column(Text, nullable=False)
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="alerts")
