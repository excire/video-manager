import ffmpeg
import os
import subprocess
from pathlib import Path

def get_video_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        return float(video_stream['duration'])
    except Exception as e:
        print(f"Error probing {file_path}: {e}")
        return 0

def create_thumbnail(video_path, output_dir, time_offset=1.0):
    video_path = Path(video_path)
    output_path = Path(output_dir) / f"{video_path.stem}_thumb.jpg"
    
    if output_path.exists():
        return str(output_path)

    try:
        (
            ffmpeg
            .input(str(video_path), ss=time_offset)
            .filter('scale', 480, -1)
            .output(str(output_path), vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return str(output_path)
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return None
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

def extract_frames_for_ai(video_path, output_dir, num_frames=3):
    duration = get_video_duration(video_path)
    if duration == 0:
        return []
    
    frame_paths = []
    offsets = [duration * i / (num_frames + 1) for i in range(1, num_frames + 1)]
    
    for i, offset in enumerate(offsets):
        output_path = Path(output_dir) / f"{Path(video_path).stem}_frame_{i}.jpg"
        try:
            (
                ffmpeg
                .input(str(video_path), ss=offset)
                .filter('scale', 224, 224) # Standard size for many AI models
                .output(str(output_path), vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            frame_paths.append(str(output_path))
        except Exception as e:
            print(f"Error extracting frame at {offset}: {e}")
            
    return frame_paths
