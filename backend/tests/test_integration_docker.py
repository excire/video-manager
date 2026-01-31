"""
Integration tests against a running Docker backend.
Run after: docker-compose -f docker-compose.integration.yml up -d
"""
import os
import time
import pytest
import httpx

pytestmark = pytest.mark.integration

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def wait_for_api(timeout: float = 30, interval: float = 0.5) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            r = httpx.get(f"{API_BASE}/settings/video-dir", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


@pytest.fixture(scope="module")
def api_ready():
    if not wait_for_api():
        pytest.skip("Backend API not available (start with docker-compose.integration.yml)")
    yield


def test_settings_video_dir_default(api_ready):
    r = httpx.get(f"{API_BASE}/settings/video-dir")
    assert r.status_code == 200
    data = r.json()
    assert "video_dir" in data
    assert data["video_dir"] == "/videos"


def test_videos_empty_initially(api_ready):
    r = httpx.get(f"{API_BASE}/videos")
    assert r.status_code == 200
    assert r.json() == []


def test_scan_discovers_videos(api_ready):
    r = httpx.post(f"{API_BASE}/scan")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "Found" in data["message"]


def test_videos_after_scan(api_ready):
    time.sleep(3)  # Allow background thumbnail processing
    r = httpx.get(f"{API_BASE}/videos")
    assert r.status_code == 200
    videos = r.json()
    assert len(videos) >= 1
    v = next((x for x in videos if x.get("filename") == "sample.mp4"), None)
    assert v is not None
    assert v.get("duration") is not None and v["duration"] > 0
    assert v.get("thumbnail_path") is not None


def test_rate_video(api_ready):
    r = httpx.get(f"{API_BASE}/videos")
    assert r.status_code == 200
    videos = r.json()
    assert len(videos) >= 1
    vid = videos[0]["id"]

    r = httpx.put(f"{API_BASE}/videos/{vid}/rate", params={"rating": 8})
    assert r.status_code == 200
    assert r.json()["rating"] == 8


def test_random_video(api_ready):
    r = httpx.get(f"{API_BASE}/videos/random")
    assert r.status_code == 200
    data = r.json()
    assert "title" in data
    assert "path" in data


def test_video_dir_update(api_ready):
    r = httpx.put(f"{API_BASE}/settings/video-dir", json={"video_dir": "/nonexistent"})
    assert r.status_code == 400

    r = httpx.put(f"{API_BASE}/settings/video-dir", json={"video_dir": "/videos"})
    assert r.status_code == 200
    assert r.json()["video_dir"] == "/videos"
