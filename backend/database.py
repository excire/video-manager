from sqlalchemy import create_engine, Column, Integer, String, Float, Table, ForeignKey, Text
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/videos.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

video_tag = Table(
    "video_tag",
    Base.metadata,
    Column("video_id", Integer, ForeignKey("videos.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True)
    filename = Column(String)
    title = Column(String)
    rating = Column(Integer, default=0) # 0-10
    thumbnail_path = Column(String)
    duration = Column(Float)
    
    tags = relationship("Tag", secondary=video_tag, back_populates="videos")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    videos = relationship("Video", secondary=video_tag, back_populates="tags")

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    video_ids = Column(Text) # Stored as comma-separated string or JSON

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
