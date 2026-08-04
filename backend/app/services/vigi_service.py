"""
TP-Link VIGI VMS Service Adapter.
Delegates operations to the active CameraProvider implementation obtained from ProviderFactory,
VIGI OpenAPI Client, and VIGI Edge Connector Engine.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Generator
from app.providers.provider_factory import ProviderFactory
from app.services.vigi_openapi_client import vigi_openapi_client
from app.services.vigi_edge_connector import vigi_edge_connector
from app.config import settings

logger = logging.getLogger(__name__)


class VigiVmsService:
    """Service wrapper for CameraProvider, Edge Connector, and OpenAPI operations."""

    def get_active_provider(self, provider_name: Optional[str] = None):
        return ProviderFactory.get_provider(provider_name)

    def get_vigi_config(self) -> Dict[str, Any]:
        """Returns safe environment/settings VIGI VMS configuration."""
        return settings.get_sanitized_config()

    def update_vigi_config(
        self,
        vigi_host: Optional[str] = None,
        vigi_rtsp_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connection_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dynamically updates host / RTSP stream settings in runtime settings."""
        if vigi_host:
            os.environ["VIGI_VMS_HOST"] = vigi_host
            settings.VIGI_VMS_HOST = vigi_host
        if vigi_rtsp_url:
            os.environ["VIGI_VMS_RTSP_URL"] = vigi_rtsp_url
            settings.VIGI_VMS_RTSP_URL = vigi_rtsp_url
        if username:
            os.environ["VIGI_VMS_USERNAME"] = username
            settings.VIGI_VMS_USERNAME = username
        if password:
            os.environ["VIGI_VMS_PASSWORD"] = password
            settings.VIGI_VMS_PASSWORD = password
        if connection_type:
            os.environ["CONNECTION_TYPE"] = connection_type
            settings.CONNECTION_TYPE = connection_type
        if provider:
            os.environ["CAMERA_PROVIDER"] = provider

        logger.info(f"VIGI Configuration updated: Host={vigi_host}, ConnectionType={connection_type}, Provider={provider}")
        return self.get_vigi_config()

    def get_capabilities(self, provider_name: Optional[str] = None) -> Dict[str, bool]:
        """Returns detected runtime capabilities of the active camera provider."""
        provider = self.get_active_provider(provider_name)
        return provider.detect_capabilities()

    def get_health(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns health metrics and provider status."""
        provider = self.get_active_provider(provider_name)
        return provider.get_health()

    def discover_network_devices(self, provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scans local network using ONVIF WS-Discovery and OpenAPI."""
        provider = self.get_active_provider(provider_name)
        return provider.discover_network_devices()

    def get_channels(self, provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of active channels from active camera provider."""
        provider = self.get_active_provider(provider_name)
        return provider.get_channels()

    def test_connection(
        self,
        vigi_host: Optional[str] = None,
        port: int = 554,
        username: str = "",
        password: str = "",
        rtsp_url: str = "",
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tests connection to VIGI VMS server or direct RTSP live stream."""
        provider = self.get_active_provider(provider_name)
        return provider.test_connection(
            host=vigi_host,
            port=port,
            username=username,
            password=password,
            rtsp_url=rtsp_url
        )

    def generate_mjpeg_stream(
        self,
        channel_id: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> Generator[bytes, None, None]:
        """Generates live HTTP MJPEG stream."""
        provider = self.get_active_provider(provider_name)
        return provider.generate_mjpeg_stream(channel_id=channel_id, rtsp_url=rtsp_url)

    def summarize_vigi_stream(
        self,
        channel_id: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        duration_seconds: int = 15,
        vigi_host: Optional[str] = None,
        username: str = "",
        password: str = "",
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs AI summarization on stream using active provider."""
        provider = self.get_active_provider(provider_name)
        return provider.summarize_stream(
            channel_id=channel_id,
            rtsp_url=rtsp_url,
            duration_seconds=duration_seconds,
            host=vigi_host,
            username=username,
            password=password
        )

    # ── OpenAPI Operations ───────────────────────────────────────────────────

    def get_openapi_devices(self) -> List[Dict[str, Any]]:
        return vigi_openapi_client.get_devices()

    def get_openapi_device_config(self, device_id: str) -> Dict[str, Any]:
        return vigi_openapi_client.get_device_config(device_id)

    def update_openapi_device_config(self, device_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        return vigi_openapi_client.update_device_config(device_id, updates)

    def subscribe_openapi_events(
        self,
        webhook_url: str,
        event_types: Optional[List[str]] = None,
        device_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return vigi_openapi_client.subscribe_events(webhook_url, event_types, device_ids)

    # ── Edge Connector Operations ─────────────────────────────────────────────

    def get_edge_health(self) -> Dict[str, Any]:
        return vigi_edge_connector.get_all_stream_health()

    def discover_edge_cameras(self) -> Dict[str, Any]:
        return vigi_edge_connector.discover_local_cameras()

    def reconnect_edge_stream(self, channel_id: str) -> Dict[str, Any]:
        return vigi_edge_connector.trigger_auto_reconnect(channel_id)

    def forward_edge_event(
        self,
        channel_id: str,
        event_type: str,
        confidence: float = 0.95,
        snapshot_url: Optional[str] = None,
        clip_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return vigi_edge_connector.forward_event_to_cloud(
            channel_id=channel_id,
            event_type=event_type,
            confidence=confidence,
            snapshot_url=snapshot_url,
            clip_url=clip_url,
            metadata=metadata
        )

    def get_forwarded_events_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        return vigi_edge_connector.get_forwarded_events_log(limit)


vigi_service = VigiVmsService()
