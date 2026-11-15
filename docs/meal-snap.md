# Meal Snap (Food page)

Members photograph a meal, check the foods and portions, and save it. The Food page shows the day's calories and
protein against their targets, with a one-line tip in English or Roman Urdu.

## How it works

- **Food table:** `backend/data/desi_foods.json`, 35 everyday Pakistani foods (roti, daal, karahi, biryani, chai…)
  with household units (roti, katori, plate, piece). Every number comes from USDA FoodData Central, FNDDS 2021-2023
  (public domain). Rebuild it with `python scripts/build_desi_foods.py <surveyDownload.json>`.
- **Photo recognition:** `ai_coach/infrastructure/vision.py` sends the photo to Google Gemini with the list of food
  keys and asks only *which foods and how many units*. Calories and macros are always computed from the food table.
- **Targets:** Mifflin-St Jeor calories x activity, adjusted for the goal; protein 1.4-2.0 g per kg by goal
  (`ai_coach/domain/nutrition.py`). They need weight, height and date of birth in the profile.
- Photos are not stored.

## Setup

1. `cd backend && .venv/Scripts/python.exe -m alembic upgrade head` (adds the `meal_logs` table). Run it against the
   production database before deploying.
2. Optional: get a free Gemini API key at https://aistudio.google.com/apikey and set `GEMINI_API_KEY` in
   `backend/.env` (and in the backend's Vercel environment variables). Without it, the Food page works with manual
   entry and says photo recognition is off.
3. `GEMINI_MODEL` defaults to `gemini-flash-lite-latest`, which has the largest free daily quota.

## API (all need a signed-in user)

| Method | Path | What it does |
|---|---|---|
| GET | `/api/v1/ai/foods` | The food table |
| POST | `/api/v1/ai/meals/analyze` | Photo (base64 JPEG/PNG/WebP) to suggested items; saves nothing |
| POST | `/api/v1/ai/meals` | Save a meal; the server recomputes all macros |
| GET | `/api/v1/ai/meals/day?start=&end=` | Meals, totals, targets and tip for one local day |
| DELETE | `/api/v1/ai/meals/{id}` | Delete a meal |
