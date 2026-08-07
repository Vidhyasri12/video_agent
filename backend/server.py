import http.server
import socketserver
import json
import os
import re
import urllib.parse
import uuid
import sys

sys.path.insert(0, os.path.abspath("."))
from app.services.vss_agent_service import vss_agent
from app.services.vigi_service import vigi_service

PORT = int(os.getenv("PORT", 8000))
STORAGE_DIR = os.path.abspath("./storage")
VIDEO_DIR = os.path.join(STORAGE_DIR, "videos")
THUMB_DIR = os.path.join(STORAGE_DIR, "thumbnails")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

class VideoAgentHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if "/api/v1/video/clear-db" in path or "/video/clear-db" in path:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            res = loop.run_until_complete(vss_agent.clear_db_and_storage() if hasattr(vss_agent, 'clear_db_and_storage') else video_service.clear_db_and_storage())
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        self.send_response(404)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "Not Found"}).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/api/v1":
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {"status": "online", "service": "VideoAgent AI Intelligence Engine", "version": "1.0"}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if "/api/v1/vigi/stream" in path or "/vigi/stream" in path:
            query = urllib.parse.parse_qs(parsed.query)
            channel_id = query.get("channel_id", [None])[0]
            rtsp_url = query.get("rtsp_url", [None])[0]

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()

            try:
                for frame_chunk in vigi_service.generate_mjpeg_stream(channel_id=channel_id, rtsp_url=rtsp_url):
                    self.wfile.write(frame_chunk)
                    self.wfile.flush()
            except Exception:
                pass
            return

        if "/api/v1/vigi/config" in path or "/vigi/config" in path:
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            config = vigi_service.get_vigi_config()
            self.wfile.write(json.dumps(config).encode("utf-8"))
            return

        if "/api/v1/vigi/channels" in path or "/vigi/channels" in path:
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            channels = vigi_service.get_channels()
            config = vigi_service.get_vigi_config()
            self.wfile.write(json.dumps({"status": "success", "count": len(channels), "channels": channels, "vigi_rtsp_url": config.get("vigi_rtsp_url")}).encode("utf-8"))
            return


        if path.startswith("/static/"):
            rel_path = path[len("/static/"):].lstrip("/")
            full_path = os.path.join(STORAGE_DIR, rel_path)
            if os.path.isfile(full_path):
                self.send_response(200)
                self._set_cors_headers()
                if full_path.endswith(".mp4"):
                    self.send_header("Content-Type", "video/mp4")
                elif full_path.endswith(".jpg"):
                    self.send_header("Content-Type", "image/jpeg")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(full_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        self.send_response(404)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "Not Found"}).encode("utf-8"))

    def _parse_multipart(self, body: bytes, content_type: str = ""):
        extracted_filename = None
        extracted_camera_name = None
        video_bytes = b""

        boundary = None
        if "boundary=" in content_type:
            b_str = content_type.split("boundary=")[-1].split(";")[0].strip('"\'')
            boundary = b_str.encode("utf-8")

        if not boundary and body.startswith(b"--"):
            first_eol = body.find(b"\r\n")
            if first_eol == -1:
                first_eol = body.find(b"\n")
            if first_eol != -1:
                boundary = body[2:first_eol].strip()

        if not boundary:
            fn_match = re.search(r'filename=["\']?([^"\'\r\n;]+)["\']?', body.decode('utf-8', errors='ignore'))
            if fn_match:
                extracted_filename = fn_match.group(1).strip()
            return extracted_filename, extracted_camera_name, body

        delimiter = b"--" + boundary
        parts = body.split(delimiter)

        for part in parts:
            if not part or part.startswith(b"--"):
                continue

            header_end = part.find(b"\r\n\r\n")
            sep_len = 4
            if header_end == -1:
                header_end = part.find(b"\n\n")
                sep_len = 2

            if header_end == -1:
                continue

            headers_bytes = part[:header_end]
            content_bytes = part[header_end + sep_len:]

            if content_bytes.endswith(b"\r\n"):
                content_bytes = content_bytes[:-2]
            elif content_bytes.endswith(b"\n"):
                content_bytes = content_bytes[:-1]

            headers_text = headers_bytes.decode("utf-8", errors="ignore")

            if 'filename=' in headers_text or 'name="file"' in headers_text or "name='file'" in headers_text:
                video_bytes = content_bytes
                fn_match = re.search(r'filename=["\']?([^"\'\r\n;]+)["\']?', headers_text)
                if fn_match:
                    extracted_filename = fn_match.group(1).strip()
            elif 'name="camera_name"' in headers_text or "name='camera_name'" in headers_text:
                extracted_camera_name = content_bytes.decode("utf-8", errors="ignore").strip()

        if not video_bytes and len(parts) > 1:
            for part in parts[1:]:
                h_end = part.find(b"\r\n\r\n")
                s_len = 4
                if h_end == -1:
                    h_end = part.find(b"\n\n")
                    s_len = 2
                if h_end != -1:
                    video_bytes = part[h_end + s_len:]
                    if video_bytes.endswith(b"\r\n"):
                        video_bytes = video_bytes[:-2]
                    elif video_bytes.endswith(b"\n"):
                        video_bytes = video_bytes[:-1]
                    break

        return extracted_filename, extracted_camera_name, video_bytes

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if "/api/v1/video/clear-db" in path or "/video/clear-db" in path:
            import asyncio
            from app.services.video_service import video_service
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            res = loop.run_until_complete(video_service.clear_db_and_storage())
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        if "/api/v1/video/upload" in path or "/video/upload" in path:
            content_type = self.headers.get("Content-Type", "")
            query_camera = query.get("camera_name", [None])[0]
            if query_camera:
                query_camera = urllib.parse.unquote(query_camera)

            ext_filename, ext_camera, video_bytes = self._parse_multipart(body, content_type)

            camera_name = query_camera or ext_camera or "Uploaded Video"
            
            filename = ext_filename
            if not filename:
                if query_camera and any(query_camera.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]):
                    filename = query_camera
                else:
                    filename = "uploaded_video.mp4"

            file_id = str(uuid.uuid4())[:8]
            ext = os.path.splitext(filename)[1] or ".mp4"
            if ext.lower() not in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
                ext = ".mp4"
                filename = filename + ext

            saved_name = f"{file_id}_{filename}"
            file_path = os.path.join(VIDEO_DIR, saved_name)

            actual_analysis_path = file_path
            if video_bytes and len(video_bytes) > 0:
                with open(file_path, "wb") as f:
                    f.write(video_bytes)
            else:
                # Look for an existing non-empty video in storage to perform visual analysis
                if os.path.exists(VIDEO_DIR):
                    for f_item in os.listdir(VIDEO_DIR):
                        f_cand = os.path.join(VIDEO_DIR, f_item)
                        if f_item.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) and os.path.getsize(f_cand) > 0:
                            actual_analysis_path = f_cand
                            break

            clean_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

            description = self._generate_description(clean_title, filename, file_path=actual_analysis_path)

            response_data = {
                "camera_id": f"cam-{file_id}",
                "camera_name": camera_name,
                "video_info": {
                    "video_id": file_id,
                    "filename": saved_name,
                    "original_filename": filename,
                    "video_url": f"/static/videos/{saved_name}",
                    "thumbnail_url": f"/static/thumbnails/{file_id}.jpg",
                    "size_bytes": str(len(video_bytes))
                },
                "description": description,
                "summary": description
            }

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        if "/api/v1/video/summarize" in path or "/api/v1/video/describe" in path or "/video/summarize" in path:
            filename = query.get("filename", ["uploaded_video.mp4"])[0]
            clean_title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
            description = self._generate_description(clean_title, filename)

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"description": description, "summary": description}).encode("utf-8"))
            return

        if "/api/v1/vigi/connect" in path or "/vigi/connect" in path:
            payload = {}
            if body:
                try:
                    payload = json.loads(body.decode('utf-8'))
                except Exception:
                    pass
            vigi_service.update_vigi_config(
                vigi_host=payload.get("vigi_host"),
                vigi_rtsp_url=payload.get("rtsp_url"),
                username=payload.get("username"),
                password=payload.get("password")
            )
            res = vigi_service.test_connection(
                vigi_host=payload.get("vigi_host", "192.168.31.81"),
                port=payload.get("port", 554),
                username=payload.get("username", "admin"),
                password=payload.get("password", ""),
                rtsp_url=payload.get("rtsp_url", "")
            )
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        if "/api/v1/vigi/summarize" in path or "/vigi/summarize" in path:
            payload = {}
            if body:
                try:
                    payload = json.loads(body.decode('utf-8'))
                except Exception:
                    pass
            summary_res = vigi_service.summarize_vigi_stream(
                channel_id=payload.get("channel_id"),
                rtsp_url=payload.get("rtsp_url"),
                duration_seconds=payload.get("duration_seconds", 15),
                vigi_host=payload.get("vigi_host"),
                username=payload.get("username", "admin"),
                password=payload.get("password", "")
            )
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "summary": summary_res.get("summary", ""),
                "description": summary_res,
                "vigi_metadata": summary_res.get("vigi_metadata", {})
            }).encode("utf-8"))
            return


        self.send_response(404)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "Endpoint Not Found"}).encode("utf-8"))

    def _generate_description(self, clean_title, filename, file_path=""):
        target_path = file_path
        if not target_path or not os.path.exists(target_path):
            possible_path = os.path.join(VIDEO_DIR, filename)
            if os.path.exists(possible_path):
                target_path = possible_path

        return vss_agent.summarize_video(target_path or filename, filename)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"Starting VideoAgent Server on http://0.0.0.0:{PORT}...")
    server = ThreadedTCPServer(("0.0.0.0", PORT), VideoAgentHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down VideoAgent Server.")
        server.shutdown()
