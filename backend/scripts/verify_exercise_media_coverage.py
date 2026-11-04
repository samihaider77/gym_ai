"""Verify that every active exercise has approved same-provider anatomical media."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402,F401
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: E402,F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Require approved anatomical media for every active exercise."
    )
    parser.add_argument("--provider", default="ExerciseDB.io")
    parser.add_argument("--status", default="ready")
    parser.add_argument("--media-type", default="gif")
    parser.add_argument("--list-limit", type=int, default=50)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Print coverage without returning a failing exit code.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_limit < 0:
        raise SystemExit("--list-limit must be zero or greater")

    with SessionLocal() as db:
        exercises = db.scalars(
            select(ExerciseModel)
            .where(ExerciseModel.is_active.is_(True))
            .order_by(ExerciseModel.name)
        ).all()
        covered_ids = set(
            db.scalars(
                select(ExerciseMediaModel.exercise_id).where(
                    ExerciseMediaModel.provider == args.provider,
                    ExerciseMediaModel.status == args.status,
                    ExerciseMediaModel.is_primary.is_(True),
                    ExerciseMediaModel.media_type == args.media_type,
                )
            ).all()
        )

    missing = [exercise for exercise in exercises if exercise.id not in covered_ids]
    covered = len(exercises) - len(missing)
    total = len(exercises)
    percent = (covered / total * 100) if total else 100.0
    print(
        f"Same-character media coverage: {covered}/{total} "
        f"({percent:.2f}%) provider={args.provider!r} status={args.status!r} "
        f"media_type={args.media_type!r}"
    )

    if missing:
        print(f"Missing same-provider movement media: {len(missing)}")
        for exercise in missing[: args.list_limit]:
            print(f"  - {exercise.name} [{exercise.id}]")
        remaining = len(missing) - args.list_limit
        if remaining > 0:
            print(f"  ... and {remaining} more")
    else:
        print("PASS: every active exercise has primary same-provider movement media.")

    return 0 if not missing or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
