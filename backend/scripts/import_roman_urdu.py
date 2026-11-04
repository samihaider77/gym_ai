"""Load Roman Urdu exercise names and instructions into the database.

Run from backend/: python scripts/import_roman_urdu.py [--dry-run]
Reads data/exercises_roman_urdu.json, keyed by the English exercise name so it survives a fresh
seed. Exercises not in the file keep showing English. Safe to re-run.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402,F401  (mapper registry)
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data" / "exercises_roman_urdu.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    entries: dict[str, dict] = json.loads(DATA.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        updated = 0
        found = set()
        for exercise in db.scalars(select(ExerciseModel).where(ExerciseModel.name.in_(entries))):
            entry = entries[exercise.name]
            found.add(exercise.name)
            name_ur = (entry.get("name_ur") or "").strip()[:200] or None
            instructions_ur = (entry.get("instructions_ur") or "").strip() or None
            if (exercise.name_ur, exercise.instructions_ur) != (name_ur, instructions_ur):
                exercise.name_ur, exercise.instructions_ur = name_ur, instructions_ur
                updated += 1
        missing = sorted(set(entries) - found)
        print(f"{updated} exercises updated, {len(found)} matched, {len(missing)} names in the file not in the database.")
        for name in missing[:20]:
            print(f"  not found: {name}")
        if args.dry_run:
            db.rollback()
            print("Dry run: nothing saved.")
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
