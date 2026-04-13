import cv2
import os
import random
import numpy as np

VIDEO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(VIDEO_DIR, "public", "frames")
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
FRAMES_PER_VIDEO = 10
BLACK_THRESHOLD = 20  # pixel value below this is considered "black"
BORDER_RATIO = 0.98    # fraction of row/col that must be black to count as letterbox

os.makedirs(OUTPUT_DIR, exist_ok=True)

def detect_crop(frame):
    """Detect and remove black letterbox borders."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Find top crop
    top = 0
    for y in range(h):
        if np.mean(gray[y, :] < BLACK_THRESHOLD) < BORDER_RATIO:
            top = y
            break

    # Find bottom crop
    bottom = h
    for y in range(h - 1, -1, -1):
        if np.mean(gray[y, :] < BLACK_THRESHOLD) < BORDER_RATIO:
            bottom = y + 1
            break

    # Find left crop
    left = 0
    for x in range(w):
        if np.mean(gray[:, x] < BLACK_THRESHOLD) < BORDER_RATIO:
            left = x
            break

    # Find right crop
    right = w
    for x in range(w - 1, -1, -1):
        if np.mean(gray[:, x] < BLACK_THRESHOLD) < BORDER_RATIO:
            right = x + 1
            break

    # Safety: don't crop too aggressively (keep at least 50% of frame)
    if (bottom - top) < h * 0.5:
        top, bottom = 0, h
    if (right - left) < w * 0.5:
        left, right = 0, w

    return frame[top:bottom, left:right]

def extract_frames(video_path, video_name):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  ERROR: Cannot open {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < FRAMES_PER_VIDEO:
        print(f"  WARN: {video_name} only has {total_frames} frames")
        return []

    # Pick random frame positions, avoiding first/last 5%
    margin = int(total_frames * 0.05)
    positions = sorted(random.sample(range(margin, total_frames - margin), FRAMES_PER_VIDEO))

    saved = []
    safe_name = video_name.replace(" ", "_").replace(".", "_")

    for i, pos in enumerate(positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue

        cropped = detect_crop(frame)
        filename = f"{safe_name}_{i:02d}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(filepath, cropped, [cv2.IMWRITE_JPEG_QUALITY, 85])
        saved.append(filename)

    cap.release()
    return saved

if __name__ == "__main__":
    all_frames = []
    videos = [f for f in os.listdir(VIDEO_DIR)
              if os.path.splitext(f)[1].lower() in VIDEO_EXTS]

    print(f"Found {len(videos)} videos")
    for v in sorted(videos):
        print(f"Processing: {v}")
        frames = extract_frames(os.path.join(VIDEO_DIR, v), os.path.splitext(v)[0])
        print(f"  Extracted {len(frames)} frames")
        all_frames.extend(frames)

    # Write manifest for the website
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    import json
    with open(manifest_path, "w") as f:
        json.dump(all_frames, f)

    print(f"\nDone! {len(all_frames)} total frames saved to {OUTPUT_DIR}")
    print(f"Manifest written to {manifest_path}")
