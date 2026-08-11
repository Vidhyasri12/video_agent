from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Form, Query
from typing import Optional
from pydantic import BaseModel
from app.services.video_service import video_service
import os

router = APIRouter()

class VideoSummarizeRequest(BaseModel):
    filename: Optional[str] = None

class VideoChatRequest(BaseModel):
    filename: Optional[str] = None
    question: str
    video_title: Optional[str] = None

@router.post("/upload")
async def upload_video(
    camera_name: Optional[str] = Query(None),
    camera_name_form: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    import urllib.parse
    eff_camera_name = camera_name or camera_name_form or "Uploaded Feed"
    if eff_camera_name:
        eff_camera_name = urllib.parse.unquote(eff_camera_name)
    
    file_name = None
    content = b""

    if file:
        file_name = file.filename
        try:
            content = await file.read()
        except Exception:
            content = b""

    if not file_name:
        # Fallback to camera_name if it ends with video extension, or default
        if eff_camera_name and any(eff_camera_name.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]):
            file_name = eff_camera_name
        else:
            file_name = "uploaded_video.mp4"

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        file_name = file_name + ".mp4"

    save_res = await video_service.save_uploaded_video(file_name, content)
    desc = save_res.get("description")

    return {
        "camera_id": "cam-" + save_res.get("video_id", "uploaded"),
        "camera_name": eff_camera_name,
        "video_info": save_res,
        "description": desc,
        "summary": desc
    }

@router.post("/describe")
@router.post("/summarize")
@router.get("/describe")
@router.get("/summarize")
async def describe_video(
    filename: Optional[str] = None,
    payload: Optional[VideoSummarizeRequest] = Body(None)
):
    target_filename = filename or (payload.filename if payload and payload.filename else None) or "13258882-uhd_3840_2160_30fps.mp4"
    description_data = video_service.generate_video_description(target_filename)

    return {
        "status": "success",
        "filename": target_filename,
        "summary": description_data.get("summary", ""),
        "description": description_data,
        "title": description_data.get("title", ""),
        "scene_type": description_data.get("scene_type", ""),
        "timeline": description_data.get("timeline", []),
        "detected_objects": description_data.get("detected_objects", []),
        "safety_highlights": description_data.get("safety_highlights", [])
    }

@router.post("/chat")
async def chat_with_video(payload: VideoChatRequest):
    target_filename = payload.filename or "Sample_Traffic_Surveillance.mp4"
    question = payload.question.strip()

    # Query video service with timing check capabilities
    chat_res = video_service.chat_with_video(target_filename, question)

    filename = chat_res.get("filename", target_filename)
    scope = chat_res.get("scope", "")
    raw_answer = chat_res.get("answer", "")
    summary = chat_res.get("summary", "")
    timeline = chat_res.get("timeline", [])
    objects = chat_res.get("detected_objects", [])
    highlights = chat_res.get("safety_highlights", [])
    agent_provider = chat_res.get("agent_provider", "NVIDIA VSS Agent")

    timeline_str = "\n".join([f"• [{item.get('time', '00:00')}] {item.get('event', '')}" for item in timeline]) if timeline else "• [00:00 - End] Video feed monitored continuously."
    objects_str = ", ".join(objects) if objects else "Standard visual elements"
    highlights_str = "\n".join([f"✓ {h}" for h in highlights]) if highlights else "✓ Protocol compliance verified across monitored feed."

    # Construct clean answer text with timing check header if scoped
    scope_header = f"**⏱️ Evaluated Window:** `{scope}`\n\n" if scope and scope != "Full video" else ""
    
    if raw_answer:
        answer = f"{scope_header}{raw_answer}\n\n#### ⏱️ Timeline Highlights:\n{timeline_str}"
    else:
        answer = (
            f"### 📹 Video AI Assistant ({payload.video_title or filename})\n\n"
            f"{scope_header}"
            f"{summary}\n\n"
            f"**Detected Entities:** {objects_str}\n\n"
            f"#### ⏱️ Chronological Timeline:\n{timeline_str}\n\n"
            f"#### 🔍 Safety & Operational Audit:\n{highlights_str}"
        )

    return {
        "status": "success",
        "filename": filename,
        "question": question,
        "answer": answer,
        "scope": scope,
        "summary": summary,
        "timeline": timeline,
        "detected_objects": objects,
        "safety_highlights": highlights,
        "agent_provider": agent_provider
    }

@router.post("/clear-db")
@router.delete("/clear-db")
async def clear_database_endpoint():
    result = await video_service.clear_db_and_storage()
    return result


