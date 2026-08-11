import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.vss_agent_service import vss_agent
from app.services.video_service import video_service

client = TestClient(app)

def test_extract_time_range_patterns():
    # 1. from X to Y
    res1 = vss_agent._extract_time_range("What happened from 0:05 to 0:20 in this video?", 30.0)
    assert res1 == (5.0, 20.0)

    # 2. between X and Y
    res2 = vss_agent._extract_time_range("Describe events between 10s and 25s", 30.0)
    assert res2 == (10.0, 25.0)

    # 3. at X
    res3 = vss_agent._extract_time_range("What happens at 00:15?", 30.0)
    assert res3 is not None
    assert res3[0] <= 15.0 <= res3[1]

    # 4. first N seconds
    res4 = vss_agent._extract_time_range("Show me the first 10 seconds", 30.0)
    assert res4 == (0.0, 10.0)

    # 5. last N seconds
    res5 = vss_agent._extract_time_range("Summarize the last 10 sec", 30.0)
    assert res5 == (20.0, 30.0)

def test_chat_endpoint_with_timing_check():
    response = client.post(
        "/api/v1/video/chat",
        json={
            "filename": "Sample_Traffic_Surveillance.mp4",
            "question": "What happens from 0:05 to 0:15?"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "00:05" in data["scope"] or "0:05" in data["scope"]
    assert "answer" in data
    assert len(data["timeline"]) > 0

def test_chat_endpoint_full_video_question():
    response = client.post(
        "/api/v1/video/chat",
        json={
            "filename": "Sample_Traffic_Surveillance.mp4",
            "question": "Give me an executive summary of this video"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["question"] == "Give me an executive summary of this video"
    assert "answer" in data
