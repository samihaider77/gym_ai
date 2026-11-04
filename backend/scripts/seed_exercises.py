"""Idempotently seed GymAI's curated Exercise V1 library.

Run from backend/: python scripts/seed_exercises.py
The records are original curated metadata; no external dataset is copied.
"""
from pathlib import Path
import sys
import json
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select, func
from app.core.db.session import SessionLocal
from app.modules.equipment.infrastructure.models import EquipmentModel
from app.modules.exercises.infrastructure.models import ExerciseModel, exercise_muscle_association
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel
from app.core.utils.slug import generate_slug
sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_names import canonical_equipment, display_name  # noqa: E402

MUSCLES = [
    ("Chest", "chest"), ("Back", "back"), ("Shoulders", "shoulders"), ("Biceps", "arms"),
    ("Triceps", "arms"), ("Forearms", "arms"), ("Quadriceps", "legs"), ("Hamstrings", "legs"),
    ("Glutes", "legs"), ("Calves", "legs"), ("Core", "core"), ("Hip Flexors", "legs"),
    ("Lower Back", "back"), ("Full Body", "full_body"),
]
EQUIPMENT = [
    ("Barbell", "barbell"), ("Dumbbell", "dumbbell"), ("Kettlebell", "kettlebell"),
    ("Cable Machine", "cable"), ("Smith Machine", "machine"), ("Leg Press Machine", "machine"),
    ("Resistance Band", "band"), ("Pull-Up Bar", "bodyweight"), ("Bench", "bench"),
    ("Bodyweight", "bodyweight"), ("Treadmill", "cardio"),
]

