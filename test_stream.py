import os
import sys
import time
import socket
import urllib.parse
from app.services.tunnel_service import tunnel_service

print("1. Ensuring Cloudflare TCP Tunnel is running...", flush=True)
tunnel_service.ensure_tunnel_running()
status = tunnel_service.get_status()
print(f"Tunnel status: {status}", flush=True)

print("2. Testing TCP port 8554 socket connection...", flush=True)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3.0)
try:
    res = s.connect_ex(("127.0.0.1", 8554))
    print(f"Socket connect result: {res} (0 means connected successfully)", flush=True)
except Exception as e:
    print(f"Socket connection error: {e}", flush=True)
finally:
    s.close()

print("3. Testing RTSP OPTIONS / DESCRIBE handshake via raw socket...", flush=True)
try:
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.settimeout(5.0)
    s2.connect(("127.0.0.1", 8554))
    req = "OPTIONS rtsp://127.0.0.1:8554/live/1/1/avm RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: VideoIntelligence/1.0\r\n\r\n"
    s2.sendall(req.encode())
    resp = s2.recv(1024)
    print("RTSP Handshake Response:", resp.decode(errors="ignore"), flush=True)
    s2.close()
except Exception as e:
    print(f"RTSP Raw Socket error: {e}", flush=True)

print("4. Testing OpenCV capture on RTSP channels...", flush=True)
try:
    import cv2
    channels = [
        "rtsp://admin:Gt%40102020@127.0.0.1:8554/live/1/1/avm",
        "rtsp://admin:Gt%40102020@127.0.0.1:8554/live/1/2/avm",
    ]
    for ch_url in channels:
        print(f"Trying {ch_url}...", flush=True)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;4000000"
        cap = cv2.VideoCapture(ch_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f">>> SUCCESS: Live frame captured ({w}x{h}) from {ch_url}", flush=True)
                snapshot_file = os.path.abspath("live_camera_snapshot.jpg")
                cv2.imwrite(snapshot_file, frame)
                print(f">>> Saved image to: {snapshot_file}", flush=True)
                cap.release()
                break
            else:
                print(f"cap.isOpened() True, but frame read was False for {ch_url}", flush=True)
            cap.release()
        else:
            print(f"Failed to open {ch_url}", flush=True)
except Exception as e:
    print(f"OpenCV test error: {e}", flush=True)

print("Test complete.", flush=True)
