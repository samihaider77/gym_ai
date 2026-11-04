"""Merge duplicate equipment and tidy exercise names already in the database.

Run from backend/: python scripts/normalize_catalog.py [--dry-run]
Duplicate equipment rows are deactivated (not deleted) after their exercises move to the
canonical row, so the step can be inspected or reversed. Safe to re-run.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select, update  # noqa: E402

from app.core.db.session import SessionLocal  # noqa: E402
from app.core.utils.slug import generate_slug  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402
from catalog_names import canonical_equipment, display_name  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = list(db.scalars(select(EquipmentModel)))
        by_name = {row.name: row for row in rows}
        merged = 0
        for row in rows:
            target_name = canonical_equipment(row.name)
            if target_name == row.name:
                continue
            target = by_name.get(target_name)
            if target is None:
                target = EquipmentModel(name=target_name, slug=generate_slug(target_name),
                                        category=generate_slug(target_name).replace("-", "_"),
                                        description=f"{target_name} equipment")
                db.add(target)
                db.flush()
                by_name[target_name] = target
            target.is_active = True
            moved = db.execute(update(ExerciseModel).where(ExerciseModel.equipment_id == row.id)
                               .values(equipment_id=target.id)).rowcount
            if row.is_active:
                print(f"equipment: {row.name} -> {target_name} ({moved} exercises)")
                merged += 1
            row.is_active = False

        taken = {name.lower() for name in db.scalars(select(ExerciseModel.name))}
        renamed = 0
        for exercise in db.scalars(select(ExerciseModel)):
            new_name = display_name(exercise.name)
            if new_name != exercise.name and (new_name.lower() == exercise.name.lower() or new_name.lower() not in taken):
                print(f"name: {exercise.name} -> {new_name}")
                exercise.name = new_name
                renamed += 1

        print(f"\n{merged} equipment rows merged, {renamed} exercise names tidied.")
        if args.dry_run:
            db.rollback()
            print("Dry run: nothing saved.")
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
