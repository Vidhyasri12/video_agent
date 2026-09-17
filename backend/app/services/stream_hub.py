"""
High-Performance RTSP Stream Hub & Frame Broadcaster.
Solves NVR '429 Stream Up To Limit' error by multiplexing multiple client viewers
into a single shared RTSP capture connection per channel with auto-fallback to sub-stream.
Ensures steady 25 FPS stream delivery so browser never sees black screens or dropped connections.
"""

import os
import time
import cv2
import numpy as np
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Generator

from app.services.tunnel_service import tunnel_service

logger = logging.getLogger(__name__)

def format_rtsp_url(rtsp_url: str) -> str:
    if not rtsp_url or not rtsp_url.startswith("rtsp://"):
        return rtsp_url
    import urllib.parse
    try:
        prefix, rest = rtsp_url.split("rtsp://", 1)
        if "@" not in rest:
            return rtsp_url
        user_info, host_path = rest.rsplit("@", 1)
        if ":" in user_info:
            user, password = user_info.split(":", 1)
            unquoted_pass = urllib.parse.unquote(password)
            quoted_pass = urllib.parse.quote(unquoted_pass, safe="")
            unquoted_user = urllib.parse.unquote(user)
            quoted_user = urllib.parse.quote(unquoted_user, safe="")
            return f"rtsp://{quoted_user}:{quoted_pass}@{host_path}"
    except Exception:
        pass
    return rtsp_url


