"""
Abstract Base Class for Camera Providers.
Enforces standard interfaces across all VMS and Camera implementations.
Conforms to Production Provider Abstraction with Capability Detection.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Generator


class CameraProvider(ABC):
    """
    Polymorphic Camera Provider interface.
    The rest of the VideoAgent application depends strictly on this abstraction.
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Returns provider identifier string (e.g. 'vigi', 'vigi_openapi', 'vigi_cloud_streaming', 'hikvision', 'dahua', 'axis', 'mock')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Returns human-readable provider name."""
        pass

    @abstractmethod
    def detect_capabilities(self) -> Dict[str, bool]:
        """
        Detects runtime capabilities supported by this provider/deployment.
        Expected keys:
        - supports_rtsp: True/False
        - supports_onvif: True/False
        - supports_openapi: True/False
        - supports_edge_connector: True/False
        - supports_cloud_streaming: True/False
        - supports_ptz: True/False
        - supports_event_subscriptions: True/False
        - supports_configuration: True/False
        """
        pass

    @abstractmethod
    def test_connection(
        self,
        host: Optional[str] = None,
        port: int = 554,
        username: str = "",
        password: str = "",
        rtsp_url: str = ""
    ) -> Dict[str, Any]:
        """Tests connectivity to camera/NVR/VMS."""
        pass

    @abstractmethod
    def get_channels(self) -> List[Dict[str, Any]]:
        """Returns list of active channels/cameras under this provider."""
        pass

    @abstractmethod
    def generate_mjpeg_stream(
        self,
        channel_id: Optional[str] = None,
        rtsp_url: Optional[str] = None
    ) -> Generator[bytes, None, None]:
        """Transcodes video stream into live HTTP MJPEG stream with CCTV OSD overlay."""
        pass

    @abstractmethod
    def summarize_stream(
        self,
        channel_id: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        duration_seconds: int = 15,
        host: Optional[str] = None,
        username: str = "",
        password: str = ""
    ) -> Dict[str, Any]:
        """Extracts keyframes from stream and runs AI Agent summarization."""
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """Returns health status metrics of provider and connected cameras."""
        pass

    @abstractmethod
    def discover_network_devices(self) -> List[Dict[str, Any]]:
        """Discovers network cameras on local subnet using ONVIF WS-Discovery and OpenAPI."""
        pass
