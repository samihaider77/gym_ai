"""Merge near-duplicate exercises such as "Hammer Curl" and "Hammer Curls" or
"Drag Curl" and "Drag Curl with Barbell".

Run from backend/: python scripts/merge_duplicate_exercises.py [--dry-run]
Exercises match when their names share the same words once plurals, spelling variants,
filler words and equipment words are ignored, and they use the same equipment. In each group
the exercise used in the most workouts (then with the most media) is kept. Workout entries,
media and muscles move onto it, missing text is copied over, and the others are deactivated,
not deleted. The kept exercise takes the cleanest name in the group; the names of the merged
rows stay in the table so the seed and import scripts do not create them again. Safe to re-run.
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import func, select, update  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel, VISIBLE_MEDIA_STATUSES  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel, exercise_muscle_association  # noqa: E402
from app.modules.users.infrastructure.models import UserModel  # noqa: E402,F401  (mapper registry)
from app.modules.workout_plans.infrastructure.models import WorkoutPlanModel  # noqa: E402,F401
from app.modules.workout_days.infrastructure.models import WorkoutDayModel  # noqa: E402,F401
from app.modules.workout_exercises.infrastructure.models import WorkoutExerciseModel  # noqa: E402
from seed_exercises import SPECS  # noqa: E402

# Equipment words in a name, mapped to the same token as the exercise's equipment row.
NAME_EQUIPMENT = {"dumbbell": "dumbbell", "dumbbells": "dumbbell", "db": "dumbbell", "barbell": "barbell",
                  "bb": "barbell", "kettlebell": "kettlebell", "kettlebells": "kettlebell", "cable": "cable",
                  "cables": "cable", "machine": "machine", "band": "band", "bands": "band",
                  "bodyweight": "bodyweight", "ez": "ez", "smith": "smith"}
ROW_EQUIPMENT = {"Dumbbell": "dumbbell", "Barbell": "barbell", "Kettlebell": "kettlebell", "Cable Machine": "cable",
                 "Machine": "machine", "Resistance Band": "band", "Bodyweight": "bodyweight",
                 "E-Z Curl Bar": "ez", "Smith Machine": "smith"}
FILLER = {"with", "a", "the", "on", "using", "and", "of", "to", "in", "exercise", "bar"}
SPELLING = {"biceps": "bicep", "triceps": "tricep", "pushup": "push up", "pullup": "pull up", "situp": "sit up",
            "chinup": "chin up", "alternate": "alternating", "flye": "fly", "flyes": "fly", "flies": "fly",
            "extensions": "extension", "raises": "raise", "curls": "curl", "presses": "press", "rows": "row",
            "squats": "squat", "lunges": "lunge", "crunches": "crunch", "dips": "dip", "shrugs": "shrug",
            "kickbacks": "kickback", "deadlifts": "deadlift"}
SEEDED = {spec[0] for spec in SPECS}


def singular(word: str) -> str:
    # "mornings" -> "morning"; leaves "press", "abs" and "lats" alone.
    return word[:-1] if len(word) > 4 and word.endswith("s") and not word.endswith("ss") else word


def match_keys(name: str, equipment: str | None) -> tuple[tuple[str, str], tuple[str, str]]:
    """Two keys: the words in any order, and the words run together ("cross-over" = "crossover")."""
    words = re.sub(r"[^a-z0-9 ]", " ", name.lower().replace("-", " ")).split()
    tokens = [singular(token) for word in words for token in SPELLING.get(word, word).split()]
    gear = {NAME_EQUIPMENT[t] for t in tokens if t in NAME_EQUIPMENT}
    if equipment in ROW_EQUIPMENT:
        gear.add(ROW_EQUIPMENT[equipment])
    rest = [t for t in tokens if t not in NAME_EQUIPMENT and t not in FILLER]
    gear_key = ",".join(sorted(gear))
    return (" ".join(sorted(rest)), gear_key), (singular("".join(rest)), gear_key)


def name_rank(name: str) -> tuple:
    # Seeded names first (the seed re-activates them by name), then names without a
    # "with ..." / " - " tail, then the shortest.
    lowered = f" {name.lower()} "
    clumsy = any(part in lowered for part in (" with ", " using ", " - "))
    return name not in SEEDED, clumsy, len(name), name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        equipment = {row.id: row.name for row in db.scalars(select(EquipmentModel))}
        used = dict(db.execute(select(WorkoutExerciseModel.exercise_id, func.count())
                               .group_by(WorkoutExerciseModel.exercise_id)).all())
        groups: dict[int, list[ExerciseModel]] = defaultdict(list)
        group_of: dict[tuple[str, str], int] = {}
        for exercise in db.scalars(select(ExerciseModel).where(ExerciseModel.is_active.is_(True))):
            keys = [k for k in match_keys(exercise.name, equipment.get(exercise.equipment_id)) if k[0]]
            if not keys:
                continue
            found = {group_of[k] for k in keys if k in group_of}
            group = min(found) if found else len(group_of)
            for other in found - {group}:  # this exercise links two groups: join them
                groups[group] += groups.pop(other)
                group_of.update({k: group for k, g in group_of.items() if g == other})
            groups[group].append(exercise)
            group_of.update({k: group for k in keys})

        merged = 0
        for members in groups.values():
            if len(members) < 2:
                continue
            members.sort(key=lambda e: (-used.get(e.id, 0), -sum(m.status in VISIBLE_MEDIA_STATUSES for m in e.media),
                                        -len(e.media), name_rank(e.name)))
            keeper, duplicates = members[0], members[1:]
            best = min(members, key=lambda e: name_rank(e.name))
            print(f"{best.name}  <-  " + ", ".join(e.name for e in members if e is not best))

            keeper_urls = {m.media_url for m in keeper.media}
            has_primary = any(m.is_primary for m in keeper.media)
            for duplicate in duplicates:
                db.execute(update(WorkoutExerciseModel).where(WorkoutExerciseModel.exercise_id == duplicate.id)
                           .values(exercise_id=keeper.id))
                for media in list(duplicate.media):
                    if media.media_url in keeper_urls:
                        continue
                    keeper_urls.add(media.media_url)
                    media.is_primary = media.is_primary and not has_primary
                    has_primary = has_primary or media.is_primary
                    media.exercise_id = keeper.id
                muscles = db.execute(select(exercise_muscle_association.c.muscle_group_id, exercise_muscle_association.c.role)
                                     .where(exercise_muscle_association.c.exercise_id == duplicate.id)).all()
                if muscles:
                    db.execute(insert(exercise_muscle_association).on_conflict_do_nothing(),
                               [{"exercise_id": keeper.id, "muscle_group_id": m, "role": r} for m, r in muscles])
                for field in ("description", "instructions", "force_type", "mechanic_type"):
                    if not getattr(keeper, field) and getattr(duplicate, field):
                        setattr(keeper, field, getattr(duplicate, field))
                duplicate.is_active = False
                merged += 1
            db.flush()
            db.expire(keeper, ["media"])

            if best is not keeper:
                # Swap names and slugs so both stay taken; a temporary value avoids the unique index.
                old_name, old_slug = keeper.name, keeper.slug
                best_name, best_slug = best.name, best.slug
                best.name, best.slug = f"~merge~{best.id}", f"~merge~{best.id}"
                db.flush()
                keeper.name, keeper.slug = best_name, best_slug
                db.flush()
                best.name, best.slug = old_name, old_slug
                db.flush()

        # The importer keeps one primary per exercise; make sure merging left exactly one.
        for exercise in db.scalars(select(ExerciseModel).where(ExerciseModel.is_active.is_(True))):
            visible = [m for m in exercise.media if m.status.lower() not in {"failed", "deprecated", "rejected"}]
            if visible and sum(m.is_primary for m in visible) != 1:
                for index, media in enumerate(sorted(visible, key=lambda m: not m.is_primary)):
                    media.is_primary = index == 0

        print(f"\n{merged} duplicate exercises merged.")
        if args.dry_run:
            db.rollback()
            print("Dry run: nothing saved.")
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
