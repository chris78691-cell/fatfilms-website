"""
Extract a single "title card" frame from each film.

Heuristic:
- Sample every 0.25s across the first 10s and last 10s of each video (title
  cards sit either at the intro or the end credits).
- Score each frame by Canny edge density in the middle horizontal band plus
  a bonus for high-contrast luminance (bright text on dark / dark on bright).
- Keep the frame with the best score.

Crucially, we do NOT auto-crop black borders here — title cards are often
white text on a black backdrop, and the border detector in extract_frames.py
was eating the text. Save the raw frame instead.

Optional MANUAL_OVERRIDES at the bottom lets you pin specific timestamps
when the heuristic picks the wrong frame for a particular film.

Usage:
    python extract_titlecards.py
"""
import cv2
import numpy as np
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "public" / "titlecards"

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

# {filename: timestamp_seconds} — hardcoded when the heuristic picks wrong.
MANUAL_OVERRIDES: dict[str, float] = {}


def score_frame(frame: np.ndarray) -> float:
    """Higher = more likely to contain title text.

    Combines edge density in the middle horizontal band (text sits there) with
    a lightweight "strong contrast" signal from luminance standard deviation in
    the same band. Title cards tend to be high-contrast text on solid backgrounds.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Wider band: middle 60 % of the height catches text that's not perfectly centered.
    y0, y1 = int(h * 0.2), int(h * 0.8)
    band = gray[y0:y1, :]
    edges = cv2.Canny(band, 80, 160)
    edge_score = float(edges.mean())
    contrast_score = float(band.std()) / 4.0  # normalise
    return edge_score + contrast_score


def extract_at(cap, pos: int):
    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
    ret, frame = cap.read()
    return frame if ret else None


def pick_titlecard(video_path: Path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if fps > 0 else 0

    # Manual override wins.
    ov = MANUAL_OVERRIDES.get(video_path.name)
    if ov is not None:
        frame = extract_at(cap, int(ov * fps))
        cap.release()
        return (frame, float("inf")) if frame is not None else None

    # Sample every 0.25s across the first 10 s and last 10 s.
    early = [t for t in np.arange(0.0, min(10.0, duration), 0.25)]
    late = [t for t in np.arange(max(duration - 10.0, 0.0), duration, 0.25)]
    times = sorted(set(early + late))
    positions = [min(int(t * fps), total - 1) for t in times]

    best_frame, best_score = None, -1.0
    for pos in positions:
        frame = extract_at(cap, pos)
        if frame is None:
            continue
        s = score_frame(frame)
        if s > best_score:
            best_score = s
            best_frame = frame

    cap.release()
    return (best_frame, best_score) if best_frame is not None else None


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in VIDEOS:
        path = PROJECT_ROOT / name
        if not path.exists():
            print(f"  MISSING:  {name}")
            continue
        result = pick_titlecard(path)
        if result is None or result[0] is None:
            print(f"  FAIL:     {name}")
            continue
        frame, score = result
        safe = os.path.splitext(name)[0].replace(" ", "_").replace(".", "_")
        out = OUTPUT_DIR / f"{safe}.jpg"
        cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, 88])
        tag = "override" if score == float("inf") else f"score {score:.1f}"
        print(f"  OK:       {name}  ->  {out.name}  ({tag})")
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
