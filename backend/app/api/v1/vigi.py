import time
from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.services.vigi_service import vigi_service
from app.services.vigi_cloud_service import vigi_cloud_service
from app.providers.provider_factory import ProviderFactory
from app.core.exceptions import VmsException

router = APIRouter()

# ── Pydantic Request Models ────────────────────────────────────────────────

class VigiConnectRequest(BaseModel):
    vigi_host: Optional[str] = "192.168.31.81"
    port: Optional[int] = 554
    username: Optional[str] = "admin"
    password: Optional[str] = ""
    rtsp_url: Optional[str] = None
    provider: Optional[str] = None

class VigiSummarizeRequest(BaseModel):
    channel_id: Optional[str] = None
    rtsp_url: Optional[str] = None
    vigi_host: Optional[str] = None
    username: Optional[str] = "admin"
    password: Optional[str] = ""
    duration_seconds: Optional[int] = 15

class VigiConfigUpdateRequest(BaseModel):
    vigi_host: Optional[str] = None
    vigi_rtsp_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_type: Optional[str] = None
    provider: Optional[str] = None

class VigiEdgeReconnectRequest(BaseModel):
    channel_id: str

class VigiEdgeForwardEventRequest(BaseModel):
    channel_id: str
    event_type: str = "motion_detection"
    confidence: Optional[float] = 0.95
    snapshot_url: Optional[str] = None
    clip_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class VigiOpenApiSubscribeRequest(BaseModel):
    webhook_url: str
    event_types: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None

class VigiCloudAuthRequest(BaseModel):
    client_id: Optional[str] = "vigi_app_client_883"
    client_secret: Optional[str] = ""
    cloud_org_id: Optional[str] = "org-vigi-global-883"

class VigiCloudTicketRequest(BaseModel):
    device_id: str

class VigiCloudWebhookPayload(BaseModel):
    event_id: Optional[str] = None
    device_id: Optional[str] = "vigi-cloud-cam-01"
    event_type: Optional[str] = "motion_detection"
    timestamp: Optional[str] = None
    snapshot_url: Optional[str] = None

class VigiCloudSummarizeRequest(BaseModel):
    device_id: Optional[str] = "vigi-cloud-cam-01"
    duration_seconds: Optional[int] = 15

class VigiPlaybackUrlRequest(BaseModel):
    channel_id: Optional[str] = "1"
    stream_id: Optional[str] = "1"
    start_time: str
    end_time: str
    host: Optional[str] = None
    port: Optional[int] = 8554
    username: Optional[str] = "admin"
    password: Optional[str] = ""

class VigiPlaybackSummarizeRequest(BaseModel):
    channel_id: Optional[str] = "1"
    start_time: str
    end_time: str
    duration_seconds: Optional[int] = 15
    rtsp_url: Optional[str] = None
    host: Optional[str] = None
    username: Optional[str] = "admin"
    password: Optional[str] = ""



# ── Core Production Endpoints ──────────────────────────────────────────────

@router.get("/capabilities")
async def get_vigi_capabilities(provider: Optional[str] = Query(None)):
    capabilities = vigi_service.get_capabilities(provider_name=provider)
    active_provider = vigi_service.get_active_provider(provider_name=provider)
    return {
        "status": "success",
        "provider": active_provider.provider_type,
        "provider_name": active_provider.display_name,
        "capabilities": capabilities,
        "supported_providers": ProviderFactory.list_supported_providers()
    }

@router.get("/health")
async def get_vigi_health(provider: Optional[str] = Query(None)):
    return vigi_service.get_health(provider_name=provider)

