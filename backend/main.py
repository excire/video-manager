from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import os
import random
from typing import List
from pathlib import Path
from pydantic import BaseModel

from database import engine, Base, get_db, Video, Tag, Playlist, Setting
import video_utils

# Create tables
Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ... (existing imports)

app = FastAPI(title="Local Video Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_VIDEO_DIR = "/videos"
DATA_DIR = os.getenv("DATA_DIR", "/backend/data")
THUMB_DIR = os.path.join(DATA_DIR, "thumbnails")
FRAME_DIR = os.path.join(DATA_DIR, "frames")
AI_TAGGING_ENABLED = os.getenv("AI_TAGGING_ENABLED", "1") == "1"

os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)

# Serve static files
app.mount("/static/thumbnails", StaticFiles(directory=THUMB_DIR), name="thumbnails")

class VideoDirUpdate(BaseModel):
    video_dir: str

def get_video_dir_setting(db: Session) -> str:
    setting = db.query(Setting).filter(Setting.key == "video_dir").first()
    if setting and setting.value:
        return setting.value
    return DEFAULT_VIDEO_DIR

def normalize_video_dir(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))

def run_ai_tagging(video_id: int):
    if not AI_TAGGING_ENABLED:
        return
    import ai_utils
    ai_utils.auto_tag_video(video_id, FRAME_DIR)

@app.get("/videos", response_model=None)
def list_videos(db: Session = Depends(get_db)):
    return db.query(Video).all()

@app.get("/settings/video-dir")
def get_video_dir(db: Session = Depends(get_db)):
    return {"video_dir": get_video_dir_setting(db)}

@app.put("/settings/video-dir")
def update_video_dir(payload: VideoDirUpdate, db: Session = Depends(get_db)):
    normalized = normalize_video_dir(payload.video_dir)
    if not os.path.isdir(normalized):
        raise HTTPException(status_code=400, detail="Video directory not found")

    setting = db.query(Setting).filter(Setting.key == "video_dir").first()
    if not setting:
        setting = Setting(key="video_dir", value=normalized)
        db.add(setting)
    else:
        setting.value = normalized
    db.commit()
    return {"video_dir": normalized}

@app.get("/videos/random")
def get_random_video(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    return random.choice(videos)

@app.post("/scan")
def scan_videos(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Scan VIDEO_DIR for video files
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    found_videos = []
    video_dir = get_video_dir_setting(db)
    
    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                full_path = os.path.join(root, file)
                
                # Check if already in DB
                existing = db.query(Video).filter(Video.path == full_path).first()
                if not existing:
                    new_video = Video(
                        path=full_path,
                        filename=file,
                        title=Path(file).stem,
                        rating=0
                    )
                    db.add(new_video)
                    db.commit()
                    db.refresh(new_video)
                    found_videos.append(new_video)
                    
                    # Process in background (thumbnails, duration)
                    background_tasks.add_task(process_video_metadata, new_video.id)
    
    return {"message": f"Started scanning. Found {len(found_videos)} new videos."}

def process_video_metadata(video_id: int):
    db = next(get_db())
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return
    
    duration = video_utils.get_video_duration(video.path)
    thumb_path = video_utils.create_thumbnail(video.path, THUMB_DIR)
    
    video.duration = duration
    video.thumbnail_path = thumb_path
    db.commit()
    
    # Run AI tagging
    run_ai_tagging(video_id)

@app.put("/videos/{video_id}/rate")
def rate_video(video_id: int, rating: int, db: Session = Depends(get_db)):
    if not (0 <= rating <= 10):
        raise HTTPException(status_code=400, detail="Rating must be 0-10")
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video.rating = rating
    db.commit()
    return {"message": "Rating updated", "rating": rating}

@app.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
