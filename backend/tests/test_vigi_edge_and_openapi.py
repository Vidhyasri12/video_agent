import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.vigi_openapi_client import vigi_openapi_client
from app.services.vigi_edge_connector import vigi_edge_connector
from app.providers import ProviderFactory, VigiOpenApiProvider, VigiCloudStreamingProvider

client = TestClient(app)


def test_vigi_openapi_client_auth_and_devices():
    auth_res = vigi_openapi_client.authenticate()
    assert auth_res["status"] == "authenticated"
    assert "access_token" in auth_res
    assert vigi_openapi_client.is_authenticated() is True

    devices = vigi_openapi_client.get_devices()
    assert len(devices) >= 3
    assert devices[0]["device_id"] == "vigi-openapi-cam-01"


def test_vigi_openapi_client_config():
    cfg = vigi_openapi_client.get_device_config("vigi-openapi-cam-01")
    assert cfg["status"] == "success"
    assert "config" in cfg

    updated = vigi_openapi_client.update_device_config("vigi-openapi-cam-01", {"motion_sensitivity": 90})
    assert updated["status"] == "success"
    assert updated["current_config"]["motion_sensitivity"] == 90


def test_vigi_openapi_client_subscriptions():
    sub = vigi_openapi_client.subscribe_events(
        webhook_url="https://cloud.videoagent.io/webhooks/vigi-events",
        event_types=["motion_detection", "line_crossing"]
    )
    assert sub["status"] == "success"
    assert sub["subscription"]["webhook_url"] == "https://cloud.videoagent.io/webhooks/vigi-events"


def test_vigi_edge_connector_stream_health_and_reconnect():
    health = vigi_edge_connector.get_all_stream_health()
    assert health["status"] == "success"
    assert health["total_streams"] >= 4

    reconnect_res = vigi_edge_connector.trigger_auto_reconnect("vigi-cam-01")
    assert reconnect_res["status"] == "reconnected"
    assert reconnect_res["channel_id"] == "vigi-cam-01"


def test_vigi_edge_connector_selective_cloud_forwarder():
    forward_res = vigi_edge_connector.forward_event_to_cloud(
        channel_id="vigi-cam-01",
        event_type="intrusion_detection",
        confidence=0.98,
        snapshot_url="/api/v1/edge/snapshots/test.jpg"
    )
    assert forward_res["status"] == "forwarded"
    assert forward_res["event"]["event_type"] == "intrusion_detection"
    assert forward_res["event"]["raw_stream_forwarded"] is False  # Only event/snapshot sent

    log = vigi_edge_connector.get_forwarded_events_log()
    assert len(log) >= 1
    assert log[0]["event_type"] == "intrusion_detection"


def test_provider_factory_and_capabilities():
    providers = ProviderFactory.list_supported_providers()
    assert "vigi_openapi" in providers
    assert "vigi_cloud_streaming" in providers

    openapi_prov = ProviderFactory.get_provider("vigi_openapi")
    assert isinstance(openapi_prov, VigiOpenApiProvider)
    caps = openapi_prov.detect_capabilities()
    assert caps["supports_openapi"] is True
    assert caps["supports_edge_connector"] is True
    assert caps["supports_rtsp"] is True

    cloud_prov = ProviderFactory.get_provider("vigi_cloud_streaming")
    assert isinstance(cloud_prov, VigiCloudStreamingProvider)
    caps_cloud = cloud_prov.detect_capabilities()
    assert caps_cloud["supports_cloud_streaming"] is True


def test_api_vigi_edge_endpoints():
    res = client.get("/api/v1/vigi/edge/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"

    res_disc = client.get("/api/v1/vigi/edge/discover")
    assert res_disc.status_code == 200
    assert res_disc.json()["status"] == "success"

    res_rec = client.post("/api/v1/vigi/edge/reconnect", json={"channel_id": "vigi-cam-01"})
    assert res_rec.status_code == 200
    assert res_rec.json()["status"] == "reconnected"

    res_fwd = client.post(
        "/api/v1/vigi/edge/forward-event",
        json={"channel_id": "vigi-cam-01", "event_type": "line_crossing", "confidence": 0.92}
    )
    assert res_fwd.status_code == 200
    assert res_fwd.json()["status"] == "forwarded"

    res_log = client.get("/api/v1/vigi/edge/forwarded-events")
    assert res_log.status_code == 200
    assert res_log.json()["status"] == "success"


def test_api_vigi_openapi_endpoints():
    res_dev = client.get("/api/v1/vigi/openapi/devices")
    assert res_dev.status_code == 200
    assert res_dev.json()["count"] >= 3

    res_cfg = client.get("/api/v1/vigi/openapi/config/vigi-openapi-cam-01")
    assert res_cfg.status_code == 200
    assert res_cfg.json()["status"] == "success"

    res_upd = client.post(
        "/api/v1/vigi/openapi/config/vigi-openapi-cam-01",
        json={"motion_sensitivity": 85}
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["current_config"]["motion_sensitivity"] == 85

    res_sub = client.post(
        "/api/v1/vigi/openapi/subscribe",
        json={"webhook_url": "https://api.videoagent.io/vigi/webhooks"}
    )
    assert res_sub.status_code == 200
    assert res_sub.json()["status"] == "success"
