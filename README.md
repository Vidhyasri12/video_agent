# NVIDIA VSS Video Intelligence & Summarizer

Streamlined, production-ready AI Video Intelligence application inspired by NVIDIA VSS (Video Search and Summarization) architecture. Allows users to upload video files and generate instant AI narrative summaries, scene classification, object tracking pills, and timestamp breakdown sequences.

**Live Camera Streaming**: All cameras are configured to show live RTSP streaming videos using the password `Gt@102020`.

---

## 🌟 Key Features

1. **Clean Single-Page Workflow**:
   - Drag & drop or browse to upload video files (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`).
   - Instant video playback preview.
   - Prominent **"Summarize Video"** button powering NVIDIA VSS vision model summarization.
   - Remove file button to clear and upload new videos seamlessly.

2. **Live Camera Streaming**:
   - **7 VIGI Camera Channels** configured with live RTSP streaming
   - Real-time MJPEG transcoded streams from IP cameras
   - Camera Grid View and Live Surveillance Wall modes
   - All cameras use password: `Gt@102020`
   - Automatic fallback to sample videos if RTSP connection fails
   - Live OSD overlay showing camera name and real-time timestamp

3. **VSS Vision Model Summary**:
   - Executive narrative summary.
   - Scene classification & confidence scoring.
   - Entity & object tracking pills.
   - Timestamp breakdown timeline (`00:00 - 00:05`, `00:05 - 00:12`, etc.).
   - Key safety & operational insights.
   - One-click copy summary report to clipboard.

---

## 🚀 Running the Application

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenCV (for RTSP streaming): `pip install opencv-python`

### 1. Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
API Documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend (React + TS + Vite)
```bash
cd frontend
npm install
npm run dev
```
Access the application at: [http://localhost:3000](http://localhost:3000)

---

## 📹 Camera Configuration

All 7 cameras are configured with the following RTSP credentials:
- **Username**: Niyas
- **Password**: Gt@102020
- **Protocol**: RTSP over TCP
- **Default Port**: 554

### Camera Channels:
1. **Channel 1**: 192.168.31.81 - Loading Area (VIGI C540-W)
2. **Channel 2**: 192.168.31.99 - Powder Coating Area (VIGI C440-W 2.0)
3. **Channel 3**: 192.168.31.251 - Front Door (VIGI C440-W 2.0)
4. **Channel 4**: 192.168.31.227 - NVR Central Hub (VIGI NVR2016H)
5. **Channel 5**: 192.168.31.99 - Powder Coating Area Zone 2 (VIGI C440-W UN)
6. **Channel 6**: 192.168.31.251 - Front Entry Perimeter (VIGI C440-W UN)
7. **Channel 7**: 192.168.31.81 - Cargo Bay 2 (VIGI C540-W)

### Stream Mode
The application defaults to **MJPEG Transcode** mode for live streaming, which provides:
- Real-time frame-by-frame streaming from RTSP cameras
- Browser-compatible HTTP MJPEG format
- Live OSD overlay with camera info and timestamps
- Automatic RTSP connection retry logic
- Fallback to sample videos if cameras are offline
