"""Add drawings made by the GymAI drawing notebook (tools/ai-drawings) to the exercise library.

Run from backend/: python scripts/import_generated_drawings.py <gymai-drawings.zip or folder> [--pick picks.json] [--dry-run]
Each exercise folder holds start-N.png / end-N.png candidates. Candidate 1 is used unless picks.json maps the
exercise name to another number (0 skips it). Every pair becomes the same start/end loop as the library drawings.
Exercises are matched by their English name. Safe to re-run.
"""
import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_open_exercise_media as media  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

LICENSE = "CC BY-SA 4.0"
ATTRIBUTION = ("“{name}” drawing made by GymAI in the Everkinetic style, adapted from Everkinetic drawings "
               "(everkinetic.com), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="gymai-drawings.zip from the notebook, or the unzipped folder")
    parser.add_argument("--pick", help="JSON file: {\"Exercise Name\": candidate number, 0 to skip}")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(args.source)
        if root.suffix.lower() == ".zip":
            zipfile.ZipFile(root).extractall(tmp)
            root = Path(tmp)
        manifest_path = next(root.rglob("manifest.json"))
        drawings = manifest_path.parent
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        picks = json.loads(Path(args.pick).read_text(encoding="utf-8")) if args.pick else {}
        media.cached_download = lambda url: Path(url)  # frames are local files, not downloads

        added, missing, skipped, touched = 0, [], 0, set()
        with media.SessionLocal() as db:
            for entry in entries:
                choice = int(picks.get(entry["name"], 1))
                if choice == 0:
                    skipped += 1
                    continue
                exercise = db.scalar(select(media.ExerciseModel).where(
                    func.lower(media.ExerciseModel.name) == entry["name"].lower(),
                    media.ExerciseModel.is_active.is_(True)))
                if exercise is None:
                    missing.append(entry["name"])
                    continue
                frames = [drawings / entry["slug"] / f"{phase}-{choice}.png" for phase in ("start", "end")]
                if not all(frame.exists() for frame in frames):
                    missing.append(f"{entry['name']} (no candidate {choice})")
                    continue
                item = media.SourceItem(
                    provider="GymAI", source_id=entry["slug"], name=exercise.name, kind="loop",
                    urls=[str(frame) for frame in frames], license=LICENSE,
                    attribution=ATTRIBUTION.format(name=exercise.name))
                print(f"{exercise.name}: candidate {choice}")
                if args.dry_run:
                    continue
                if choice != 1:  # a different pick replaces an earlier render
                    for old in item.folder.glob("*"):
                        old.unlink()
                fields = media.render(item, 480)
                media.upsert_media(db, exercise, item, fields, 480, all_styles=False)
                touched.add(exercise.id)
                added += 1
            if not args.dry_run:
                media.choose_primaries(db, touched)
                db.commit()
        print(f"\n{added} drawings added, {skipped} skipped, {len(missing)} not matched.")
        for name in missing:
            print("  not matched:", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
