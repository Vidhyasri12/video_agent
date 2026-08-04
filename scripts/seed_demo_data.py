import asyncio
import uuid
from datetime import datetime, timedelta
from app.db.session import AsyncSessionLocal, engine, Base
from app.db.models import Camera, Event, Caption, Summary, Alert
from app.services.embedding_service import embedding_service

async def seed_data():
    async with engine.begin() as conn:
        try:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as e:
            print(f"Extension note: {e}")
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("🌱 Seeding realistic CCTV intelligence demo data...")

        # 1. Cameras
        cams = [
            Camera(
                id="cam-gate-01",
                name="Main Entrance Gate 1",
                location="Perimeter North",
                rtsp_url="rtsp://admin:pass@192.168.1.101:554/live",
                status="online",
                fps=30
            ),
            Camera(
                id="cam-wh-dock-02",
                name="Warehouse Loading Dock B",
                location="Logistics Hub",
                rtsp_url="rtsp://admin:pass@192.168.1.102:554/live",
                status="online",
                fps=30
            ),
            Camera(
                id="cam-assembly-03",
                name="Assembly Floor Zone 3",
                location="Factory Hall A",
                rtsp_url="rtsp://admin:pass@192.168.1.103:554/live",
                status="online",
                fps=30
            ),
            Camera(
                id="cam-storage-04",
                name="Chemical Storage Room",
                location="Restricted Wing C",
                rtsp_url="rtsp://admin:pass@192.168.1.104:554/live",
                status="online",
                fps=30
            )
        ]
        for c in cams:
            await db.merge(c)

        # 2. Events & Real-time Alerts
        now = datetime.utcnow()

        events = [
            Event(
                id="evt-fall-01",
                camera_id="cam-wh-dock-02",
                timestamp=now - timedelta(minutes=15),
                event_type="fall_detected",
                severity="critical",
                description="Worker slipped and fell near wet floor area at Loading Dock B.",
                object_class="person",
                object_count=1,
                bbox=[420, 310, 780, 510],
                confidence=0.96,
                thumbnail_url="/static/thumbnails/sample_fall.jpg",
                clip_url="/static/videos/demo_fall.mp4"
            ),
            Event(
                id="evt-helmet-02",
                camera_id="cam-assembly-03",
                timestamp=now - timedelta(minutes=35),
                event_type="helmet_violation",
                severity="medium",
                description="Worker operating machinery without compulsory safety helmet.",
                object_class="person",
                object_count=1,
                bbox=[200, 150, 410, 600],
                confidence=0.92,
                thumbnail_url="/static/thumbnails/sample_helmet.jpg",
                clip_url="/static/videos/demo_helmet.mp4"
            ),
            Event(
                id="evt-forklift-03",
                camera_id="cam-wh-dock-02",
                timestamp=now - timedelta(minutes=50),
                event_type="near_miss",
                severity="high",
                description="Two forklifts crossed paths within 1.5m clearance zone while worker walked past.",
                object_class="forklift",
                object_count=2,
                bbox=[500, 400, 1100, 850],
                confidence=0.94,
                thumbnail_url="/static/thumbnails/sample_forklift.jpg",
                clip_url="/static/videos/demo_forklift.mp4"
            ),
            Event(
                id="evt-loiter-04",
                camera_id="cam-gate-01",
                timestamp=now - timedelta(hours=1, minutes=10),
                event_type="loitering",
                severity="medium",
                description="Individual loitering near restricted Gate 1 access door for over 3 minutes.",
                object_class="person",
                object_count=1,
                bbox=[150, 220, 310, 580],
                confidence=0.88,
                thumbnail_url="/static/thumbnails/sample_loiter.jpg",
                clip_url="/static/videos/demo_loiter.mp4"
            )
        ]

        for e in events:
            await db.merge(e)

        # 3. Alerts
        alerts = [
            Alert(
                id="alt-01",
                event_id="evt-fall-01",
                alert_type="fall_detected",
                severity="critical",
                status="triggered",
                message="CRITICAL: Worker slip/fall incident detected at Loading Dock B!",
                notification_sent=True
            ),
            Alert(
                id="alt-02",
                event_id="evt-forklift-03",
                alert_type="near_miss",
                severity="high",
                status="acknowledged",
                message="HIGH: Vehicle proximity violation near forklift loading ramp.",
                notification_sent=True
            )
        ]
        for a in alerts:
            await db.merge(a)

        # 4. VLM Captions with Vector Embeddings
        captions_raw = [
            ("cam-gate-01", "A person wearing a red jacket entered through Gate 1 carrying a black backpack at 14:02:11."),
            ("cam-wh-dock-02", "A worker in yellow vest slipped near loading dock floor while moving heavy inventory packages."),
            ("cam-assembly-03", "Two assembly operators inspected engine components while a forklift reversed behind them."),
            ("cam-storage-04", "Normal baseline monitoring in Chemical Storage Room. Zero unauthorized entries detected.")
        ]

        for cam_id, text_str in captions_raw:
            emb = embedding_service.generate_embedding(text_str)
            cap = Caption(
                id=str(uuid.uuid4()),
                camera_id=cam_id,
                timestamp=now - timedelta(minutes=20),
                duration_start=0.0,
                duration_end=10.0,
                raw_text=text_str,
                embedding=emb
            )
            db.add(cap)

        await db.commit()
        print("✅ Demo dataset seeded successfully with vector embeddings & alerts!")

if __name__ == "__main__":
    asyncio.run(seed_data())
