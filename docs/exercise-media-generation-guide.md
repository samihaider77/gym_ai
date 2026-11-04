# Legacy media generation guide

> The low-poly outputs from this pipeline are retired and must not be registered for user-facing display. Use the reviewed local asset importer documented in `exercisedb-media-import.md` for ExerciseDB-style anatomical visuals.

Prepare a deterministic manifest:

```powershell
python tools/exercise-animation/generate_exercise.py --exercise barbell-bench-press
python tools/exercise-animation/generate_exercise.py --exercise barbell-bench-press --render
```

The render command requires Blender 3.x on `PATH`. It produces `poster.png` and `animation.mp4` in a versioned directory. Validate dimensions, file size, playback, duration, camera angle, equipment contact, and movement form before registering media with `status=ready`; otherwise leave it `review_required` or `failed`.
