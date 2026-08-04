from fastapi import APIRouter
from app.api.v1 import video, summaries, vigi

api_router = APIRouter()
api_router.include_router(video.router, prefix="/video", tags=["video"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(vigi.router, prefix="/vigi", tags=["vigi"])


