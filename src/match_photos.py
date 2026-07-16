"""Match exported meal photos to meal_ids by capture timestamp.

Drop photos (any filenames; HEIC/JPG/PNG) into data/photos_raw/. Each
photo's capture time is matched against meal_start in meal_dataset.parquet;
matches within TOLERANCE_MIN minutes are converted to JPEG and written to
data/photos/<meal_id>_<k>.jpg — the layout src/carb_source_labeler.py expects.

A "meal" in the dataset aggregates food entries logged within 15 minutes, so
several photos of different foods can belong to one meal — all photos within
tolerance are kept, numbered chronologically.

macOS-only (uses mdls for capture time and sips for HEIC→JPEG conversion).
Export photos as *originals* (AirDrop, or Photos.app "Export Unmodified
Originals") — screenshots and re-saves lose the capture timestamp.

  python src/match_photos.py
"""

import subprocess
import sys
from datetime import datetime, tzinfo
from pathlib import Path

import pandas as pd
from PIL import Image

MEALS = "data/meal_dataset.parquet"
RAW = Path("data/photos_raw")
OUT = Path("data/photos")
TOLERANCE_MIN = 30

EXTENSIONS = {".heic", ".jpg", ".jpeg", ".png"}


def capture_time(photo: Path, local_tz: tzinfo) -> datetime | None:
    # EXIF DateTimeOriginal is the capture time proper — use it when PIL can
    # read the file (JPEG/PNG). EXIF times are naive local time.
    if photo.suffix.lower() != ".heic":
        exif = Image.open(photo).getexif()
        value = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal, else DateTime
        if value:
            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").replace(tzinfo=local_tz)

    # HEIC (or EXIF-less files): Spotlight extracts the capture date. Note it
    # indexes asynchronously — a just-copied file can report (null); rerun.
    raw = subprocess.run(
        ["mdls", "-raw", "-name", "kMDItemContentCreationDate", str(photo)],
        capture_output=True, text=True,
    ).stdout.strip()
    if not raw or raw == "(null)":
        return None
    return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")


def main() -> None:
    if not RAW.exists():
        sys.exit(f"create {RAW}/ and drop the exported photos in it first")

    meals = pd.read_parquet(MEALS)[["meal_id", "meal_start"]]
    meals["start_utc"] = meals["meal_start"].dt.tz_convert("UTC")
    local_tz = meals["meal_start"].iloc[0].tzinfo

    candidates = []   # (meal_id, taken, delta_minutes, photo)
    no_timestamp = []
    unmatched = []
    photos = [p for p in sorted(RAW.iterdir()) if p.suffix.lower() in EXTENSIONS]
    if not photos:
        sys.exit(f"no photos found in {RAW}/")

    for photo in photos:
        taken = capture_time(photo, local_tz)
        if taken is None:
            no_timestamp.append(photo.name)
            continue
        deltas = (meals["start_utc"] - taken).abs()
        best = deltas.idxmin()
        minutes = deltas[best].total_seconds() / 60
        if minutes <= TOLERANCE_MIN:
            candidates.append((int(meals.loc[best, "meal_id"]), taken, minutes, photo))
        else:
            unmatched.append(f"{photo.name} (nearest meal {minutes:.0f} min away)")

    # Keep every photo within tolerance — a meal aggregates food entries
    # logged within 15 minutes, so multiple photos per meal are expected.
    matched: dict[int, list[tuple[datetime, float, Path]]] = {}
    for meal_id, taken, minutes, photo in candidates:
        matched.setdefault(meal_id, []).append((taken, minutes, photo))

    OUT.mkdir(exist_ok=True)
    for meal_id, photos_for_meal in sorted(matched.items()):
        for k, (taken, minutes, photo) in enumerate(sorted(photos_for_meal), start=1):
            dest = OUT / f"{meal_id}_{k}.jpg"
            subprocess.run(
                ["sips", "-s", "format", "jpeg", str(photo), "--out", str(dest)],
                capture_output=True, check=True,
            )
            print(f"meal {meal_id:3d} #{k}  <-  {photo.name}  (Δ {minutes:.1f} min)")

    n_photos = sum(len(v) for v in matched.values())
    print(f"\nmatched   {len(matched)}/{len(meals)} meals ({n_photos} photos)")
    for label, items in [("no capture timestamp", no_timestamp),
                         ("no meal within tolerance", unmatched)]:
        if items:
            print(f"\n{label} ({len(items)}):")
            for item in items:
                print(f"  {item}")


if __name__ == "__main__":
    main()
