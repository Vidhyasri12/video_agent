"""
Provider Factory and Registry for Camera Implementations.
Conforms to Production Provider Abstraction with Capability Detection.
Ensures application components decouple from specific camera vendors and transport protocols.
"""

import os
import logging
from typing import Dict, Type, Optional
from app.providers.base_provider import CameraProvider
from app.providers.vigi_provider import VigiProvider
from app.providers.vigi_openapi_provider import VigiOpenApiProvider
from app.providers.vigi_cloud_streaming_provider import VigiCloudStreamingProvider
from app.providers.hikvision_provider import HikvisionProvider
from app.providers.dahua_provider import DahuaProvider
from app.providers.axis_provider import AxisProvider
from app.providers.mock_provider import MockProvider
from app.core.exceptions import UnsupportedCapabilityError

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory registry managing CameraProvider instances."""

    _registry: Dict[str, Type[CameraProvider]] = {
        "vigi": VigiProvider,
        "vigi_openapi": VigiOpenApiProvider,
        "vigi_cloud_streaming": VigiCloudStreamingProvider,
        "hikvision": HikvisionProvider,
        "dahua": DahuaProvider,
        "axis": AxisProvider,
        "mock": MockProvider
    }

    _instances: Dict[str, CameraProvider] = {}

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[CameraProvider]):
        """Registers a new camera provider implementation."""
        cls._registry[name.lower()] = provider_cls
        logger.info(f"Registered camera provider: '{name}'")

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> CameraProvider:
        """
        Returns an instance of the requested provider.
        If provider_name is None, defaults to environment variable `CAMERA_PROVIDER` or 'vigi'.
        """
        name = (provider_name or os.environ.get("CAMERA_PROVIDER", "vigi")).lower()

        if name not in cls._registry:
            valid_providers = ", ".join(cls._registry.keys())
            raise UnsupportedCapabilityError(
                f"Unknown camera provider '{name}'. Configured supported providers are: {valid_providers}"
            )

        if name not in cls._instances:
            provider_cls = cls._registry[name]
            cls._instances[name] = provider_cls()
            logger.info(f"Instantiated camera provider '{name}' ({cls._instances[name].display_name})")

        return cls._instances[name]

    @classmethod
    def list_supported_providers(cls) -> Dict[str, str]:
        """Returns dict of supported provider keys and display names."""
        result = {}
        for name, cls_type in cls._registry.items():
            try:
                inst = cls.get_provider(name)
                result[name] = inst.display_name
            except Exception:
                result[name] = name.upper()
        return result
