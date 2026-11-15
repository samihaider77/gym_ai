# Meal Snap (Food page)

Members photograph a meal, check the foods and portions, and save it. The Food page shows the day's calories and
protein against their targets, with a one-line tip in English or Roman Urdu.

## How a photo becomes calories

1. The app shrinks the photo to about 1000 px and sends it to `POST /api/v1/ai/meals/analyze`.
2. `ai_coach/infrastructure/vision.py` asks Google Gemini to list **every** food and drink on the plate with an English
   and a Roman Urdu name, an estimated weight in grams and, for our 35 desi dishes, the dish key and a count in its
   household unit (roti, katori, plate).
3. Each food is priced from our data, in this order:
   - **Desi table** (`backend/data/desi_foods.json`, 35 dishes with household units).
   - **USDA table** (`backend/data/usda_foods.json`, ~5,400 foods): name matching in `foods.match()`, one "serving"
     of the estimated weight.
   - **Estimate**: only if neither table has the food, the AI's own per-100 g values are used and the item is marked
     "estimate" in the app.
4. The member edits portions (or adds foods from the desi list or the search box) and saves. The server recomputes
   every number on save. Photos are not stored.

Both tables come from USDA FoodData Central, FNDDS 2021-2023 (public domain); `scripts/build_desi_foods.py` rebuilds
them from the FNDDS JSON download. The app itself does not show the data source.

## Accuracy check

`scripts/eval_meal_snap.py` runs real multi-dish plate photos through the same code and counts which food types were
found. Test set: 40 plates (115 food types) from the SOHL Multi-Dish Indian Food dataset (MIT licence). Note that the
dataset's label files number classes alphabetically, not in the order its README lists them; the script maps this.

| Version | Foods seen | Foods that got calories |
|---|---|---|
| 35 desi dishes only | 85.8% | 56.6% |
| Every food + USDA lookup (current) | 89.6% | 89.6% |

About 10% of priced items used the AI's estimate (mostly chutneys and regional snacks not in USDA).

## Setup

1. `cd backend && .venv/Scripts/python.exe -m alembic upgrade head` (adds the `meal_logs` table). Run it against the
   production database before deploying.
2. Get a free Gemini API key at https://aistudio.google.com/apikey and set `GEMINI_API_KEY` in `backend/.env` (and in
   the backend's Vercel environment variables). Without it, the Food page works with manual entry only.
3. `GEMINI_MODEL` defaults to `gemini-flash-lite-latest`, which has the largest free daily quota.

## API (all need a signed-in user)

| Method | Path | What it does |
|---|---|---|
| GET | `/api/v1/ai/foods` | The desi food table |
| GET | `/api/v1/ai/foods/search?q=` | Search desi and USDA foods by name |
| POST | `/api/v1/ai/meals/analyze` | Photo (base64 JPEG/PNG/WebP) to suggested items; saves nothing |
| POST | `/api/v1/ai/meals` | Save a meal; the server recomputes all macros |
| GET | `/api/v1/ai/meals/day?start=&end=` | Meals, totals, targets and tip for one local day |
| DELETE | `/api/v1/ai/meals/{id}` | Delete a meal |
