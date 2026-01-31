import torch
import clip
from PIL import Image
import os
from database import SessionLocal, Video, Tag

# Load model once
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# candidate_tags = ["indoor", "outdoor", "person", "crowd", "nature", "city", "action", "speech", "music", "animation"]
# In a real app, you might want a more comprehensive list or dynamically generate them.
DEFAULT_CANDIDATE_TAGS = ["indoor", "outdoor", "person", "landscape", "urban", "nature", "close-up", "group", "action"]

def suggest_tags(image_paths, candidate_tags=DEFAULT_CANDIDATE_TAGS):
    if not image_paths:
        return []
    
    images = []
    for path in image_paths:
        try:
            image = preprocess(Image.open(path)).unsqueeze(0).to(device)
            images.append(image)
        except Exception as e:
            print(f"Error processing {path}: {e}")
    
    if not images:
        return []
        
    image_input = torch.cat(images)
    text_input = clip.tokenize(candidate_tags).to(device)
    
    with torch.no_grad():
        logits_per_image, logits_per_text = model(image_input, text_input)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
    
    # Average probabilities across frames
    avg_probs = probs.mean(axis=0)
    
    # Get tags with prob > threshold
    threshold = 0.2
    suggested = [candidate_tags[i] for i, prob in enumerate(avg_probs) if prob > threshold]
    
    return suggested

def auto_tag_video(video_id: int, frame_dir: str):
    import video_utils
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return
            
        frames = video_utils.extract_frames_for_ai(video.path, frame_dir)
        tags = suggest_tags(frames)
        
        for tag_name in tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            
            if tag not in video.tags:
                video.tags.append(tag)
        
        db.commit()
        
        # Cleanup frames
        for f in frames:
            try:
                os.remove(f)
            except:
                pass
    finally:
        db.close()
