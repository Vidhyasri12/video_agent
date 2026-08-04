import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_capabilities_endpoint():
    response = client.get("/api/v1/vigi/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "provider" in data
    assert "capabilities" in data
    assert "supported_providers" in data
    assert data["capabilities"]["supports_rtsp"] is True

def test_health_endpoint():
    response = client.get("/api/v1/vigi/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "healthy_simulated"]
    assert "provider" in data
    assert "capabilities" in data
    assert "timestamp" in data

def test_config_endpoint_redacts_passwords():
    response = client.get("/api/v1/vigi/config")
    assert response.status_code == 200
    data = response.json()
    assert "vigi_vms_password" not in data  # Redacted
    assert "vigi_vms_password_set" in data
