"""Keep legacy generated exercise animations registered but retired.

The low-poly visual pipeline is no longer approved for user-facing exercise
demonstrations. New anatomical media is imported with
``import_exercisedb_media.py``.
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, or_
from app.core.db.session import SessionLocal
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: F401
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: F401
from app.modules.exercises.infrastructure.models import ExerciseModel
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel

ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = ROOT / "frontend" / "public" / "exercise-media" / "generated"

NAME_ALIASES = {
    "Barbell Squat": ["Barbell Back Squat", "Barbell Squat", "Squat"],
    "Barbell Deadlift": ["Conventional Deadlift", "Barbell Deadlift", "Deadlift"],
    "Dumbbell Biceps Curl": ["Dumbbell Curl", "Barbell Curl", "Biceps Curl", "Dumbbell Biceps Curl"],
    "Romanian Deadlift": ["Romanian Deadlift", "Barbell Romanian Deadlift"],
    "Sit-Up": ["Sit-Up", "3/4 Sit-Up"],
}

SLUG_ALIASES = {
    "barbell-squat": ["barbell-back-squat", "barbell-squat", "squat"],
    "deadlift": ["conventional-deadlift", "deadlift", "barbell-deadlift"],
    "dumbbell-biceps-curl": ["dumbbell-curl", "barbell-curl", "dumbbell-biceps-curl"],
    "barbell-romanian-deadlift": ["romanian-deadlift", "barbell-romanian-deadlift"],
    "sit-up": ["sit-up", "3-4-sit-up"],
}

with SessionLocal() as db:
    registered = 0
    for version_dir in sorted(MEDIA_ROOT.glob("*/v*/")):
        folder_slug = version_dir.parent.name
        movement_file = version_dir / "movement.json"
        video = version_dir / "animation.mp4"
        poster = version_dir / "poster.png"

        if not video.exists() or video.stat().st_size == 0:
            continue

        definition = {}
        if movement_file.exists():
            try:
                definition = json.loads(movement_file.read_text())
            except Exception:
                pass

        ex_name = definition.get("name", "")
        possible_names = [ex_name] + NAME_ALIASES.get(ex_name, [])
        possible_slugs = [folder_slug] + SLUG_ALIASES.get(folder_slug, [])

        query = select(ExerciseModel).where(
            or_(
                ExerciseModel.slug.in_(possible_slugs),
                ExerciseModel.name.in_(possible_names)
            )
        )
        exercises = db.scalars(query).all()

        if not exercises:
            print(f"[-] Skipped unknown exercise for folder: {folder_slug} (name: {ex_name})")
            continue

        media_url = f"/exercise-media/generated/{version_dir.parent.name}/{version_dir.name}/animation.mp4"
        poster_url = f"/exercise-media/generated/{version_dir.parent.name}/{version_dir.name}/poster.png"

        for exercise in exercises:
            row = db.scalar(
                select(ExerciseMediaModel).where(
                    ExerciseMediaModel.exercise_id == exercise.id,
                    ExerciseMediaModel.media_url == media_url
                )
            )
            if not row:
                row = ExerciseMediaModel(exercise_id=exercise.id, media_type="animation", media_url=media_url)
                db.add(row)

            row.poster_url = poster_url
            row.provider = "GymAI Visual Pipeline"
            row.license = "GymAI original"
            row.attribution = "GymAI procedural character and equipment"
            row.width = 640
            row.height = 360
            row.camera_angle = definition.get("camera_angle") or "45-degree"
            row.format = "mp4"
            row.version = int(version_dir.name.removeprefix("v")) if version_dir.name.startswith("v") else 1
            row.status = "deprecated"
            row.is_primary = False
            registered += 1
            print(f"[+] Retired legacy media for: {exercise.name} -> {media_url}")

    db.commit()
    print(f"\nSuccessfully kept {registered} legacy exercise media records deprecated.")