@router.get("/stream")
async def stream_vigi_live(
    channel_id: Optional[str] = Query(None),
    rtsp_url: Optional[str] = Query(None),
    provider: Optional[str] = Query(None)
):
    return StreamingResponse(
        vigi_service.generate_mjpeg_stream(channel_id=channel_id, rtsp_url=rtsp_url, provider_name=provider),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/playback/url")
async def get_vigi_playback_url(req: VigiPlaybackUrlRequest = Body(...)):
    """Constructs and returns VIGI RTSP Replay URL with UTC timestamps."""
    url = vigi_service.build_playback_url(
        channel=req.channel_id or "1",
        stream=req.stream_id or "1",
        start_time=req.start_time,
        end_time=req.end_time,
        host=req.host,
        port=req.port or 8554,
        username=req.username or "",
        password=req.password or ""
    )
    from app.providers.vigi_provider import format_vigi_utc_timestamp
    return {
        "status": "success",
        "rtsp_url": url,
        "channel_id": req.channel_id,
        "stream_id": req.stream_id,
        "start_time_utc": format_vigi_utc_timestamp(req.start_time),
        "end_time_utc": format_vigi_utc_timestamp(req.end_time),
        "formatted_pattern": "rtsp://<IP>/replay/<channel>/<stream>/avm?starttime=<START>&endtime=<END>"
    }

@router.get("/playback/stream")
async def stream_vigi_playback(
    channel_id: Optional[str] = Query("1"),
    start_time: str = Query(""),
    end_time: str = Query(""),
    stream_id: str = Query("1"),
    rtsp_url: Optional[str] = Query(None),
    provider: Optional[str] = Query(None)
):
    """Streams MJPEG feed for historical video playback."""
    return StreamingResponse(
        vigi_service.generate_playback_mjpeg_stream(
            channel_id=channel_id,
            start_time=start_time,
            end_time=end_time,
            stream_id=stream_id,
            rtsp_url=rtsp_url,
            provider_name=provider
        ),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/playback/summarize")
async def summarize_vigi_playback(req: VigiPlaybackSummarizeRequest = Body(...), provider: Optional[str] = Query(None)):
    """Runs AI summarization on historical playback stream."""
    try:
        res = vigi_service.summarize_playback_stream(
            channel_id=req.channel_id,
            start_time=req.start_time,
            end_time=req.end_time,
            duration_seconds=req.duration_seconds or 15,
            rtsp_url=req.rtsp_url,
            provider_name=provider
        )
        return {"status": "success", "summary": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playback AI Summarization error: {str(e)}")


from app.services.stream_hub import stream_hub
from fastapi.responses import Response

@router.get("/snapshot")
def get_vigi_snapshot(
    channel_id: Optional[str] = Query(None),
    rtsp_url: Optional[str] = Query(None),
    provider: Optional[str] = Query(None)
):
    """Returns the latest single JPEG snapshot frame from StreamHub without holding long-lived HTTP connections."""
    active_prov = vigi_service.get_active_provider(provider)
    ch_info = getattr(active_prov, "channels", {}).get(channel_id) if channel_id else None
    target_rtsp = rtsp_url or (ch_info.get("rtsp_url") if ch_info else None) or os.environ.get("VIGI_VMS_RTSP_URL", "")
    channel_name = ch_info.get("name", "TP-Link VIGI Feed") if ch_info else "VIGI RTSP Stream"
    sub_rtsp = ch_info.get("sub_rtsp_url") if ch_info else None
    cid = channel_id or "default-channel"

    worker = stream_hub.get_or_create_worker(cid, channel_name, target_rtsp, sub_rtsp)
    jpeg = worker.latest_jpeg or worker.generate_status_frame("CONNECTING...")
    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

from app.services.tunnel_service import tunnel_service

@router.get("/tunnel/status")
def get_tunnel_status():
    """Returns status of the Cloudflare TCP Tunnel supervisor."""
    return tunnel_service.get_status()

@router.post("/tunnel/restart")
def restart_tunnel():
    """Manually triggers tunnel restart."""
    tunnel_service.stop_supervisor()
    time.sleep(0.5)
    tunnel_service.start_supervisor()
    return tunnel_service.get_status()

@router.get("/config")
async def get_vigi_config():
    return vigi_service.get_vigi_config()

@router.post("/update-config")
async def update_vigi_config(req: VigiConfigUpdateRequest = Body(...)):
    return vigi_service.update_vigi_config(
        vigi_host=req.vigi_host,
        vigi_rtsp_url=req.vigi_rtsp_url,
        username=req.username,
        password=req.password,
        connection_type=req.connection_type,
        provider=req.provider
    )

@router.get("/discover")
async def discover_vigi_devices(provider: Optional[str] = Query(None)):
    devices = vigi_service.discover_network_devices(provider_name=provider)
    return {
        "status": "success",
        "count": len(devices),
        "devices": devices
    }

@router.get("/channels")
async def get_vigi_channels(provider: Optional[str] = Query(None)):
    channels = vigi_service.get_channels(provider_name=provider)
    config = vigi_service.get_vigi_config()
    return {
        "status": "success",
        "count": len(channels),
        "channels": channels,
        "vigi_rtsp_url": config.get("vigi_rtsp_url")
    }

@router.post("/connect")
def connect_vigi(req: VigiConnectRequest = Body(...)):
    # Update active VIGI config with incoming host, RTSP URL, and credentials
    vigi_service.update_vigi_config(
        vigi_host=req.vigi_host,
        vigi_rtsp_url=req.rtsp_url,
        username=req.username,
        password=req.password,
        provider=req.provider
    )
    result = vigi_service.test_connection(
        vigi_host=req.vigi_host,
        port=req.port or 554,
        username=req.username or "admin",
        password=req.password or "",
        rtsp_url=req.rtsp_url or "",
        provider_name=req.provider
    )
    return result

@router.post("/summarize")
def summarize_vigi_stream(req: VigiSummarizeRequest = Body(...)):
    summary_result = vigi_service.summarize_vigi_stream(
        channel_id=req.channel_id,
        rtsp_url=req.rtsp_url,
        duration_seconds=req.duration_seconds or 15,
        vigi_host=req.vigi_host,
        username=req.username or "admin",
        password=req.password or ""
    )
    return {
        "status": "success",
        "summary": summary_result.get("summary", ""),
        "description": summary_result,
        "vigi_metadata": summary_result.get("vigi_metadata", {})
    }

# ── VIGI Edge Connector Endpoints ──────────────────────────────────────────

@router.get("/edge/status")
async def get_edge_status():
    return vigi_service.get_edge_health()

@router.get("/edge/discover")
async def discover_edge_cameras():
    return vigi_service.discover_edge_cameras()

@router.post("/edge/reconnect")
async def reconnect_edge_stream(req: VigiEdgeReconnectRequest = Body(...)):
    return vigi_service.reconnect_edge_stream(req.channel_id)

@router.post("/edge/forward-event")
async def forward_edge_event(req: VigiEdgeForwardEventRequest = Body(...)):
    return vigi_service.forward_edge_event(
        channel_id=req.channel_id,
        event_type=req.event_type,
        confidence=req.confidence or 0.95,
        snapshot_url=req.snapshot_url,
        clip_url=req.clip_url,
        metadata=req.metadata
    )

@router.get("/edge/forwarded-events")
async def get_edge_forwarded_events(limit: int = Query(20)):
    return {
        "status": "success",
        "count": len(vigi_service.get_forwarded_events_log(limit)),
        "events": vigi_service.get_forwarded_events_log(limit)
    }

# ── VIGI OpenAPI Integration Endpoints ─────────────────────────────────────

@router.get("/openapi/devices")
async def get_openapi_devices():
    devices = vigi_service.get_openapi_devices()
    return {
        "status": "success",
        "count": len(devices),
        "devices": devices
    }

@router.get("/openapi/config/{device_id}")
async def get_openapi_device_config(device_id: str):
    return vigi_service.get_openapi_device_config(device_id)

@router.post("/openapi/config/{device_id}")
async def update_openapi_device_config(device_id: str, updates: Dict[str, Any] = Body(...)):
    return vigi_service.update_openapi_device_config(device_id, updates)

@router.post("/openapi/subscribe")
async def subscribe_openapi_events(req: VigiOpenApiSubscribeRequest = Body(...)):
    return vigi_service.subscribe_openapi_events(
        webhook_url=req.webhook_url,
        event_types=req.event_types,
        device_ids=req.device_ids
    )

# ── TP-Link VIGI Cloud VMS Endpoints (Experimental - Feature Flag Protected)

@router.post("/cloud/auth")
async def authenticate_vigi_cloud(req: VigiCloudAuthRequest = Body(...)):
    return vigi_cloud_service.authenticate_cloud(
        client_id=req.client_id,
        client_secret=req.client_secret,
        org_id=req.cloud_org_id
    )

@router.get("/cloud/devices")
async def get_vigi_cloud_devices():
    devices = vigi_cloud_service.get_cloud_devices()
    return {
        "status": "success",
        "count": len(devices),
        "devices": devices
    }

@router.post("/cloud/stream-ticket")
async def get_vigi_cloud_stream_ticket(req: VigiCloudTicketRequest = Body(...)):
    return vigi_cloud_service.get_stream_ticket(device_id=req.device_id)

@router.post("/cloud/webhook")
async def receive_vigi_cloud_webhook(payload: VigiCloudWebhookPayload = Body(...)):
    return vigi_cloud_service.process_cloud_webhook(payload.model_dump() if hasattr(payload, "model_dump") else payload.dict())

@router.get("/cloud/webhooks")
async def get_vigi_cloud_webhooks():
    return {
        "status": "success",
        "history": vigi_cloud_service.get_webhook_history()
    }

@router.get("/cloud/stream")
async def stream_vigi_cloud_live(device_id: Optional[str] = Query("vigi-cloud-cam-01")):
    vigi_cloud_service._check_feature_flag()
    return StreamingResponse(
        vigi_cloud_service.generate_cloud_mjpeg_stream(device_id=device_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/cloud/summarize")
async def summarize_vigi_cloud_stream(req: VigiCloudSummarizeRequest = Body(...)):
    summary_result = vigi_cloud_service.summarize_cloud_stream(
        device_id=req.device_id,
        duration_seconds=req.duration_seconds or 15
    )
    return {
        "status": "success",
        "summary": summary_result.get("summary", ""),
        "description": summary_result,
        "vigi_metadata": summary_result.get("vigi_metadata", {})
    }

@router.get("/cloud/status")
async def get_vigi_cloud_status():
    return vigi_cloud_service.get_cloud_status()
