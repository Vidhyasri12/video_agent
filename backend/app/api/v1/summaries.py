from fastapi import APIRouter
from datetime import datetime, timedelta
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import summary_service

router = APIRouter()

@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(req: SummaryRequest):
    now = datetime.utcnow()
    start = req.start_time or (now - timedelta(hours=1))
    end = req.end_time or now

    res = summary_service.generate_summary_for_events([], start, end)

    return SummaryResponse(
        id="sum-" + now.strftime("%Y%m%d%H%M%S"),
        camera_id=req.camera_id,
        timeframe_type=req.timeframe_type,
        start_time=start,
        end_time=end,
        summary_text=res["summary_text"],
        metrics_json=res["metrics"],
        created_at=now
    )

