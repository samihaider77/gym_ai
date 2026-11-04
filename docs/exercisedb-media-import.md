# ExerciseDB local media import

GymAI imports ExerciseDB visuals only from a package already present on local disk. The importer does not access the network. Confirm the project has a valid ExerciseDB.io license or other permission before importing or deploying the media.

## Package pairing

Each exercise JSON object supplies an `id` and `name`. Objects may live in individual files or in a JSON array. The ID pairs metadata to the GIF filename:

```text
0025.json
0025-720.gif
0025-360.gif   # optional thumbnail
```

`exerciseList.json` is intentionally ignored because it contains names without IDs. The importer matches the JSON exercise name to a GymAI exercise by normalized exact name; it does not guess near matches. For the requested resolution it looks for `{id}-{resolution}.gif`, then `{id}.gif`, then selects the nearest uniquely named local resolution. Missing files are reported and never downloaded or inferred. The package is indexed once, so a full library does not trigger a filesystem scan for every exercise.

## Run the importer

From the repository root:

```powershell
python backend/scripts/import_exercisedb_media.py --source-dir sample-set/sample-set --preferred-resolution 720 --dry-run
python backend/scripts/import_exercisedb_media.py --source-dir sample-set/sample-set --preferred-resolution 720
python backend/scripts/import_exercisedb_media.py --source sample-set.zip --preferred-resolution 720 --dry-run
```

`--source` and `--source-dir` are aliases and accept either an extracted directory or a ZIP file. ZIP entries are validated against path traversal before extraction to a temporary directory. The preferred resolution defaults to `720`, which is appropriate for the exercise detail view. Pass a different installed resolution when required. If the exact size is absent, the closest available size is used. If `{id}-360.gif` is present, it is copied and registered as thumbnail metadata.

For each exact match, the command:

1. copies only discovered local GIF files to `frontend/public/exercise-media/exercisedb/{id}/`;
2. extracts frame one to `poster.png` with Pillow;
3. records GIF width, height, total duration, provider, attribution, and file URLs;
4. marks the ExerciseDB record `ready` and primary;
5. globally marks every old `GymAI Visual Pipeline` row `deprecated` and non-primary.

The command is idempotent: rerunning it updates the existing ExerciseDB media record and safely refreshes the copied files. Reduced-motion users see `poster.png`; other users receive the animated GIF.

## Require complete same-character coverage

After importing, run the coverage gate:

```powershell
python backend/scripts/verify_exercise_media_coverage.py
```

The command exits non-zero until every active GymAI exercise has a primary, ready ExerciseDB GIF. It lists missing exercise names and IDs so partial imports cannot be mistaken for completion. Use `--allow-incomplete` only for a progress report:

```powershell
python backend/scripts/verify_exercise_media_coverage.py --allow-incomplete --list-limit 25
```

The supplied sample package contains only exercise `0025`, so it is intentionally insufficient for the all-exercise gate. Full coverage requires the complete licensed same-character JSON/GIF package and reviewed mappings for GymAI names that do not exactly match the source names.
