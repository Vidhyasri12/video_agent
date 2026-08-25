import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base
from app.core.exceptions import VmsException
from app.core.logging_config import setup_structured_logging

# Initialize structured logging with credential redaction
setup_structured_logging(logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global VMS Exception Handler
@app.exception_handler(VmsException)
async def vms_exception_handler(request: Request, exc: VmsException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directories exist
os.makedirs("./storage/videos", exist_ok=True)
os.makedirs("./storage/thumbnails", exist_ok=True)

# Mount static media directories
app.mount("/static", StaticFiles(directory="./storage"), name="static")

from sqlalchemy import text

from app.services.tunnel_service import tunnel_service

@app.on_event("startup")
async def startup_event():
    # Start Cloudflare Tunnel supervisor & auto-healer
    try:
        tunnel_service.start_supervisor()
    except Exception as e:
        print(f"Notice: Tunnel supervisor start error: {e}")

    if engine is not None:
        import asyncio
        try:
            async def _init_db():
                async with engine.begin() as conn:
                    try:
                        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    except Exception as ex:
                        print(f"Extension vector notice: {ex}")
                    await conn.run_sync(Base.metadata.create_all)
            await asyncio.wait_for(_init_db(), timeout=1.5)
        except Exception as e:
            print(f"Notice: Database startup skipped ({e}). Operating in standalone mode.")

@app.get("/")
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
