from pathlib import Path


def test_video_dir_setting(app_client, tmp_path):
    client, _, main = app_client

    res = client.get("/settings/video-dir")
    assert res.status_code == 200
    assert res.json()["video_dir"] == main.DEFAULT_VIDEO_DIR

    res = client.put("/settings/video-dir", json={"video_dir": str(tmp_path / "missing")})
    assert res.status_code == 400

    valid_dir = tmp_path / "videos"
    valid_dir.mkdir()
    res = client.put("/settings/video-dir", json={"video_dir": str(valid_dir)})
    assert res.status_code == 200
    assert res.json()["video_dir"] == str(valid_dir.resolve())

    res = client.get("/settings/video-dir")
    assert res.json()["video_dir"] == str(valid_dir.resolve())


def test_scan_adds_videos(app_client, tmp_path, monkeypatch):
    client, database, main = app_client

    video_dir = tmp_path / "scan_videos"
    video_dir.mkdir()
    (video_dir / "sample.mp4").write_bytes(b"fake")

    client.put("/settings/video-dir", json={"video_dir": str(video_dir)})

    monkeypatch.setattr(main, "process_video_metadata", lambda video_id: None)

    res = client.post("/scan")
    assert res.status_code == 200

    db = database.SessionLocal()
    try:
        videos = db.query(database.Video).all()
        assert len(videos) == 1
        assert videos[0].filename == "sample.mp4"
    finally:
        db.close()


def test_process_video_metadata_updates_thumbnail_and_duration(app_client, tmp_path, monkeypatch):
    _, database, main = app_client

    video_dir = tmp_path / "metadata_videos"
    video_dir.mkdir()
    video_path = video_dir / "clip.mp4"
    video_path.write_bytes(b"fake")

    db = database.SessionLocal()
    try:
        video = database.Video(
            path=str(video_path),
            filename="clip.mp4",
            title="clip",
            rating=0,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        video_id = video.id
    finally:
        db.close()

    monkeypatch.setattr(main.video_utils, "get_video_duration", lambda _: 12.5)
    monkeypatch.setattr(main.video_utils, "create_thumbnail", lambda *_: str(tmp_path / "thumb.jpg"))

    main.process_video_metadata(video_id)

    db = database.SessionLocal()
    try:
        updated = db.query(database.Video).filter(database.Video.id == video_id).first()
        assert updated.duration == 12.5
        assert updated.thumbnail_path == str(tmp_path / "thumb.jpg")
    finally:
        db.close()


def test_rate_and_random_video(app_client, tmp_path):
    client, database, _ = app_client

    res = client.get("/videos/random")
    assert res.status_code == 404

    db = database.SessionLocal()
    try:
        video = database.Video(
            path=str(tmp_path / "rate.mp4"),
            filename="rate.mp4",
            title="Rate Test",
            rating=0,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        video_id = video.id
    finally:
        db.close()

    res = client.put(f"/videos/{video_id}/rate", params={"rating": 7})
    assert res.status_code == 200

    db = database.SessionLocal()
    try:
        updated = db.query(database.Video).filter(database.Video.id == video_id).first()
        assert updated.rating == 7
    finally:
        db.close()

    res = client.get("/videos/random")
    assert res.status_code == 200
    assert res.json()["title"] == "Rate Test"


def test_list_tags(app_client):
    client, database, _ = app_client

    db = database.SessionLocal()
    try:
        video = database.Video(path="x", filename="x.mp4", title="x", rating=0)
        tag = database.Tag(name="demo")
        video.tags.append(tag)
        db.add(video)
        db.commit()
    finally:
        db.close()

    res = client.get("/tags")
    assert res.status_code == 200
    tags = res.json()
    assert any(t["name"] == "demo" for t in tags)
