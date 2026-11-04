"""Add the 3D character renders (.tools/3d/shaded_render.py) to the exercise library.

Run from backend/: python scripts/import_3d_renders.py [renders folder] [--dry-run]
The folder (default ../.tools/3d/shaded) holds <slug>/frames/NN.png, one smooth start -> end movement per
exercise. Each becomes a looping MP4 (forwards, hold, back) with the start frame as poster, provider "GymAI3D".
Exercises are matched through exercise-poses.json by their English name. Safe to re-run; only finished
renders are imported, so it can run again while rendering continues.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_open_exercise_media as media  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
POSES = ROOT / "tools" / "ai-drawings" / "exercise-poses.json"
FRAMES = 16
SIZE = 480
FPS, HOLD = 15, 6
LICENSE = "CC0 1.0"
ATTRIBUTION = "“{name}” 3D render made by GymAI with a MakeHuman (MPFB) character, CC0 1.0"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_loop(frames: list[Path], folder: Path) -> dict:
    """Frames -> looping MP4 on white plus a poster; same output shape as media.render()."""
    target, poster = folder / "animation.mp4", folder / "poster.webp"
    url_base = f"/exercise-media/gymai3d/{folder.name}"
    if not target.exists():
        folder.mkdir(parents=True, exist_ok=True)
        stills = [media.load_frame(f, SIZE) for f in frames]
        sequence = [stills[0]] * HOLD + stills[1:] + [stills[-1]] * HOLD + stills[-2:0:-1]
        work = folder / ".frames"
        work.mkdir(exist_ok=True)
        try:
            for index, still in enumerate(sequence):
                still.save(work / f"{index:03d}.png")
            media.run_ffmpeg(["-framerate", str(FPS), "-i", str(work / "%03d.png"), "-c:v", "libx264",
                              "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                              str(target.with_suffix(".tmp.mp4"))])
            target.with_suffix(".tmp.mp4").replace(target)
        finally:
            for file in work.glob("*.png"):
                file.unlink()
            work.rmdir()
        stills[0].save(poster, "WEBP", quality=82)
    duration = (HOLD * 2 + (FRAMES - 1) + (FRAMES - 2)) / FPS
    return dict(media_type="video", format="mp4", media_url=f"{url_base}/animation.mp4",
                poster_url=f"{url_base}/poster.webp", duration=duration, width=SIZE, height=SIZE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default=str(ROOT / ".tools" / "3d" / "shaded"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    names = {slugify(s["name"]): s["name"] for s in json.loads(POSES.read_text(encoding="utf-8"))}
    added, missing, unfinished, touched = 0, [], 0, set()
    with media.SessionLocal() as db:
        for folder in sorted(p for p in Path(args.source).iterdir() if p.is_dir() and not p.name.startswith("_")):
            frames = [folder / "frames" / f"{i:02d}.png" for i in range(FRAMES)]
            if not all(f.exists() for f in frames):
                unfinished += 1
                continue
            name = names.get(folder.name)
            exercise = name and db.scalar(select(media.ExerciseModel).where(
                func.lower(media.ExerciseModel.name) == name.lower(), media.ExerciseModel.is_active.is_(True)))
            if not exercise:
                missing.append(name or folder.name)
                continue
            if args.dry_run:
                print(exercise.name)
                continue
            item = media.SourceItem(provider="GymAI3D", source_id=folder.name, name=exercise.name, kind="loop",
                                    urls=[], license=LICENSE, attribution=ATTRIBUTION.format(name=exercise.name))
            fields = render_loop(frames, media.PUBLIC_MEDIA_ROOT / "gymai3d" / f"{folder.name}-loop")
            media.upsert_media(db, exercise, item, fields, SIZE, all_styles=False)
            touched.add(exercise.id)
            added += 1
            if added % 50 == 0:
                print(f"{added} imported...", flush=True)
        if not args.dry_run:
            db.flush()  # the session does not autoflush; choose_primaries must see the new rows
            media.choose_primaries(db, touched)
            db.commit()
    print(f"\n{added} renders added, {unfinished} still rendering, {len(missing)} not matched.")
    for name in missing:
        print("  not matched:", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
