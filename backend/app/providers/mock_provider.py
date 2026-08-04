"""
Mock / Demo Camera Provider Implementation.
Conforms to Production Requirement #4 & #13.
Isolated simulation provider for offline development and testing.
Only activated when ENABLE_MOCK_PROVIDER=True.
"""
import os
import time
import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

from app.providers.base_provider import CameraProvider
from app.services.vss_agent_service import vss_agent

logger = logging.getLogger(__name__)

MOCK_CHANNELS = [
    {
        "channel_id": "mock-cam-01",
        "name": "Simulated Warehouse Camera",
        "model": "VideoAgent Mock VMS v1.0",
        "ip_address": "127.0.0.1",
        "port": 554,
        "status": "online_simulated",
        "rtsp_url": "rtsp://mock:mock@127.0.0.1:554/stream1",
        "sample_video": "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4"
    }
]

class MockProvider(CameraProvider):
    """Mock Provider serving local video files for dev/test testing."""

    def __init__(self, storage_dir: str = "./storage"):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        possible_dirs = [
            os.path.abspath(os.path.join(storage_dir, "videos")),
            os.path.abspath(os.path.join(base_dir, "../../../storage/videos")),
            os.path.abspath(os.path.join(base_dir, "../../storage/videos")),
            os.path.abspath("./storage/videos")
        ]
        found_dir = None
        for p in possible_dirs:
            if os.path.exists(p) and os.path.isdir(p):
                found_dir = p
                break
        if not found_dir:
            found_dir = os.path.abspath(os.path.join(storage_dir, "videos"))
            os.makedirs(found_dir, exist_ok=True)
        self.video_dir = found_dir

    @property
    def provider_type(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock / Development Provider (Simulated)"

    def detect_capabilities(self) -> Dict[str, bool]:
        return {
            "supports_rtsp": True,
            "supports_onvif": False,
            "supports_openapi": False,
            "supports_cloud_api": False,
            "supports_webhooks": False,
            "supports_ptz": False
        }

    def test_connection(self, host: Optional[str] = None, port: int = 554, username: str = "", password: str = "", rtsp_url: str = "") -> Dict[str, Any]:
        return {
            "status": "online_simulated",
            "provider": self.provider_type,
            "message": "Connected to Mock Stream Simulator.",
            "resolution": "1920x1080",
            "timestamp": datetime.now().isoformat()
        }

    def get_channels(self) -> List[Dict[str, Any]]:
        return MOCK_CHANNELS

    def discover_network_devices(self) -> List[Dict[str, Any]]:
        return [{"ip": "127.0.0.1", "vendor": "VideoAgent Mock Provider", "protocol": "Simulated", "status": "online"}]

    def generate_mjpeg_stream(self, channel_id: Optional[str] = None, rtsp_url: Optional[str] = None) -> Generator[bytes, None, None]:
        sample_path = os.path.join(self.video_dir, "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4")
        cap = cv2.VideoCapture(sample_path) if cv2 is not None and os.path.exists(sample_path) else None

        if cap is None or not cap.isOpened():
            black_frame = np.zeros((720, 1280, 3), dtype=np.uint8) if np is not None else None
            while True:
                if black_frame is not None and cv2 is not None:
                    _, buffer = cv2.imencode('.jpg', black_frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.04)
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.04)
                        continue

                if frame is not None and cv2 is not None:
                    h, w = frame.shape[:2]
                    cv2.rectangle(frame, (0, 0), (w, 36), (50, 50, 50), -1)
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, f"MOCK SIMULATOR FEED  |  {now_str}", (20, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.04)
        finally:
            cap.release()

    def summarize_stream(self, channel_id: Optional[str] = None, rtsp_url: Optional[str] = None, duration_seconds: int = 15, host: Optional[str] = None, username: str = "", password: str = "") -> Dict[str, Any]:
        sample_path = os.path.join(self.video_dir, "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4")
        res = vss_agent.summarize_video(sample_path, "Simulated Camera")
        res["title"] = "Mock Provider Video Summary"
        res["vigi_metadata"] = {"channel_id": "mock-01", "is_live": False, "protocol": "Mock Stream"}
        return res

    def get_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy_simulated",
            "provider": self.provider_type,
            "display_name": self.display_name,
            "capabilities": self.detect_capabilities(),
            "timestamp": datetime.now().isoformat()
        }