# name, primary, secondary, equipment, type, difficulty, force, mechanic, compound
SPECS = [
    ("Barbell Bench Press","Chest","Triceps","Barbell","strength","intermediate","push","compound",True),
    ("Dumbbell Bench Press","Chest","Triceps","Dumbbell","strength","beginner","push","compound",True),
    ("Incline Barbell Bench Press","Chest","Shoulders","Barbell","strength","intermediate","push","compound",True),
    ("Incline Dumbbell Press","Chest","Shoulders","Dumbbell","strength","beginner","push","compound",True),
    ("Decline Bench Press","Chest","Triceps","Barbell","strength","intermediate","push","compound",True),
    ("Dumbbell Fly","Chest","Shoulders","Dumbbell","strength","beginner","push","isolation",False),
    ("Cable Crossover","Chest","Shoulders","Cable Machine","strength","beginner","push","isolation",False),
    ("Push-Up","Chest","Triceps","Bodyweight","calisthenics","beginner","push","compound",True),
    ("Close-Grip Push-Up","Triceps","Chest","Bodyweight","calisthenics","beginner","push","compound",True),
    ("Chest Dip","Chest","Triceps","Bodyweight","calisthenics","intermediate","push","compound",True),
    ("Barbell Back Squat","Quadriceps","Glutes","Barbell","strength","intermediate","push","compound",True),
    ("Front Squat","Quadriceps","Core","Barbell","strength","advanced","push","compound",True),
    ("Goblet Squat","Quadriceps","Glutes","Dumbbell","strength","beginner","push","compound",True),
    ("Barbell Hack Squat","Quadriceps","Glutes","Barbell","strength","advanced","push","compound",True),
    ("Leg Press","Quadriceps","Glutes","Leg Press Machine","strength","beginner","push","compound",True),
    ("Walking Lunge","Quadriceps","Glutes","Dumbbell","strength","beginner","push","compound",True),
    ("Reverse Lunge","Glutes","Quadriceps","Dumbbell","strength","beginner","push","compound",True),
    ("Bulgarian Split Squat","Quadriceps","Glutes","Dumbbell","strength","intermediate","push","compound",True),
    ("Step-Up","Glutes","Quadriceps","Bench","strength","beginner","push","compound",True),
    ("Barbell Hip Thrust","Glutes","Hamstrings","Barbell","strength","intermediate","push","compound",True),
    ("Glute Bridge","Glutes","Hamstrings","Bodyweight","strength","beginner","push","isolation",False),
    ("Romanian Deadlift","Hamstrings","Glutes","Barbell","strength","intermediate","pull","compound",True),
    ("Stiff-Leg Deadlift","Hamstrings","Lower Back","Barbell","strength","advanced","pull","compound",True),
    ("Seated Leg Curl","Hamstrings","Calves","Leg Press Machine","strength","beginner","pull","isolation",False),
    ("Lying Leg Curl","Hamstrings","Calves","Leg Press Machine","strength","beginner","pull","isolation",False),
    ("Standing Calf Raise","Calves","","Bodyweight","strength","beginner","push","isolation",False),
    ("Seated Calf Raise","Calves","","Dumbbell","strength","beginner","push","isolation",False),
    ("Conventional Deadlift","Lower Back","Glutes","Barbell","strength","advanced","pull","compound",True),
    ("Sumo Deadlift","Glutes","Hamstrings","Barbell","strength","advanced","pull","compound",True),
    ("Pull-Up","Back","Biceps","Pull-Up Bar","calisthenics","intermediate","pull","compound",True),
    ("Chin-Up","Biceps","Back","Pull-Up Bar","calisthenics","intermediate","pull","compound",True),
    ("Lat Pulldown","Back","Biceps","Cable Machine","strength","beginner","pull","compound",True),
    ("Barbell Bent-Over Row","Back","Biceps","Barbell","strength","intermediate","pull","compound",True),
    ("One-Arm Dumbbell Row","Back","Biceps","Dumbbell","strength","beginner","pull","compound",True),
    ("Seated Cable Row","Back","Biceps","Cable Machine","strength","beginner","pull","compound",True),
    ("Chest-Supported Row","Back","Biceps","Dumbbell","strength","beginner","pull","compound",True),
    ("Straight-Arm Pulldown","Back","Shoulders","Cable Machine","strength","beginner","pull","isolation",False),
    ("Barbell Overhead Press","Shoulders","Triceps","Barbell","strength","intermediate","push","compound",True),
    ("Dumbbell Shoulder Press","Shoulders","Triceps","Dumbbell","strength","beginner","push","compound",True),
    ("Arnold Press","Shoulders","Triceps","Dumbbell","strength","intermediate","push","compound",True),
    ("Dumbbell Lateral Raise","Shoulders","","Dumbbell","strength","beginner","pull","isolation",False),
    ("Cable Lateral Raise","Shoulders","","Cable Machine","strength","beginner","pull","isolation",False),
    ("Face Pull","Shoulders","Back","Cable Machine","strength","beginner","pull","isolation",False),
    ("Rear Delt Fly","Shoulders","Back","Dumbbell","strength","beginner","pull","isolation",False),
    ("Barbell Shrug","Shoulders","Forearms","Barbell","strength","beginner","pull","isolation",False),
    ("Barbell Curl","Biceps","Forearms","Barbell","strength","beginner","pull","isolation",False),
    ("Dumbbell Curl","Biceps","Forearms","Dumbbell","strength","beginner","pull","isolation",False),
    ("Hammer Curl","Biceps","Forearms","Dumbbell","strength","beginner","pull","isolation",False),
    ("Incline Dumbbell Curl","Biceps","Forearms","Dumbbell","strength","intermediate","pull","isolation",False),
    ("Cable Curl","Biceps","Forearms","Cable Machine","strength","beginner","pull","isolation",False),
    ("Triceps Pushdown","Triceps","Shoulders","Cable Machine","strength","beginner","push","isolation",False),
    ("Overhead Triceps Extension","Triceps","Shoulders","Dumbbell","strength","beginner","push","isolation",False),
    ("Skull Crusher","Triceps","Shoulders","Barbell","strength","intermediate","push","isolation",False),
    ("Bench Dip","Triceps","Chest","Bench","calisthenics","beginner","push","compound",True),
    ("Plank","Core","Shoulders","Bodyweight","calisthenics","beginner","static","isolation",False),
    ("Side Plank","Core","Shoulders","Bodyweight","calisthenics","beginner","static","isolation",False),
    ("Hanging Knee Raise","Core","Hip Flexors","Pull-Up Bar","calisthenics","intermediate","pull","isolation",False),
    ("Hanging Leg Raise","Core","Hip Flexors","Pull-Up Bar","calisthenics","advanced","pull","isolation",False),
    ("Ab Wheel Rollout","Core","Shoulders","Bodyweight","strength","advanced","push","compound",True),
    ("Cable Crunch","Core","Hip Flexors","Cable Machine","strength","beginner","pull","isolation",False),
    ("Russian Twist","Core","Hip Flexors","Dumbbell","strength","beginner","static","compound",True),
    ("Mountain Climber","Core","Full Body","Bodyweight","cardio","beginner","dynamic","compound",True),
    ("Burpee","Full Body","Core","Bodyweight","cardio","intermediate","dynamic","compound",True),
    ("Jumping Jack","Full Body","Calves","Bodyweight","cardio","beginner","dynamic","compound",True),
    ("Treadmill Walk","Full Body","Calves","Treadmill","cardio","beginner","dynamic","compound",True),
    ("Treadmill Run","Full Body","Calves","Treadmill","cardio","intermediate","dynamic","compound",True),
    ("Kettlebell Swing","Glutes","Hamstrings","Kettlebell","strength","intermediate","pull","compound",True),
    ("Kettlebell Clean","Full Body","Shoulders","Kettlebell","strength","advanced","pull","compound",True),
    ("Kettlebell Goblet Squat","Quadriceps","Glutes","Kettlebell","strength","beginner","push","compound",True),
    ("Kettlebell Turkish Get-Up","Shoulders","Core","Kettlebell","strength","advanced","dynamic","compound",True),
    ("Band Pull-Apart","Shoulders","Back","Resistance Band","strength","beginner","pull","isolation",False),
    ("Band Row","Back","Biceps","Resistance Band","strength","beginner","pull","compound",True),
    ("Band Chest Press","Chest","Triceps","Resistance Band","strength","beginner","push","compound",True),
    ("Band Squat","Quadriceps","Glutes","Resistance Band","strength","beginner","push","compound",True),
    ("Cat-Cow Stretch","Lower Back","Core","Bodyweight","stretching","beginner","dynamic","isolation",False),
    ("Child's Pose","Lower Back","Shoulders","Bodyweight","flexibility","beginner","static","isolation",False),
    ("Cobra Stretch","Core","Shoulders","Bodyweight","flexibility","beginner","static","isolation",False),
    ("World's Greatest Stretch","Hip Flexors","Hamstrings","Bodyweight","flexibility","beginner","dynamic","compound",True),
    ("Standing Quad Stretch","Quadriceps","Hip Flexors","Bodyweight","stretching","beginner","static","isolation",False),
    ("Seated Hamstring Stretch","Hamstrings","Lower Back","Bodyweight","stretching","beginner","static","isolation",False),
    ("Standing Calf Stretch","Calves","","Bodyweight","stretching","beginner","static","isolation",False),
    ("Barbell Good Morning","Hamstrings","Lower Back","Barbell","strength","intermediate","pull","compound",True),
    ("Back Extension","Lower Back","Glutes","Bodyweight","strength","beginner","pull","compound",True),
    ("Dumbbell Pullover","Chest","Back","Dumbbell","strength","intermediate","pull","compound",True),
    ("Inverted Row","Back","Biceps","Bodyweight","calisthenics","beginner","pull","compound",True),
    ("Rack Pull","Back","Glutes","Barbell","strength","advanced","pull","compound",True),
    ("Dumbbell Front Raise","Shoulders","","Dumbbell","strength","beginner","push","isolation",False),
    ("Upright Row","Shoulders","Biceps","Barbell","strength","intermediate","pull","compound",True),
    ("Cable Pull-Through","Glutes","Hamstrings","Cable Machine","strength","beginner","pull","compound",True),
    ("Nordic Hamstring Curl","Hamstrings","Glutes","Bodyweight","strength","advanced","pull","isolation",False),
    ("Sissy Squat","Quadriceps","Core","Bodyweight","strength","advanced","push","isolation",False),
    ("Cossack Squat","Quadriceps","Glutes","Bodyweight","flexibility","intermediate","push","compound",True),
    ("Single-Leg Calf Raise","Calves","","Bodyweight","strength","beginner","push","isolation",False),
    ("Wrist Curl","Forearms","","Dumbbell","strength","beginner","pull","isolation",False),
    ("Reverse Wrist Curl","Forearms","","Dumbbell","strength","beginner","pull","isolation",False),
    ("Pallof Press","Core","Shoulders","Cable Machine","strength","beginner","push","isolation",False),
    ("Dead Bug","Core","Hip Flexors","Bodyweight","calisthenics","beginner","static","compound",True),
    ("Bird Dog","Core","Lower Back","Bodyweight","flexibility","beginner","static","compound",True),
    ("Box Jump","Quadriceps","Glutes","Bench","plyometrics","intermediate","dynamic","compound",True),
    ("Jump Rope","Calves","Full Body","Bodyweight","cardio","beginner","dynamic","compound",True),
]

