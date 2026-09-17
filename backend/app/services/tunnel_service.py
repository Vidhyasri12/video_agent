"""
Cloudflare TCP Tunnel Supervisor & Auto-Healer.
Automatically launches, monitors, and auto-restarts the `cloudflared access tcp`
proxy for RTSP camera streaming so connections never get 'Connection refused'.
"""

import os
import sys
import time
import socket
import logging
import subprocess
import threading
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

class TunnelService:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_error: Optional[str] = None
        self._last_probe_error: Optional[str] = None
        self._started_at: Optional[str] = None

    @property
    def hostname(self) -> str:
        return os.environ.get("CLOUDFLARE_HOSTNAME") or getattr(settings, "CLOUDFLARE_HOSTNAME", "nvr1.goodwindco.in")

    @property
    def port(self) -> int:
        return int(os.environ.get("VIGI_VMS_PORT") or getattr(settings, "VIGI_VMS_PORT", 8554))

    @property
    def host(self) -> str:
        return os.environ.get("VIGI_VMS_HOST") or getattr(settings, "VIGI_VMS_HOST", "127.0.0.1")

    def _find_cloudflared_binary(self) -> Optional[str]:
        """Locates or downloads the platform-specific cloudflared binary."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        is_windows = (sys.platform == "win32" or os.name == "nt")

        if is_windows:
            possible_paths = [
                os.path.join(base_dir, "bin", "cloudflared.exe"),
                os.path.abspath("./bin/cloudflared.exe"),
                r"C:\Program Files\Cloudflare\cloudflared.exe",
                r"C:\Program Files (x86)\Cloudflare\cloudflared.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\cloudflared\cloudflared.exe"),
                os.path.expanduser(r"~\bin\cloudflared.exe"),
            ]
            for p in possible_paths:
                if os.path.isfile(p):
                    return p

            sys_path = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
            if sys_path and sys_path.lower().endswith(".exe"):
                return sys_path

            # Attempt to auto-download Windows binary
            bin_dir = os.path.join(base_dir, "bin")
            target_path = os.path.join(bin_dir, "cloudflared.exe")
            try:
                os.makedirs(bin_dir, exist_ok=True)
                import urllib.request
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
                logger.info(f"Downloading Windows cloudflared from {url} to {target_path}...")
                urllib.request.urlretrieve(url, target_path)
                return target_path
            except Exception as e:
                logger.error(f"Failed to auto-download Windows cloudflared: {e}")
                return None
        else:
            possible_paths = [
                os.path.join(base_dir, "bin", "cloudflared"),
                os.path.abspath("./bin/cloudflared"),
                "/usr/local/bin/cloudflared",
                "/usr/bin/cloudflared"
            ]
            for p in possible_paths:
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    return p

            sys_path = shutil.which("cloudflared")
            if sys_path:
                return sys_path

            # Attempt to auto-download Linux binary
            bin_dir = os.path.join(base_dir, "bin")
            target_path = os.path.join(bin_dir, "cloudflared")
            try:
                os.makedirs(bin_dir, exist_ok=True)
                import urllib.request
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
                logger.info(f"Downloading cloudflared from {url} to {target_path}...")
                urllib.request.urlretrieve(url, target_path)
                os.chmod(target_path, 0o755)
                return target_path
            except Exception as e:
                logger.error(f"Failed to auto-download cloudflared: {e}")
                return None

    def is_listening(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        """Quickly checks if TCP port is listening with 0.5s timeout."""
        target_host = host or self.host
        target_port = port or self.port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((target_host, target_port)) == 0
        except Exception:
            return False

    def probe_rtsp(self, timeout: float = 2.0) -> bool:
        """Verify that the local listener reaches an RTSP origin through Cloudflare."""
        try:
            with socket.create_connection((self.host, self.port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                request = (
                    f"OPTIONS rtsp://{self.host}:{self.port}/ RTSP/1.0\r\n"
                    "CSeq: 1\r\n"
                    "User-Agent: video-agent-healthcheck/1.0\r\n\r\n"
                )
                sock.sendall(request.encode("ascii"))
                response = sock.recv(256)
                if response.startswith(b"RTSP/"):
                    self._last_error = None
                    self._last_probe_error = None
                    return True
                self._last_probe_error = "Cloudflare listener returned a non-RTSP response"
        except (OSError, TimeoutError) as exc:
            self._last_probe_error = f"RTSP origin probe failed: {exc}"
        return False

    def _read_process_stderr(self, process: subprocess.Popen) -> None:
        """Drain cloudflared diagnostics so pipe buffers cannot stall the tunnel."""
        if process.stderr is None:
            return
        try:
            for line in iter(process.stderr.readline, ""):
                message = line.strip()
                if not message:
                    continue
                if "ERR" in message or "error=" in message.lower():
                    self._last_error = message[-500:]
                    logger.error("cloudflared: %s", message)
                else:
                    logger.info("cloudflared: %s", message)
        except Exception as exc:
            logger.debug("cloudflared diagnostic reader stopped: %s", exc)

    def ensure_tunnel_running(self) -> bool:
        """
        Verifies tunnel is active; starts or restarts it if down.
        Thread-safe.
        """
        if self.is_listening():
            return True

        with self._lock:
            # Double-check inside lock
            if self.is_listening():
                return True

            binary = self._find_cloudflared_binary()
            if not binary:
                logger.error("Cannot start Cloudflare tunnel: cloudflared binary not found")
                return False

            local_url = f"{self.host}:{self.port}"
            cmd = [
                binary,
                "access",
                "tcp",
                "--hostname",
                self.hostname,
                "--url",
                local_url
            ]

            logger.info(f"Starting Cloudflare TCP tunnel: {' '.join(cmd)}")
            try:
                # Terminate any stale process reference
                if self._process and self._process.poll() is None:
                    try:
                        self._process.terminate()
                        self._process.wait(timeout=1.0)
                    except Exception:
                        pass

                is_windows = (sys.platform == "win32" or os.name == "nt")
                creationflags = (0x08000000 | 0x00000200) if is_windows else 0  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=creationflags,
                    start_new_session=(not is_windows)
                )
                self._last_error = None
                self._last_probe_error = None
                self._started_at = datetime.now(timezone.utc).isoformat()
                self._stderr_thread = threading.Thread(
                    target=self._read_process_stderr,
                    args=(self._process,),
                    daemon=True,
                    name="CloudflareTunnelDiagnostics",
                )
                self._stderr_thread.start()

                # Poll for up to 4.0 seconds for port to open
                start_time = time.time()
                while time.time() - start_time < 4.0:
                    if self.is_listening():
                        logger.info(f"Cloudflare TCP tunnel active on {local_url} -> {self.hostname} (PID {self._process.pid})")
                        return True
                    time.sleep(0.15)

                logger.warning(f"Cloudflare tunnel started (PID {self._process.pid}), but port {local_url} not yet responding")
                return self.is_listening()
            except Exception as e:
                logger.error(f"Error starting Cloudflare tunnel: {e}")
                return False

    def _watchdog_loop(self):
        """Background thread that monitors and auto-heals the tunnel."""
        while self._running:
            try:
                if not self.is_listening():
                    logger.warning(f"Cloudflare tunnel listener on {self.host}:{self.port} is down. Auto-restarting...")
                    self.ensure_tunnel_running()
            except Exception as e:
                logger.debug(f"Watchdog check notice: {e}")
            time.sleep(5.0)

    def start_supervisor(self):
        """Starts background watchdog supervisor."""
        self._running = True
        self.ensure_tunnel_running()
        if self._watchdog_thread is None or not self._watchdog_thread.is_alive():
            self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="CloudflareTunnelWatchdog")
            self._watchdog_thread.start()
            logger.info("Cloudflare tunnel supervisor & auto-healer started")

    def stop_supervisor(self):
        self._running = False
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=1.0)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None

    def get_status(self) -> Dict[str, Any]:
        listening = self.is_listening()
        process_running = bool(self._process and self._process.poll() is None)
        upstream_active = self.probe_rtsp() if listening else False
        return {
            "active": upstream_active,
            "status": "connected" if upstream_active else ("listener_only" if listening else "offline"),
            "listener_active": listening,
            "upstream_active": upstream_active,
            "process_running": process_running,
            "hostname": self.hostname,
            "local_url": f"{self.host}:{self.port}",
            "target_service": f"rtsp-over-cloudflare://{self.hostname}",
            "pid": self._process.pid if process_running else None,
            "started_at": self._started_at,
            "last_error": self._last_error or self._last_probe_error,
        }

tunnel_service = TunnelService()
