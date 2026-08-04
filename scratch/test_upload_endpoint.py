import os
import sys
import json
import urllib.request
import urllib.parse
import threading
import time

sys.path.insert(0, os.path.abspath("backend"))

from app.api.v1.video import upload_video
from app.services.vss_agent_service import vss_agent
import server

def test_vss_agent_nan():
    res = vss_agent._generate_dynamic_vss_summary("Test", "test.mp4", {"timestamps": [], "motion_diffs": [], "duration": 0})
    json_str = json.dumps(res)
    assert res["title"] == "NVIDIA VSS Summary: Test"
    print("VSS Agent NaN test PASSED!")

def test_server_multipart_parse():
    handler = server.VideoAgentHandler.__new__(server.VideoAgentHandler)
    body = (
        b"------WebKitFormBoundaryx1Sb0GTyJdQSmTRk\r\n"
        b'Content-Disposition: form-data; name="file"; filename="15396218_1920_1080_25fps.mp4"\r\n'
        b"Content-Type: video/mp4\r\n\r\n"
        b"[dummy_binary_video_data_12345]\r\n"
        b"------WebKitFormBoundaryx1Sb0GTyJdQSmTRk--\r\n"
    )
    content_type = "multipart/form-data; boundary=----WebKitFormBoundaryx1Sb0GTyJdQSmTRk"
    filename, camera_name, video_bytes = handler._parse_multipart(body, content_type)
    assert filename == "15396218_1920_1080_25fps.mp4"
    assert video_bytes == b"[dummy_binary_video_data_12345]"
    print("Server multipart parse test PASSED!")

def test_live_server_curl():
    server_address = ("127.0.0.1", 8005)
    httpd = server.ThreadedTCPServer(server_address, server.VideoAgentHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.5)

    url = "http://127.0.0.1:8005/api/v1/video/upload?camera_name=15396218_1920_1080_25fps.mp4"
    boundary = "----WebKitFormBoundaryx1Sb0GTyJdQSmTRk"
    body_str = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="15396218_1920_1080_25fps.mp4"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
        f"TEST_VIDEO_BYTES_CONTENT\r\n"
        f"--{boundary}--\r\n"
    )
    req = urllib.request.Request(
        url,
        data=body_str.encode("utf-8"),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json, text/plain, */*"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "camera_id" in data
        assert data["camera_name"] == "15396218_1920_1080_25fps.mp4"
        assert "video_info" in data
        assert "description" in data
        assert "summary" in data

    httpd.shutdown()
    print("Live server HTTP upload curl test PASSED!")

if __name__ == "__main__":
    test_vss_agent_nan()
    test_server_multipart_parse()
    test_live_server_curl()
    print("All unit tests & HTTP integration tests PASSED successfully!")
