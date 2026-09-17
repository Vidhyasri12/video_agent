import os
import pytest
from app.providers import (
    ProviderFactory,
    VigiProvider,
    HikvisionProvider,
    DahuaProvider,
    AxisProvider,
    MockProvider
)
from app.core.exceptions import UnsupportedCapabilityError, CameraOfflineError
from app.providers.vigi_provider import DEFAULT_VIGI_CHANNELS

def test_provider_factory_list():
    providers = ProviderFactory.list_supported_providers()
    assert "vigi" in providers
    assert "hikvision" in providers
    assert "dahua" in providers
    assert "axis" in providers
    assert "mock" in providers

def test_vigi_provider_capabilities():
    provider = ProviderFactory.get_provider("vigi")
    assert isinstance(provider, VigiProvider)
    assert provider.provider_type == "vigi"
    caps = provider.detect_capabilities()
    assert caps["supports_rtsp"] is True
    assert caps["supports_onvif"] is True
    assert caps["supports_openapi"] is False

def test_hikvision_provider_capabilities():
    provider = ProviderFactory.get_provider("hikvision")
    assert isinstance(provider, HikvisionProvider)
    assert provider.provider_type == "hikvision"
    caps = provider.detect_capabilities()
    assert caps["supports_rtsp"] is True

def test_dahua_provider_capabilities():
    provider = ProviderFactory.get_provider("dahua")
    assert isinstance(provider, DahuaProvider)
    assert provider.provider_type == "dahua"
    caps = provider.detect_capabilities()
    assert caps["supports_rtsp"] is True

def test_axis_provider_capabilities():
    provider = ProviderFactory.get_provider("axis")
    assert isinstance(provider, AxisProvider)
    assert provider.provider_type == "axis"
    caps = provider.detect_capabilities()
    assert caps["supports_rtsp"] is True

def test_mock_provider_capabilities():
    provider = ProviderFactory.get_provider("mock")
    assert isinstance(provider, MockProvider)
    assert provider.provider_type == "mock"
    caps = provider.detect_capabilities()
    assert caps["supports_rtsp"] is True

def test_unsupported_provider_raises_exception():
    with pytest.raises(UnsupportedCapabilityError):
        ProviderFactory.get_provider("unknown_vendor_xyz")
def test_vigi_nvr_channels_use_documented_live_paths():
    for channel_number, channel in enumerate(DEFAULT_VIGI_CHANNELS, start=1):
        assert channel["rtsp_url"].endswith(f"/live/{channel_number}/1/avm")
        assert channel["sub_rtsp_url"].endswith(f"/live/{channel_number}/2/avm")