class ChannelStreamWorker:
    """
    Dedicated worker thread capturing frames from a single camera channel.
    Distributes encoded JPEG frames to any number of HTTP subscribers at steady 25 FPS.
    """
    def __init__(self, channel_id: str, channel_name: str, primary_url: str, sub_url: Optional[str] = None):
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.primary_url = primary_url
        self.sub_url = sub_url
        self.latest_jpeg: Optional[bytes] = None
        self.last_frame_time = 0.0
        self.subscribers = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.is_live = False
        self.resolution = "2560x1440"

    def add_subscriber(self):
        with self.lock:
            self.subscribers += 1
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._capture_loop, daemon=True, name=f"StreamWorker-{self.channel_id}")
                self.thread.start()

    def remove_subscriber(self):
        with self.lock:
            self.subscribers = max(0, self.subscribers - 1)

    def generate_status_frame(self, message: str, is_warning: bool = False) -> bytes:
        w, h = 1024, 576
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (11, 16, 29) # Dark slate background
        cv2.rectangle(frame, (0, 0), (w, 36), (15, 23, 42), -1)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.circle(frame, (18, 18), 5, (0, 150, 255) if is_warning else (0, 220, 255), -1)
        osd_text = f"TP-LINK VIGI  |  {self.channel_name}  |  {now_str}"
        cv2.putText(frame, osd_text, (32, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        cv2.putText(frame, message, (w // 2 - int(len(message) * 6.5), h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 255) if not is_warning else (0, 150, 255), 2, cv2.LINE_AA)
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        return buffer.tobytes()

    def _capture_loop(self):
        logger.info(f"[{self.channel_id}] Starting stream capture worker for '{self.channel_name}'")
        self.latest_jpeg = self.generate_status_frame("CONNECTING TO CAMERA RTSP FEED...")
        idle_start = None

        urls_to_try = [self.primary_url]
        if self.sub_url and self.sub_url != self.primary_url:
            urls_to_try.append(self.sub_url)
        elif "/stream1" in self.primary_url:
            urls_to_try.append(self.primary_url.replace("/stream1", "/stream2"))
        elif "/live/" in self.primary_url:
            path_parts = self.primary_url.rsplit("/", 3)
            if len(path_parts) == 4 and path_parts[-2] == "1" and path_parts[-1] == "avm":
                path_parts[-2] = "2"
                urls_to_try.append("/".join(path_parts))

        cap = None
        current_url_idx = 0

        while self.running:
            # Check for zero subscribers with 15s idle grace period
            with self.lock:
                if self.subscribers == 0:
                    if idle_start is None:
                        idle_start = time.time()
                    elif time.time() - idle_start > 15.0:
                        logger.info(f"[{self.channel_id}] Releasing idle camera stream to free NVR session")
                        break
                else:
                    idle_start = None

            # Open or reconnect VideoCapture if needed
            if cap is None or not cap.isOpened():
                if "127.0.0.1" in self.primary_url or "localhost" in self.primary_url or "8554" in self.primary_url:
                    tunnel_service.ensure_tunnel_running()

                target_url = urls_to_try[current_url_idx % len(urls_to_try)]
                formatted_url = format_rtsp_url(target_url)

                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;2000000|buffer_size;102400|max_delay;500000"
                try:
                    temp_cap = cv2.VideoCapture(formatted_url, cv2.CAP_FFMPEG)
                    temp_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    if temp_cap.isOpened():
                        ret, frame = temp_cap.read()
                        if ret and frame is not None:
                            cap = temp_cap
                            self.is_live = True
                            h, w = frame.shape[:2]
                            self.resolution = f"{w}x{h}"
                            logger.info(f"[{self.channel_id}] Connected to '{target_url}' ({self.resolution})")
                        else:
                            temp_cap.release()
                            current_url_idx += 1
                            time.sleep(0.5)
                            continue
                    else:
                        current_url_idx += 1
                        self.latest_jpeg = self.generate_status_frame("CONNECTING TO LIVE RTSP STREAM...", is_warning=False)
                        time.sleep(0.8)
                        continue
                except Exception as e:
                    logger.warning(f"[{self.channel_id}] Connect error: {e}")
                    current_url_idx += 1
                    time.sleep(0.8)
                    continue

            # Read frame continuously
            try:
                ret, frame = cap.read()
                if not ret or frame is None:
                    cap.release()
                    cap = None
                    self.is_live = False
                    current_url_idx += 1
                    time.sleep(0.3)
                    continue

                h, w = frame.shape[:2]
                self.resolution = f"{w}x{h}"

                # Scale down for fast, smooth web streaming
                if w > 1280:
                    target_w, target_h = 1024, int(1024 * (h / w))
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
                    h, w = target_h, target_w

                # OSD Header
                cv2.rectangle(frame, (0, 0), (w, 32), (0, 0, 0), -1)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.circle(frame, (16, 16), 5, (0, 255, 0), -1)
                osd_text = f"TP-LINK VIGI (LIVE RTSP)  |  {self.channel_name}  |  {now_str}"
                cv2.putText(frame, osd_text, (28, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

                _, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
                self.latest_jpeg = buf.tobytes()
                self.last_frame_time = time.time()
                time.sleep(0.033) # 30 FPS pace
            except Exception as e:
                logger.warning(f"[{self.channel_id}] Read error: {e}")
                if cap:
                    cap.release()
                cap = None
                time.sleep(0.3)

        if cap:
            try:
                cap.release()
            except Exception:
                pass
        self.running = False
        self.is_live = False
        logger.info(f"[{self.channel_id}] Stream capture worker stopped")


class StreamHub:
    """Singleton managing channel stream workers."""
    def __init__(self):
        self.workers: Dict[str, ChannelStreamWorker] = {}
        self.lock = threading.Lock()

    def get_or_create_worker(
        self,
        channel_id: str,
        channel_name: str,
        primary_url: str,
        sub_url: Optional[str] = None
    ) -> ChannelStreamWorker:
        with self.lock:
            if channel_id not in self.workers:
                self.workers[channel_id] = ChannelStreamWorker(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    primary_url=primary_url,
                    sub_url=sub_url
                )
            else:
                worker = self.workers[channel_id]
                worker.primary_url = primary_url
                worker.sub_url = sub_url
                worker.channel_name = channel_name
            return self.workers[channel_id]

    def is_channel_live(self, channel_id: str) -> bool:
        with self.lock:
            worker = self.workers.get(channel_id)
            return bool(worker and worker.is_live and (time.time() - worker.last_frame_time < 3.0))

    async def generate_mjpeg_stream(
        self,
        channel_id: str,
        channel_name: str,
        primary_url: str,
        sub_url: Optional[str] = None
    ):
        worker = self.get_or_create_worker(channel_id, channel_name, primary_url, sub_url)
        worker.add_subscriber()
        import asyncio

        try:
            while True:
                jpeg = worker.latest_jpeg or worker.generate_status_frame("CONNECTING TO LIVE STREAM...")
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
                await asyncio.sleep(0.04) # Steady 25 FPS non-blocking delivery
        finally:
            worker.remove_subscriber()

stream_hub = StreamHub()