FREE_EXERCISE_DB_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/b0eed061e1c832b3ed815fbaa4b45b3cdc14df49/dist/exercises.json"
VALID_TYPES = {"strength", "cardio", "flexibility", "calisthenics", "plyometrics", "stretching"}

def import_public_metadata(db, muscle_map, equipment_map) -> int:
    """Import normalized metadata only from the pinned public-domain dataset.

    Its image paths are intentionally not imported: the repository's public-domain
    data license is clear, while image provenance is not clearly confirmed.
    """
    with urlopen(FREE_EXERCISE_DB_URL, timeout=30) as response:
        source_items = json.load(response)
    existing = {name.lower() for name in db.execute(select(ExerciseModel.name)).scalars().all()}
    existing_slugs = set(db.execute(select(ExerciseModel.slug)).scalars().all())
    added = 0
    for raw in source_items:
        name = display_name(str(raw.get("name", "")))
        slug = generate_slug(name)
        if not name or name.lower() in existing or slug in existing_slugs:
            continue
        equipment_name = canonical_equipment(raw.get("equipment"))
        if equipment_name not in equipment_map:
            equipment = EquipmentModel(name=equipment_name, slug=generate_slug(equipment_name), category=equipment_name.lower().replace(" ", "_"), description=f"{equipment_name} equipment")
            db.add(equipment); db.flush(); equipment_map[equipment_name] = equipment
        primary_name = str((raw.get("primaryMuscles") or ["Full Body"])[0]).replace("abdominals", "Core").replace("lats", "Back").replace("traps", "Shoulders").replace("middle back", "Back").replace("lower back", "Lower Back").title()
        secondary_names = [str(x).replace("abdominals", "Core").replace("lats", "Back").replace("traps", "Shoulders").replace("middle back", "Back").replace("lower back", "Lower Back").title() for x in (raw.get("secondaryMuscles") or [])]
        for muscle_name in [primary_name, *secondary_names]:
            if muscle_name not in muscle_map:
                muscle = MuscleGroupModel(name=muscle_name, slug=generate_slug(muscle_name), body_region="general", description=f"{muscle_name} muscle group")
                db.add(muscle); db.flush(); muscle_map[muscle_name] = muscle
        category = str(raw.get("category") or "strength").lower()
        exercise_type = category if category in VALID_TYPES else "strength"
        difficulty = str(raw.get("level") or "beginner").lower()
        if difficulty not in {"beginner", "intermediate", "advanced"}: difficulty = "beginner"
        mechanic = str(raw.get("mechanic") or "compound").lower()
        instructions = "\n".join(str(x) for x in (raw.get("instructions") or []))
        item = ExerciseModel(name=name, slug=slug, description=f"A {difficulty} {mechanic} {exercise_type} movement.", instructions=instructions or "Perform the movement with controlled form and return to the starting position.", difficulty_level=difficulty, exercise_type=exercise_type, force_type=raw.get("force"), mechanic_type=mechanic, equipment_id=equipment_map[equipment_name].id, is_compound=mechanic == "compound")
        db.add(item); db.flush()
        rows = [{"exercise_id": item.id, "muscle_group_id": muscle_map[primary_name].id, "role": "primary"}]
        rows += [{"exercise_id": item.id, "muscle_group_id": muscle_map[x].id, "role": "secondary"} for x in dict.fromkeys(secondary_names) if x != primary_name]
        db.execute(exercise_muscle_association.insert(), rows)
        existing.add(name.lower()); existing_slugs.add(slug); added += 1
    return added

