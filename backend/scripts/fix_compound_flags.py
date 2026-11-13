"""Correct the compound / isolation label of exercises from the movement in their name.

Run from backend/: python scripts/fix_compound_flags.py [--dry-run]
Some imported exercises carry the wrong label (e.g. "Decline Dumbbell Flyes" marked compound). Flyes, curls,
raises, extensions, pushdowns, shrugs and core work use one joint; presses, rows, squats, deadlifts, lunges,
pull-ups, dips and push-ups use several. Exercises whose name matches none of these keep their label. The same
rules are in frontend/src/lib/suggest.ts. Uses DATABASE_URL like the API, so it also fixes the live database.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_open_exercise_media as media  # noqa: E402
from sqlalchemy import select  # noqa: E402

# First match wins, in this order (a leg curl is not a biceps curl). Keep in step with suggest.ts.
MOVEMENTS = [
    (r"\bleg curl|hamstring curl|lying curl|seated curl\b", False),
    (r"\bleg extension", False),
    (r"\bcalf|calves\b", False),
    (r"\bfl(y|ye|yes|ies)\b|cable crossover|pec deck|butterfly", False),
    (r"pullover|straight-?arm", False),
    (r"lateral raise|side raise|\by raise", False),
    (r"front raise", False),
    (r"rear delt|reverse fly|face pull", False),
    (r"shrug", False),
    (r"pushdown|push-down|triceps?\b.*kickback|triceps? press|skull|triceps? extension|overhead extension|french press|tate press|jm press", False),
    (r"\bcurl", False),
    (r"wrist", False),
    (r"crunch|sit-?up|leg raise|knee raise|plank|rollout|russian twist|hollow|v-up|mountain climber|bicycle", False),
    (r"hip thrust|glute bridge|bridge", True),
    (r"abduct|adduct|clamshell|fire hydrant|donkey kick|kickback", False),
    (r"\bdips?\b", True),
    (r"push-?ups?|press-?ups?", True),
    (r"pull-?ups?|chin-?ups?|pulldown|pull-down", True),
    (r"\brows?\b|rowing", True),
    (r"deadlift|rdl|good morning|rack pull", True),
    (r"lunge|split squat|step-?up", True),
    (r"squat|leg press|hack", True),
    (r"overhead press|shoulder press|military|arnold|push press", True),
    (r"press", True),
]


# Stretches, foam rolling and jumps are not strength movements: their label is left alone.
SKIP = r"stretch|smr|foam|jump|hop|bound"


def compound_from_name(name: str):
    if re.search(SKIP, name, re.IGNORECASE):
        return None
    for pattern, compound in MOVEMENTS:
        if re.search(pattern, name, re.IGNORECASE):
            return compound
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changed = 0
    with media.SessionLocal() as db:
        for exercise in db.scalars(select(media.ExerciseModel).where(media.ExerciseModel.is_active.is_(True))):
            compound = compound_from_name(exercise.name)
            if compound is None or compound == exercise.is_compound:
                continue
            print(f"{exercise.name}: {'compound' if exercise.is_compound else 'isolation'} -> "
                  f"{'compound' if compound else 'isolation'}")
            changed += 1
            if not args.dry_run:
                exercise.is_compound = compound
                exercise.mechanic_type = "compound" if compound else "isolation"
        if not args.dry_run:
            db.commit()
    print(f"\n{changed} exercises {'would change' if args.dry_run else 'corrected'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
