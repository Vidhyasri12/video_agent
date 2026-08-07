import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_clear_db_endpoint():
    response = client.post("/api/v1/video/clear-db")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert "message" in data

def test_video_upload_and_proper_summary_flow():
    # 1. Clear database before test
    clear_res = client.post("/api/v1/video/clear-db")
    assert clear_res.status_code == 200

    # 2. Upload a custom video file with specific name
    test_filename = "traffic_patrol_cam1.mp4"
    dummy_content = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42\x00\x00\x00\x08free"
    
    upload_res = client.post(
        f"/api/v1/video/upload?camera_name={test_filename}",
        files={"file": (test_filename, dummy_content, "video/mp4")}
    )
    
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    
    assert "video_info" in upload_data
    video_info = upload_data["video_info"]
    assert video_info["original_filename"] == test_filename
    saved_filename = video_info["filename"]
    assert "description" in upload_data
    desc = upload_data["description"]
    assert "title" in desc
    assert "summary" in desc

    # 3. Summarize the uploaded video explicitly by its original filename
    sum_orig_res = client.post(f"/api/v1/video/summarize?filename={test_filename}")
    assert sum_orig_res.status_code == 200
    sum_orig_data = sum_orig_res.json()
    assert sum_orig_data["status"] == "success"
    assert "description" in sum_orig_data

    # 4. Summarize the uploaded video explicitly by its saved filename
    sum_saved_res = client.post(f"/api/v1/video/summarize?filename={saved_filename}")
    assert sum_saved_res.status_code == 200
    sum_saved_data = sum_saved_res.json()
    assert sum_saved_data["status"] == "success"

    # 5. Clear database and state
    clear_after_res = client.post("/api/v1/video/clear-db")
    assert clear_after_res.status_code == 200
    assert clear_after_res.json()["status"] == "success"

def test_delete_clear_db_endpoint():
    response = client.delete("/api/v1/video/clear-db")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
