"""
Settings API — runtime configuration for NVIDIA VSS Agent and other system parameters.
Allows setting the NVIDIA_API_KEY dynamically without restarting the server.
"""
import os
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.vss_agent_service import vss_agent

router = APIRouter()
logger = logging.getLogger(__name__)


class NvidiaKeyRequest(BaseModel):
    api_key: str
    model: Optional[str] = None


@router.post("/nvidia")
async def set_nvidia_key(payload: NvidiaKeyRequest):
    """
    Dynamically configure the NVIDIA NIM API key at runtime.
    Sets os.environ so vss_agent picks it up immediately on the next call.
    Optionally also sets the model.
    """
    api_key = payload.api_key.strip()
    if api_key:
        os.environ["NVIDIA_API_KEY"] = api_key
        vss_agent.api_key = api_key
        logger.info("NVIDIA_API_KEY configured via settings API (key set, not logged).")

    if payload.model:
        os.environ["NVIDIA_VSS_MODEL"] = payload.model.strip()
        vss_agent.model = payload.model.strip()

    configured = bool(vss_agent.get_api_key())
    return {
        "status": "success",
        "nvidia_api_configured": configured,
        "model": vss_agent.get_model(),
        "vss_url": vss_agent.get_vss_url(),
        "message": "NVIDIA API key configured. Vision summarization is now active." if configured else "Key cleared. Using local VSS analyzer."
    }


@router.get("/status")
async def get_settings_status():
    """
    Returns current configuration status: whether NVIDIA API key is set,
    which model is in use, etc.
    """
    api_key = vss_agent.get_api_key()
    configured = bool(api_key)
    # Show only last 4 chars for security
    key_preview = f"...{api_key[-4:]}" if configured and len(api_key) >= 4 else None

    return {
        "nvidia_api_configured": configured,
        "nvidia_key_preview": key_preview,
        "model": vss_agent.get_model(),
        "vss_url": vss_agent.get_vss_url(),
        "mode": "NVIDIA NIM Vision API" if configured else "Local Motion Analyzer (No API Key)",
        "description": (
            "Using NVIDIA NIM multimodal vision model to analyze actual video content."
            if configured else
            "No NVIDIA API key set. Using local OpenCV frame analysis (motion/brightness only). "
            "Set your NVIDIA API key in Settings to enable real AI vision summarization."
        )
    }
