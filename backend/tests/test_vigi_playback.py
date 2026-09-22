import pytest
from datetime import datetime, timezone
from app.providers.vigi_provider import format_vigi_utc_timestamp, build_vigi_playback_url
from app.services.vigi_service import vigi_service

def test_format_vigi_utc_timestamp():
    # 1. ISO string with Z
    iso_z = "2026-08-28T04:30:00Z"
    assert format_vigi_utc_timestamp(iso_z) == "20260828t043000z"

    # 2. ISO string with space
    iso_space = "2026-08-28 04:30:00"
    assert format_vigi_utc_timestamp(iso_space) == "20260828t043000z"

    # 3. Already formatted VIGI string
    raw_vigi = "20260828t043000z"
    assert format_vigi_utc_timestamp(raw_vigi) == "20260828t043000z"

    # 4. Datetime object (UTC)
    dt = datetime(2026, 8, 28, 4, 30, 0, tzinfo=timezone.utc)
    assert format_vigi_utc_timestamp(dt) == "20260828t043000z"

    # 5. DD-MM-YYYY HH:mm:ss format (from UI date picker)
    dd_mm_yyyy = "20-09-2026 18:30:00"
    assert format_vigi_utc_timestamp(dd_mm_yyyy) == "20260920t183000z"

def test_build_vigi_playback_url():
    url = build_vigi_playback_url(
        channel="1",
        stream="1",
        start_time="2026-08-28 04:30:00",
        end_time="2026-08-28 05:00:00",
        host="127.0.0.1",
        port=8554,
        username="admin",
        password="Gt@102020"
    )

    expected = "rtsp://admin:Gt%40102020@127.0.0.1:8554/replay/1/1/avm?starttime=20260828t043000z&endtime=20260828t050000z"
    assert url == expected

def test_build_playback_url_with_vigi_channel_id():
    url = build_vigi_playback_url(
        channel="vigi-cam-02",
        stream="2",
        start_time="20260828t043000z",
        end_time="20260828t050000z",
        host="192.168.31.81",
        port=554,
        username="admin",
        password="password123"
    )

    assert "replay/2/2/avm" in url
    assert "starttime=20260828t043000z" in url
    assert "endtime=20260828t050000z" in url

def test_vigi_service_build_playback_url():
    url = vigi_service.build_playback_url(
        channel="1",
        stream="1",
        start_time="2026-08-28T04:30:00Z",
        end_time="2026-08-28T05:00:00Z"
    )
    assert "/replay/1/1/avm?starttime=20260828t043000z&endtime=20260828t050000z" in url
