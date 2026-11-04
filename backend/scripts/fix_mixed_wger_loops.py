"""Rebuild wger start/end loops whose two frames came from different authors (e.g. an Everkinetic line
drawing followed by someone else's colour render), so every loop shows one drawing style.

Run from backend/: python scripts/fix_mixed_wger_loops.py [--dry-run]
Each mixed loop is rebuilt from same-author pictures: a loop when that author has two, otherwise one still.
The old mixed loop row is hidden ("deprecated"). Safe to re-run.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_open_exercise_media as media  # noqa: E402
from sqlalchemy import select  # noqa: E402


def mixed_ids() -> set[str]:
    payload = media.fetch_json(f"{media.WGER_API}/exerciseinfo/?limit=2000")
    found = set()
    for exercise in payload["results"]:
        images = sorted(exercise["images"], key=lambda img: (not img["is_main"], img["id"]))
        if len(images) >= 2 and images[0].get("license_author") != images[1].get("license_author"):
            found.add(str(exercise["id"]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mixed = mixed_ids()
    items = {i.source_id: i for i in media.load_wger(include_videos=False) if i.source_id in mixed}
    fixed, touched = 0, set()
    with media.SessionLocal() as db:
        for source_id, item in sorted(items.items()):
            old_rows = list(db.scalars(select(media.ExerciseMediaModel).where(
                media.ExerciseMediaModel.provider == "wger",
                media.ExerciseMediaModel.media_url.like(f"/exercise-media/wger/{source_id}-loop/%"))))
            if not old_rows:
                continue
            exercise = db.get(media.ExerciseModel, old_rows[0].exercise_id)
            print(f"{exercise.name}: mixed loop -> {item.kind} from {len(item.urls)} same-author picture(s)")
            if args.dry_run:
                continue
            if item.kind == "loop":  # same folder as the mixed loop: clear it so it is rendered again
                shutil.rmtree(item.folder, ignore_errors=True)
            fields = media.render(item, 480)
            for row in old_rows:
                row.status, row.is_primary = "deprecated", False
            media.upsert_media(db, exercise, item, fields, 480, all_styles=False)
            touched.add(exercise.id)
            fixed += 1
        if not args.dry_run:
            db.flush()
            media.choose_primaries(db, touched)
            db.commit()
    print(f"\n{len(mixed)} wger exercises have mixed pictures; {fixed} loops rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
