"""Import a locally downloaded Vital Animations MP4/JSON package into GymAI."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import imageio_ffmpeg
from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402,F401
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: E402,F401


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MEDIA_ROOT = ROOT / "frontend" / "public" / "exercise-media" / "vital-animations"
DEFAULT_MAPPING = Path(__file__).with_name("vital-animations-free50-mapping.json")
PROVIDER = "Vital Animations"
HIDDEN_STATUSES = {"failed", "deprecated", "rejected"}


def normalize_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def extract_zip_safely(archive_path: Path, destination: Path) -> None:
    root = destination.resolve()
    try:
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (root / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise SystemExit(f"Unsafe archive entry outside destination: {member.filename}")
            archive.extractall(root)
    except BadZipFile as exc:
        raise SystemExit(f"Invalid ZIP archive: {archive_path}") from exc


def iter_metadata_records(source_root: Path):
    for metadata_file in sorted(source_root.rglob("*.json")):
        try:
            payload = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records = payload if isinstance(payload, list) else [payload]
        for record in records:
            if isinstance(record, dict) and record.get("id") and record.get("name"):
                yield metadata_file, record


def build_mp4_index(source_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in source_root.rglob("*.mp4"):
        index.setdefault(path.name.casefold(), []).append(path)
    return index


def find_mp4(metadata_file: Path, external_id: str, index: dict[str, list[Path]]) -> Path | None:
    matches = sorted(index.get(f"{external_id}.mp4".casefold(), []))
    nearby = [path for path in matches if metadata_file.parent in path.parents]
    if len(nearby) == 1:
        return nearby[0]
    if nearby:
        return min(nearby, key=lambda path: len(path.parts))
    return matches[0] if len(matches) == 1 else None


def load_mapping(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid mapping file {path}: {exc}") from exc
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
    ):
        raise SystemExit("Mapping file must be a JSON object of source ID to GymAI name")
    return payload


def transcode(source: Path, target: Path, poster: Path, size: int, crf: int) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_target = target.with_name(f"{target.stem}.tmp{target.suffix}")
    video_filter = (
        f"scale={size}:{size}:force_original_aspect_ratio=decrease,"
        f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=white"
    )
    result = subprocess.run(
        [
            ffmpeg, "-y", "-i", str(source), "-an", "-vf", video_filter,
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary_target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        temporary_target.unlink(missing_ok=True)
        raise RuntimeError(f"FFmpeg transcode failed for {source}: {result.stderr[-1200:]}")
    temporary_target.replace(target)

    result = subprocess.run(
        [
            ffmpeg, "-y", "-ss", "0.5", "-i", str(target), "-frames:v", "1",
            "-update", "1", "-c:v", "libwebp", "-quality", "78", str(poster),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"FFmpeg poster extraction failed for {target}: {result.stderr[-1200:]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import licensed Vital Animations MP4 media")
    parser.add_argument("--source", required=True, type=Path, help="Extracted package directory or ZIP")
    parser.add_argument("--mapping-file", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--size", type=int, default=720, help="Square output resolution")
    parser.add_argument("--crf", type=int, default=28, help="H.264 quality (lower is larger/better)")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.source.expanduser().resolve()
    temporary_source: tempfile.TemporaryDirectory[str] | None = None
    if source_path.is_dir():
        source_root = source_path
    elif source_path.is_file() and source_path.suffix.casefold() == ".zip":
        temporary_source = tempfile.TemporaryDirectory(prefix="gym-ai-vital-")
        source_root = Path(temporary_source.name)
        extract_zip_safely(source_path, source_root)
    else:
        raise SystemExit(f"Source must be a directory or ZIP: {source_path}")
    if args.size <= 0:
        raise SystemExit("--size must be positive")
    if not 0 <= args.crf <= 51:
        raise SystemExit("--crf must be between 0 and 51")

    mapping = load_mapping(args.mapping_file.resolve() if args.mapping_file else None)
    mp4_index = build_mp4_index(source_root)
    records = list(iter_metadata_records(source_root))
    if not records:
        raise SystemExit(f"No exercise JSON records found under: {source_root}")

    imported = 0
    skipped = 0
    invalid = 0
    assigned_exercise_ids = set()

    with SessionLocal() as db:
        exercises = db.scalars(
            select(ExerciseModel).where(ExerciseModel.is_active.is_(True))
        ).all()
        by_name: dict[str, list[ExerciseModel]] = {}
        for exercise in exercises:
            by_name.setdefault(normalize_name(exercise.name), []).append(exercise)

        for metadata_file, record in records:
            external_id = str(record.get("id", "")).strip()
            source_name = str(record.get("name", "")).strip()
            target_name = mapping.get(external_id, source_name)
            matches = by_name.get(normalize_name(target_name), [])
            source_mp4 = find_mp4(metadata_file, external_id, mp4_index)
            if len(matches) != 1 or source_mp4 is None:
                skipped += 1
                continue
            exercise = matches[0]
            if exercise.id in assigned_exercise_ids:
                invalid += 1
                print(f"[-] Duplicate target mapping ignored: {external_id} -> {exercise.name}")
                continue
            assigned_exercise_ids.add(exercise.id)

            target_dir = PUBLIC_MEDIA_ROOT / external_id
            media_url = f"/exercise-media/vital-animations/{external_id}/animation.mp4"
            poster_url = f"/exercise-media/vital-animations/{external_id}/poster.webp"
            existing = db.scalars(
                select(ExerciseMediaModel).where(
                    ExerciseMediaModel.exercise_id == exercise.id,
                    ExerciseMediaModel.provider == PROVIDER,
                )
            ).all()
            row = existing[0] if existing else ExerciseMediaModel(
                exercise_id=exercise.id,
                media_type="video",
                media_url=media_url,
            )

            if not args.dry_run:
                transcode(
                    source_mp4,
                    target_dir / "animation.mp4",
                    target_dir / "poster.webp",
                    args.size,
                    args.crf,
                )
                _, duration = imageio_ffmpeg.count_frames_and_secs(str(target_dir / "animation.mp4"))
                for media_row in exercise.media:
                    if media_row.status.lower() not in HIDDEN_STATUSES:
                        media_row.is_primary = False
                for duplicate in existing[1:]:
                    duplicate.status = "deprecated"
                    duplicate.is_primary = False

                row.media_type = "video"
                row.media_url = media_url
                row.thumbnail_url = poster_url
                row.poster_url = poster_url
                row.provider = PROVIDER
                row.license = "Vital Animations commercial use license"
                row.attribution = "Exercise animation by Vital Animations (free pack)"
                row.width = args.size
                row.height = args.size
                row.duration = max(1, round(duration))
                row.duration_ms = max(1, round(duration * 1000))
                row.camera_angle = "Instructional view"
                row.format = "mp4"
                row.version = 1
                row.status = "ready"
                row.is_primary = True
                db.add(row)

            imported += 1
            print(f"[+] {'Would import' if args.dry_run else 'Imported'} {external_id} -> {exercise.name}")

        if args.dry_run:
            db.rollback()
        else:
            db.commit()

    if temporary_source is not None:
        temporary_source.cleanup()
    print(f"{'Dry run' if args.dry_run else 'Import'} complete: imported={imported}, skipped={skipped}, invalid={invalid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
