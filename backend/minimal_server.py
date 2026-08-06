#!/usr/bin/env python
"""Minimal FastAPI server for testing"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="AI CCTV Video Intelligence & Summarization System",
    description="Minimal test server",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI CCTV Backend is running!", "status": "ok"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI CCTV Video Intelligence System",
        "version": "0.1.0"
    }

@app.get("/api/v1/videos")
async def list_videos():
    """List videos endpoint"""
    return {
        "videos": [],
        "total": 0
    }

@app.post("/api/v1/upload")
async def upload_video():
    """Video upload endpoint"""
    return {"status": "upload endpoint ready"}

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(
        "minimal_server:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
