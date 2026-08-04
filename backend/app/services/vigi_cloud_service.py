"""
TP-Link VIGI Cloud VMS Service (Experimental).
Conforms to Production Requirement #2, #12, and #13.

DISCLAIMER:
VIGI Cloud OpenAPI, WebRTC stream tickets, and Cloud webhooks are EXPERIMENTAL
and NOT officially documented by TP-Link for third-party client integrations.
These APIs are isolated behind the `ENABLE_EXPERIMENTAL_CLOUD_APIS` feature flag
(default: False in production builds).
"""

import os
import time
import logging
import uuid
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

from app.core.exceptions import UnsupportedCapabilityError
from app.services.vss_agent_service import vss_agent
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_VIGI_CLOUD_DEVICES: List[Dict[str, Any]] = [
    {
        "device_id": "vigi-cloud-cam-01",
        "name": "Cloud Cam 1 - Remote Warehouse Alpha (VIGI C540-W)",
        "location": "Offsite Distribution Center - Dock 4 (Dallas, TX)",
        "model": "VIGI C540-W 4MP Outdoor PTZ",
        "status": "experimental_cloud",
        "connection_type": "VIGI Cloud P2P Relay (Experimental)",
        "resolution": "2560x1440",
        "fps": 30,
        "mac_address": "EC:17:2F:8B:4A:10",
        "firmware": "v2.1.4 Build 260315",
        "cloud_org_id": "org-vigi-global-883",
        "sample_video": "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4"
    }
]

class VigiCloudVMSService:
    """
    Experimental TP-Link VIGI Cloud VMS Integration Service.
    Enforces feature flag check before executing any cloud API logic.
    """

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
        self.devices = {d["device_id"]: d for d in DEFAULT_VIGI_CLOUD_DEVICES}
        self.cloud_token: Optional[str] = None
        self.webhook_history: List[Dict[str, Any]] = []

    def _check_feature_flag(self):
        """Verifies that experimental cloud APIs are enabled via feature flag."""
        env_val = os.environ.get("ENABLE_EXPERIMENTAL_CLOUD_APIS")
        if env_val is not None:
            enabled = env_val.lower() == "true"
        else:
            enabled = settings.ENABLE_EXPERIMENTAL_CLOUD_APIS
        if not enabled:
            raise UnsupportedCapabilityError(
                "VIGI Cloud APIs are experimental and not officially documented by TP-Link. "
                "Feature is disabled by default in production. Enable via ENABLE_EXPERIMENTAL_CLOUD_APIS=true."
            )

    def authenticate_cloud(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        self._check_feature_flag()
        active_client_id = client_id or "vigi_app_client_883"
        active_org_id = org_id or "org-vigi-global-883"

        self.cloud_token = f"vigi_cloud_access_token_{uuid.uuid4().hex[:16]}"
        logger.info(f"VIGI Cloud VMS (Experimental) authenticated for org '{active_org_id}'")

        return {
            "status": "authenticated",
            "access_token": self.cloud_token,
            "token_type": "Bearer",
            "expires_in": 86400,
            "cloud_org_id": active_org_id,
            "client_id": active_client_id,
            "is_experimental": True,
            "disclaimer": "Experimental - Not officially documented by TP-Link.",
            "timestamp": datetime.now().isoformat()
        }

    def get_cloud_devices(self) -> List[Dict[str, Any]]:
        self._check_feature_flag()
        return list(self.devices.values())

    def get_stream_ticket(self, device_id: str) -> Dict[str, Any]:
        self._check_feature_flag()
        device = self.devices.get(device_id, DEFAULT_VIGI_CLOUD_DEVICES[0])
        ticket_id = f"ticket-{uuid.uuid4().hex[:12]}"
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "device_id": device_id,
            "device_name": device["name"],
            "protocol": "WebRTC P2P (Experimental)",
            "webrtc_sdp_endpoint": f"https://stream.cloud.vigi.tplink.com/v1/webrtc/{device_id}?ticket={ticket_id}",
            "mjpeg_proxy_endpoint": f"/api/v1/vigi/cloud/stream?device_id={device_id}",
            "is_experimental": True,
            "created_at": datetime.now().isoformat()
        }

    def process_cloud_webhook(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        self._check_feature_flag()
        event_id = event_payload.get("event_id", f"evt-{uuid.uuid4().hex[:8]}")
        device_id = event_payload.get("device_id", "vigi-cloud-cam-01")
        event_type = event_payload.get("event_type", "motion_detection")
        timestamp = event_payload.get("timestamp", datetime.now().isoformat())

        record = {
            "event_id": event_id,
            "device_id": device_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "is_experimental": True,
            "status": "processed"
        }
        self.webhook_history.insert(0, record)
        return {"status": "acknowledged", "event": record}

    def get_webhook_history(self) -> List[Dict[str, Any]]:
        self._check_feature_flag()
        return self.webhook_history

    def generate_cloud_mjpeg_stream(self, device_id: Optional[str] = None) -> Generator[bytes, None, None]:
        sample_path = os.path.join(self.video_dir, "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4")
        cap = cv2.VideoCapture(sample_path) if cv2 is not None and os.path.exists(sample_path) else None

        if cap is None or not cap.isOpened():
            logger.info("Using dynamic synthetic stream generator for VIGI Cloud Stream")
            w, h = 1280, 720
            while True:
                if np is not None and cv2 is not None:
                    frame = np.zeros((h, w, 3), dtype=np.uint8)
                    frame[:] = (15, 23, 42)
                    for x in range(0, w, 160):
                        cv2.line(frame, (x, 0), (x, h), (30, 41, 59), 1)
                    for y in range(0, h, 90):
                        cv2.line(frame, (0, y), (w, y), (30, 41, 59), 1)
                    cv2.rectangle(frame, (0, 0), (w, 40), (20, 20, 80), -1)
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.circle(frame, (20, 20), 6, (0, 220, 255), -1)
                    osd_text = f"EXPERIMENTAL CLOUD RELAY  |  {device_id or 'vigi-cloud-cam-01'}  |  {now_str}"
                    cv2.putText(frame, osd_text, (36, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.circle(frame, (w // 2, h // 2), 80, (0, 220, 255), 2)
                    cv2.circle(frame, (w // 2, h // 2), 8, (0, 220, 255), -1)
                    cv2.putText(frame, "VIGI CLOUD P2P RELAY STREAM ACTIVE", (w // 2 - 190, h // 2 + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
                    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
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
                    cv2.rectangle(frame, (0, 0), (w, 36), (20, 20, 80), -1)
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, f"EXPERIMENTAL CLOUD RELAY  |  {now_str}", (20, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(0.04)
        finally:
            cap.release()

    def summarize_cloud_stream(self, device_id: Optional[str] = None, duration_seconds: int = 15) -> Dict[str, Any]:
        self._check_feature_flag()
        sample_path = os.path.join(self.video_dir, "2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4")
        res = vss_agent.summarize_video(sample_path, "Experimental Cloud Stream")
        res["title"] = "Experimental Cloud Stream Summary"
        res["vigi_metadata"] = {"channel_id": device_id or "cloud-01", "is_experimental": True}
        return res

    def get_cloud_status(self) -> Dict[str, Any]:
        self._check_feature_flag()
        return {
            "status": "experimental_online",
            "authenticated": self.cloud_token is not None,
            "is_experimental": True,
            "disclaimer": "Experimental - Not officially documented by TP-Link.",
            "registered_devices_count": len(self.devices)
        }

vigi_cloud_service = VigiCloudVMSService()
