"""Show only the Everkinetic line drawings, so every demo in the library looks the same.

Run from backend/: python scripts/set_media_style.py [--all-styles] [--dry-run]
Media in other styles is set to "deprecated" (hidden, not deleted). --all-styles shows it again.
Each exercise's primary demo is re-picked from what stays visible. Safe to re-run.
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select  # noqa: E402

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel, VISIBLE_MEDIA_STATUSES  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402,F401  (mapper registry)
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402,F401
from catalog_names import is_house_style  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-styles", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = list(db.scalars(select(ExerciseMediaModel).where(
            ExerciseMediaModel.status.in_((*VISIBLE_MEDIA_STATUSES, "deprecated")))))
        hidden = shown = 0
        by_exercise = defaultdict(list)
        for media in rows:
            visible = args.all_styles or is_house_style(media.provider, media.attribution)
            if visible and media.status == "deprecated":
                media.status = "ready"
                shown += 1
            elif not visible and media.status in VISIBLE_MEDIA_STATUSES:
                media.status = "deprecated"
                hidden += 1
            by_exercise[media.exercise_id].append(media)

        with_demo = 0
        for media_rows in by_exercise.values():
            visible = [m for m in media_rows if m.status in VISIBLE_MEDIA_STATUSES]
            # Keep the current primary when it is still visible, else prefer a loop over a still.
            visible.sort(key=lambda m: (not m.is_primary, m.media_type != "video"))
            for media in media_rows:
                media.is_primary = bool(visible) and media is visible[0]
            with_demo += bool(visible)

        print(f"{hidden} media hidden, {shown} shown again; {with_demo} exercises have a visible demo.")
        if args.dry_run:
            db.rollback()
            print("Dry run: nothing saved.")
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
