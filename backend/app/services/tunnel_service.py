"""
Cloudflare TCP Tunnel Supervisor & Auto-Healer.
Automatically launches, monitors, and auto-restarts the `cloudflared access tcp`
proxy for RTSP camera streaming so connections never get 'Connection refused'.
"""

import os
import time
import socket
import logging
import subprocess
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TunnelService:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_attempt_time = 0.0

    @property
    def hostname(self) -> str:
        return os.environ.get("CLOUDFLARE_HOSTNAME", "cam-rtsp.goodwindco.in")

    @property
    def port(self) -> int:
        return int(os.environ.get("VIGI_VMS_PORT", 8554))

    @property
    def host(self) -> str:
        return os.environ.get("VIGI_VMS_HOST", "127.0.0.1")

    def _find_cloudflared_binary(self) -> Optional[str]:
        """Locates or downloads cloudflared binary."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        possible_paths = [
            os.path.join(base_dir, "bin", "cloudflared.exe"),
            os.path.join(base_dir, "bin", "cloudflared-windows-amd64.exe"),
            os.path.join(base_dir, "bin", "cloudflared"),
            os.path.abspath("./bin/cloudflared.exe"),
            os.path.abspath("./bin/cloudflared-windows-amd64.exe"),
            os.path.abspath("./bin/cloudflared"),
            "/usr/local/bin/cloudflared",
            "/usr/bin/cloudflared"
        ]
        for p in possible_paths:
            if os.path.isfile(p):
                if os.name == "nt":
                    return p
                if os.access(p, os.X_OK):
                    return p

        import shutil
        sys_path = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
        if sys_path:
            return sys_path

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
        """Quickly checks if TCP port is listening with 0.2s fast timeout."""
        target_host = host or self.host
        target_port = port or self.port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                return s.connect_ex((target_host, target_port)) == 0
        except Exception:
            return False

    def ensure_tunnel_running(self) -> bool:
        """
        Verifies tunnel is active; starts or restarts it if down.
        Enforces 15s cooldown between spawn attempts to prevent process thrashing.
        """
        if self.is_listening():
            return True

        with self._lock:
            if self.is_listening():
                return True

            now = time.time()
            if now - self._last_attempt_time < 15.0:
                return False

            self._last_attempt_time = now

            binary = self._find_cloudflared_binary()
            if not binary:
                logger.error("Cannot start Cloudflare tunnel: cloudflared binary not found")
                return False

            local_url = f"127.0.0.1:{self.port}"
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
                if self._process and self._process.poll() is None:
                    try:
                        self._process.terminate()
                    except Exception:
                        pass

                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

                # Poll for up to 1.0 second for port to open
                start_time = time.time()
                while time.time() - start_time < 1.0:
                    if self.is_listening():
                        logger.info(f"Cloudflare TCP tunnel active on {local_url} -> {self.hostname} (PID {self._process.pid})")
                        return True
                    time.sleep(0.1)

                logger.warning(f"Cloudflare tunnel started (PID {self._process.pid}), but port {local_url} not responding yet")
                return self.is_listening()
            except Exception as e:
                logger.error(f"Error starting Cloudflare tunnel: {e}")
                return False


    def _watchdog_loop(self):
        """Background thread that monitors and auto-heals the tunnel."""
        while self._running:
            try:
                if not self.is_listening():
                    logger.warning("Cloudflare tunnel listener is down. Auto-restarting...")
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
                except Exception:
                    pass
                self._process = None

    def get_status(self) -> Dict[str, Any]:
        listening = self.is_listening()
        return {
            "active": listening,
            "status": "connected" if listening else "offline",
            "hostname": self.hostname,
            "local_url": f"{self.host}:{self.port}",
            "pid": self._process.pid if self._process and self._process.poll() is None else None
        }

tunnel_service = TunnelService()