def main() -> None:
    db = SessionLocal()
    try:
        muscle_map = {}
        for name, region in MUSCLES:
            item = db.scalar(select(MuscleGroupModel).where(MuscleGroupModel.name == name))
            if not item:
                item = MuscleGroupModel(name=name, slug=generate_slug(name), body_region=region, description=f"{name} muscle group")
                db.add(item); db.flush()
            muscle_map[name] = item
        equipment_map = {}
        for name, category in EQUIPMENT:
            item = db.scalar(select(EquipmentModel).where(EquipmentModel.name == name))
            if not item:
                item = EquipmentModel(name=name, slug=generate_slug(name), category=category, description=f"{name} equipment")
                db.add(item); db.flush()
            equipment_map[name] = item
        for name, primary, secondary, equipment, ex_type, difficulty, force, mechanic, compound in SPECS:
            item = db.scalar(select(ExerciseModel).where(ExerciseModel.name == name))
            if not item:
                item = ExerciseModel(name=name, slug=generate_slug(name), description=f"A {difficulty} {mechanic} movement for the {primary.lower()}.", instructions=f"Set up with {equipment.lower()}, perform the movement with controlled form, and return to the starting position.", difficulty_level=difficulty, exercise_type=ex_type, force_type=force, mechanic_type=mechanic, equipment_id=equipment_map[equipment].id, is_compound=compound)
                db.add(item); db.flush()
            else:
                item.equipment_id = equipment_map[equipment].id; item.is_active = True
            db.execute(delete(exercise_muscle_association).where(exercise_muscle_association.c.exercise_id == item.id))
            rows = [{"exercise_id": item.id, "muscle_group_id": muscle_map[primary].id, "role": "primary"}]
            if secondary: rows.append({"exercise_id": item.id, "muscle_group_id": muscle_map[secondary].id, "role": "secondary"})
            db.execute(exercise_muscle_association.insert(), rows)
        imported = import_public_metadata(db, muscle_map, equipment_map)
        db.commit()
        exercise_count = db.scalar(select(func.count()).select_from(ExerciseModel))
        muscle_count = db.scalar(select(func.count()).select_from(MuscleGroupModel))
        equipment_count = db.scalar(select(func.count()).select_from(EquipmentModel))
        print(f"Seed complete: {exercise_count} exercises, {muscle_count} muscle groups, {equipment_count} equipment records ({imported} new metadata records this run).")
    finally:
        db.close()

if __name__ == "__main__": main()
