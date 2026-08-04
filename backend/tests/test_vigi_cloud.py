import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_vigi_cloud_disabled_by_default():
    """Verify that undocumented VIGI Cloud endpoints return 501 UNSUPPORTED_CAPABILITY when feature flag is OFF."""
    os.environ["ENABLE_EXPERIMENTAL_CLOUD_APIS"] = "false"

    response = client.post("/api/v1/vigi/cloud/auth", json={
        "client_id": "test_client_id",
        "client_secret": "test_secret",
        "cloud_org_id": "org-vigi-test"
    })
    assert response.status_code == 501
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "UNSUPPORTED_CAPABILITY"

def test_vigi_cloud_experimental_enabled():
    """Verify that experimental VIGI Cloud endpoints function when feature flag is explicitly enabled."""
    os.environ["ENABLE_EXPERIMENTAL_CLOUD_APIS"] = "true"

    try:
        response = client.post("/api/v1/vigi/cloud/auth", json={
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "cloud_org_id": "org-vigi-test"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "authenticated"
        assert "access_token" in data

        # Test devices endpoint
        dev_res = client.get("/api/v1/vigi/cloud/devices")
        assert dev_res.status_code == 200
        assert dev_res.json()["status"] == "success"

        # Test stream ticket endpoint
        ticket_res = client.post("/api/v1/vigi/cloud/stream-ticket", json={"device_id": "vigi-cloud-cam-01"})
        assert ticket_res.status_code == 200
        assert ticket_res.json()["status"] == "success"

        # Test status endpoint
        status_res = client.get("/api/v1/vigi/cloud/status")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "experimental_online"
    finally:
        os.environ["ENABLE_EXPERIMENTAL_CLOUD_APIS"] = "false"
