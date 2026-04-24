"""
Extract a single "title card" frame from each film.

Heuristic: sample frames across the first ~5 seconds of each video, score each
by Canny edge density in the middle horizontal band (where title text tends to
sit), and keep the highest-scoring frame. Saves to public/titlecards/ as
<safe_name>.jpg.

Run after the frame-extraction script is already in place.
"""
import cv2
import numpy as np
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "public" / "titlecards"
BLACK_THRESHOLD = 20
BORDER_RATIO = 0.98

VIDEOS = [
    "american chud.mp4",
    "baking bad.mp4",
    "Bigger Things.mp4",
    "Bulk Fiction.mp4",
    "Chewlander.mp4",
    "Chiplash.mp4",
    "donnie lardo.mp4",
    "fat club.mp4",
    "fat runner.mp4",
    "fatsy driver.mp4",
    "Heavy Potter.mp4",
    "interbelly.mp4",
    "squid gain.mp4",
    "the bigs.mp4",
    "The Fatrix.mp4",
    "The Weight of Wallstreet.mp4",
]


def detect_crop(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    top = 0
    for y in range(h):
        if np.mean(gray[y, :] < BLACK_THRESHOLD) < BORDER_RATIO:
            top = y; break
    bottom = h
    for y in range(h - 1, -1, -1):
        if np.mean(gray[y, :] < BLACK_THRESHOLD) < BORDER_RATIO:
            bottom = y + 1; break
    left = 0
    for x in range(w):
        if np.mean(gray[:, x] < BLACK_THRESHOLD) < BORDER_RATIO:
            left = x; break
    right = w
    for x in range(w - 1, -1, -1):
        if np.mean(gray[:, x] < BLACK_THRESHOLD) < BORDER_RATIO:
            right = x + 1; break
    if (bottom - top) < h * 0.5: top, bottom = 0, h
    if (right - left) < w * 0.5: left, right = 0, w
    return frame[top:bottom, left:right]


def text_score(frame):
    """Higher = more likely to contain title text.

    Focus on the middle horizontal third where title cards sit, and compute
    edge density via Canny. Title cards are usually high-contrast lettering
    on a solid backdrop; dense edges in that band are a reliable proxy.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    band = gray[h // 3: (2 * h) // 3, :]
    edges = cv2.Canny(band, 80, 160)
    return edges.mean()


def pick_titlecard(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Sample densely across the first ~5 seconds (title cards live early).
    sample_times = [round(t, 2) for t in np.arange(0.5, 5.5, 0.5)]
    positions = [min(int(t * fps), total - 1) for t in sample_times]

    best_frame = None
    best_score = -1
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        cropped = detect_crop(frame)
        score = text_score(cropped)
        if score > best_score:
            best_score = score
            best_frame = cropped

    cap.release()
    return best_frame, best_score


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in VIDEOS:
        path = PROJECT_ROOT / name
        if not path.exists():
            print(f"  MISSING: {name}")
            continue
        result = pick_titlecard(path)
        if result is None or result[0] is None:
            print(f"  FAIL:    {name}")
            continue
        frame, score = result
        safe = os.path.splitext(name)[0].replace(" ", "_").replace(".", "_")
        out = OUTPUT_DIR / f"{safe}.jpg"
        cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"  OK:      {name}  ->  {out.name}  (score {score:.1f})")

    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
