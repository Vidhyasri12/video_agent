"""
Provider Architecture Package for Camera & VMS Integrations.
"""
from app.providers.base_provider import CameraProvider
from app.providers.vigi_provider import VigiProvider
from app.providers.vigi_openapi_provider import VigiOpenApiProvider
from app.providers.vigi_cloud_streaming_provider import VigiCloudStreamingProvider
from app.providers.hikvision_provider import HikvisionProvider
from app.providers.dahua_provider import DahuaProvider
from app.providers.axis_provider import AxisProvider
from app.providers.mock_provider import MockProvider
from app.providers.provider_factory import ProviderFactory

__all__ = [
    "CameraProvider",
    "VigiProvider",
    "VigiOpenApiProvider",
    "VigiCloudStreamingProvider",
    "HikvisionProvider",
    "DahuaProvider",
    "AxisProvider",
    "MockProvider",
    "ProviderFactory",
]
