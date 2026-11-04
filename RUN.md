# Running GymAI locally (Windows)

## Quick start
1. Start Docker Desktop.
2. Double-click `start.bat` in the project folder (or run `.\start.ps1` in PowerShell).

The script starts the database, installs anything missing on the first run, applies migrations,
then opens the backend and the frontend in two new windows and opens the app in your browser.
The frontend uses the first free port from 3000 to 3003. Close the two windows to stop the app.
Run `start.bat -Setup` to reinstall dependencies and re-seed exercises.

The manual steps below do the same thing one at a time.

## Prerequisites
- Docker Desktop (for PostgreSQL)
- Python 3.10+ and [uv](https://docs.astral.sh/uv/) (or plain `pip`)
- Node.js 18+

## 1. Database
From the project root:
```bash
docker compose up -d db
```
Postgres listens on `127.0.0.1:5433` (see `backend/.env`).

## 2. Backend (FastAPI, port 8000)
```bash
cd backend
uv venv .venv --python 3.12
uv pip install -p .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe scripts/seed_exercises.py
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```
Check http://localhost:8000/health and the API docs at http://localhost:8000/docs.

## 3. Exercise media (free and openly licensed)
```bash
cd backend
.venv/Scripts/python.exe scripts/import_open_exercise_media.py --source all
```
- Downloads wger.de and Everkinetic media (Creative Commons), renders small MP4 loops and webp
  images into `frontend/public/exercise-media/`, and stores the licence and author credit on every row.
- `--skip-videos` skips the ~35 MB wger source videos; `--no-create` only attaches media to
  exercises that already exist; `--dry-run` shows the matches only.
- Safe to re-run: finished files are skipped, failures are retried, and images too small to be a
  real demo (logos) are rejected.
- Source downloads are cached in `backend/.media-cache/`, which you can delete afterwards.
- `scripts/normalize_catalog.py` merges duplicate equipment (e.g. "Dumbbells" into "Dumbbell") and
  title-cases exercise names. The seed and import scripts already use the same naming rules
  (`scripts/catalog_names.py`), so you only need it for older databases. `--dry-run` previews.
- `scripts/merge_duplicate_exercises.py` merges near-duplicates such as "Hammer Curl" and
  "Hammer Curls". Workout entries, media and muscles move to the kept exercise; the others are
  deactivated, not deleted. Run it after an import; `--dry-run` lists the groups first.
- Only one demo style is shown: the black-and-white Everkinetic line drawings (the largest
  set in one look). Media in other styles (photos, real videos, other illustrators) is kept
  but hidden. The importer applies this rule; `scripts/set_media_style.py` applies it to an
  existing database, and `--all-styles` on either script shows every style again.

## 4. Frontend (Next.js, port 3000)
```bash
cd frontend
npm ci
npm run dev
```
Open http://localhost:3000 and create an account (or use the local test account in
`backend/.env.example`). For a production build use `npm run build`, then `npm start`.

If port 3000 is taken, run `npx next dev -p 3002` and make sure that origin is listed in
`CORS_ORIGINS` in `backend/.env` (3000-3003 already are).

## Frontend structure
- `src/app/(auth)`: sign in and register
- `src/app/(app)`: dashboard, exercises (library + detail), workouts (plans, days), sessions
  (live set logging), progress (body weight chart), profile
- `src/components`: app shell, exercise player and thumbnails, dialogs, toasts, form fields
- `src/lib`: API client (`api.ts`), types, data hooks
- Theme: solid surfaces, one red accent, light and dark mode (follows the system, toggle in the
  sidebar). Tokens live in `src/app/globals.css`.
- Language: English or Roman Urdu (switch in the sidebar and the phone top bar). It changes only
  exercise names and their "How to do it" steps; the rest of the app stays English. The text lives
  in the database (`name_ur`, `instructions_ur`), loaded from `backend/data/exercises_roman_urdu.json`
  by `scripts/import_roman_urdu.py`, so it works offline. Untranslated exercises show English.

## Everything with Docker
```bash
docker compose up --build
```
