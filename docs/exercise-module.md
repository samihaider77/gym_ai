# GymAI Exercise Module V1

## Data structure

`exercises.equipment_id` is a nullable foreign key to `equipment.id` with `SET NULL` deletion behavior. Exercise-to-muscle membership is stored in `exercise_muscles`, which contains `exercise_id`, `muscle_group_id`, and a `role` of `primary` or `secondary`. The existing `workout_exercises.exercise_id` foreign key remains unchanged.

## Seed data

The curated, original starter library is seeded by:

```powershell
cd backend
python scripts/seed_exercises.py
```

The script is deterministic and idempotent. It creates 81 exercises, 14 muscle groups, and 12 equipment records. No external dataset is copied; therefore no third-party dataset attribution is required.

## API filters

`GET /api/v1/exercises` supports `page`, `page_size`, `search`, `exercise_type`, `difficulty_level`, `equipment_id`, `muscle_group_id`, `is_compound`, and `is_active`. Search matches exercise names and descriptions case-insensitively.

## Frontend structure

The dedicated feature lives under `frontend/src/features/exercises/` with its own API client, types, hooks, filters, cards, detail view, deterministic explanation, match label, and alternatives. The library is at `/exercises`; details are at `/exercises/{id}`.
