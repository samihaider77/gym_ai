"""Add Workout Guide drawings (github.com/bryllim/workout-guide, CC BY-SA 4.0, built on Everkinetic) to
exercises that have no demo yet.

Run from backend/: python scripts/import_workout_guide.py [--dry-run]
Uses DATABASE_URL like the API, so the same command updates the live database when DATABASE_URL points at it.
Only frames 1 and 3 (start and end) are used: the middle frames are drawn with a different line weight, and
a start/end loop matches the Everkinetic demos. The white-on-transparent art is turned into black lines on
white like the rest of the library. Exercises that already have a demo keep it. Safe to re-run: rendered
loops are reused, so a second run (e.g. against the live database) only writes the rows.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_open_exercise_media as media  # noqa: E402
from sqlalchemy import select  # noqa: E402

REV = "HEAD"
RAW = f"https://raw.githubusercontent.com/bryllim/workout-guide/{REV}/packages/workout-guide"
CACHE = Path(__file__).resolve().parents[1] / ".media-cache" / "workout-guide"
LICENSE = "CC BY-SA 4.0"
ATTRIBUTION = ("“{name}” illustration by Bryl Lim (Workout Guide), based on Everkinetic drawings, "
               "CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)")


def black_on_white(slug: str, frame: int) -> Path:
    """Download one frame and turn its white lines into black ink on a transparent background."""
    target = CACHE / slug / f"frame-{frame}-ink.png"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        source = CACHE / slug / f"frame-{frame}.png"
        if not source.exists():
            source.write_bytes(media.fetch(f"{RAW}/assets/{slug}/frame-{frame}.png"))
        with Image.open(source) as image:
            alpha = image.convert("RGBA").getchannel("A")
        ink = Image.new("RGBA", alpha.size, (0, 0, 0, 0))
        ink.putalpha(alpha)
        ink.save(target)
    return target


def outlined(slug: str, frame: int) -> bool:
    """True for frames redrawn in the hollow double-outline style, which doesn't match the Everkinetic lines.

    Those strokes are mostly semi-transparent fill between two edges: half-opaque pixels outnumber solid ones
    (ratio about 0.85 to 6), while the thin Everkinetic-style lines stay below about 0.6."""
    black_on_white(slug, frame)  # makes sure the source is downloaded
    with Image.open(CACHE / slug / f"frame-{frame}.png") as image:
        histogram = image.convert("RGBA").getchannel("A").histogram()
    return sum(histogram[40:200]) / max(sum(histogram[200:]), 1) > 0.7


EQUIPMENT_WORDS = ("dumbbell", "barbell", "kettlebell", "cable", "band", "machine", "smith", "ez")


def same_equipment(record: dict, exercise_name: str) -> bool:
    """The match must not add equipment the drawing doesn't show (e.g. "Calf Raise" -> "Calf Raise On A Dumbbell")."""
    drawing = f"{record['name']} {record.get('equipment', '')}".lower()
    return all(word in drawing for word in EQUIPMENT_WORDS if word in exercise_name.lower().split())


def has_demo(db, exercise_id) -> bool:
    return any(m.status.lower() not in media.HIDDEN_STATUSES for m in db.scalars(
        select(media.ExerciseMediaModel).where(media.ExerciseMediaModel.exercise_id == exercise_id)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(media.fetch(f"{RAW}/manifest.json"))
    media.cached_download = lambda url: Path(url)  # frames are converted local files
    added, kept, unmatched, mixed, touched = 0, 0, [], [], set()
    with media.SessionLocal() as db:
        catalog = media.Catalog(db, create_missing=False)
        for record in manifest:
            frames = {f["index"] for f in record.get("frames", [])}
            if not {1, 3} <= frames:
                continue
            item = media.SourceItem(
                provider="WorkoutGuide", source_id=record["slug"], name=record["name"], kind="loop", urls=[],
                license=LICENSE, attribution="")
            exercise = catalog.resolve(item)
            if exercise is None or not same_equipment(record, exercise.name):
                unmatched.append(record["name"])
                continue
            if outlined(record["slug"], 1) or outlined(record["slug"], 3):
                mixed.append(record["name"])
                for row in db.scalars(select(media.ExerciseMediaModel).where(  # hide an earlier import of it
                        media.ExerciseMediaModel.provider == "WorkoutGuide",
                        media.ExerciseMediaModel.media_url.like(f"/exercise-media/workoutguide/{record['slug']}-%"))):
                    row.status, row.is_primary = "deprecated", False
                    touched.add(row.exercise_id)
                continue
            if exercise.id in touched or has_demo(db, exercise.id):
                kept += 1
                continue
            print(f"{record['name']} -> {exercise.name}")
            touched.add(exercise.id)
            if args.dry_run:
                continue
            item.name = exercise.name
            item.attribution = ATTRIBUTION.format(name=exercise.name)
            item.urls = [str(black_on_white(record["slug"], n)) for n in (1, 3)]
            fields = media.render(item, 480)
            media.upsert_media(db, exercise, item, fields, 480, all_styles=False)
            added += 1
            if added % 25 == 0:
                db.commit()
                print(f"[+] {added} added", flush=True)
        if not args.dry_run:
            db.flush()
            media.choose_primaries(db, touched)
            db.commit()
    print(f"\n{added} exercises got a demo, {kept} already had one, {len(mixed)} skipped (start and end "
          f"frames in different drawing styles), {len(unmatched)} drawings have no matching exercise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
