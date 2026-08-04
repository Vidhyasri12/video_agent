import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_video_summarize_endpoint():
    response = client.post("/api/v1/video/summarize?filename=test_video.mp4")
    assert response.status_code == 200
    data = response.json()
    assert "description" in data
    assert "summary" in data

def test_video_upload_endpoint():
    response = client.post(
        "/api/v1/video/upload?camera_name=15396218_1920_1080_25fps.mp4",
        files={"file": ("15396218_1920_1080_25fps.mp4", b"dummy video bytes", "video/mp4")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "camera_id" in data
    assert "video_info" in data
    assert "description" in data
    assert "summary" in data
