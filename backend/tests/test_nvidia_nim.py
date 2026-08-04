import os
import sys
import cv2
import base64
import json
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath("."))

from app.services.vss_agent_service import vss_agent

api_key = os.environ.get("NVIDIA_API_KEY", "")
print("Loaded NVIDIA API Key:", api_key[:15] + "...")

# Test video file
video_file = "../storage/videos/2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4"
if not os.path.exists(video_file):
    video_file = "./storage/videos/2d0394f7-35f0-4843-ad58-1f44dbada43e.mp4"

extracted = vss_agent.extract_keyframes(video_file)
print(f"Extracted {len(extracted['base64_frames'])} keyframes. Duration: {extracted['duration']}s")

# Combine 4 keyframes into a 2x2 grid image
b64_list = extracted['base64_frames']
frames = []
for b64 in b64_list[:4]:
    nparr = np.frombuffer(base64.b64decode(b64), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (320, 240))
    frames.append(img)

while len(frames) < 4:
    frames.append(np.zeros((240, 320, 3), dtype=np.uint8))

top_row = np.hstack((frames[0], frames[1]))
bot_row = np.hstack((frames[2], frames[3]))
grid_img = np.vstack((top_row, bot_row))

success, buffer = cv2.imencode('.jpg', grid_img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
grid_b64 = base64.b64encode(buffer).decode('utf-8')

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

prompt = (
    f"You are an NVIDIA VSS (Visual Search & Summarization) AI Agent. "
    f"This image is a 2x2 composite grid showing keyframes from a video titled 'City Intersection' in chronological order "
    f"(Top-Left = Frame 1, Top-Right = Frame 2, Bottom-Left = Frame 3, Bottom-Right = Frame 4). "
    f"Analyze the video events and respond ONLY with a valid raw JSON object matching this schema:\n"
    f"{{\n"
    f'  "title": "NVIDIA VSS Analysis: City Intersection",\n'
    f'  "summary": "Detailed summary of traffic, pedestrians, and scene events...",\n'
    f'  "scene_type": "Roadway & Traffic Monitoring",\n'
    f'  "confidence": 0.98,\n'
    f'  "detected_objects": ["Sedan", "Pedestrian", "Traffic Light"],\n'
    f'  "timeline": [{{"time": "00:00 - 00:10", "seconds": 0, "event": "Description of frame 1", "tag": "Baseline"}}],\n'
    f'  "safety_highlights": ["Highlight 1", "Highlight 2"]\n'
    f"}}\n"
    f"Do not include any conversational text or explanation outside the JSON object."
)

payload = {
    "model": "meta/llama-3.2-11b-vision-instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{grid_b64}"}}
            ]
        }
    ],
    "max_tokens": 1024,
    "temperature": 0.2
}

resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
print("HTTP Status:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    print("\n--- NVIDIA NIM Vision Model Response ---\n")
    print(content)
else:
    print("Error:", resp.text)
