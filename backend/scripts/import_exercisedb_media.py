"""Import locally supplied ExerciseDB GIFs into GymAI.

This command intentionally performs no network requests. Exercise metadata and
GIFs must already exist in ``--source-dir`` under the user's ExerciseDB license.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from PIL import Image, ImageSequence
from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.db.session import SessionLocal  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402,F401
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: E402
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: E402,F401


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MEDIA_ROOT = ROOT / "frontend" / "public" / "exercise-media" / "exercisedb"
PROVIDER = "ExerciseDB.io"
REJECTED_PROVIDER = "GymAI Visual Pipeline"
HIDDEN_STATUS = "deprecated"


def normalize_name(value: str) -> str:
    """Normalize names for conservative, exact matching."""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def build_asset_index(source_dir: Path) -> dict[str, list[Path]]:
    """Index local files once so large licensed packages do not require repeated scans."""
    index: dict[str, list[Path]] = {}
    for path in source_dir.rglob("*"):
        if path.is_file():
            index.setdefault(path.name.casefold(), []).append(path)
    return index


def find_asset(
    metadata_file: Path,
    filename: str,
    asset_index: dict[str, list[Path]],
) -> Path | None:
    beside_metadata = metadata_file.parent / filename
    if beside_metadata.is_file():
        return beside_metadata
    matches = sorted(asset_index.get(filename.casefold(), []))
    return matches[0] if len(matches) == 1 else None


def find_best_gif(
    metadata_file: Path,
    external_id: str,
    preferred_resolution: int,
    asset_index: dict[str, list[Path]],
) -> Path | None:
    """Choose an exact resolution, an unsuffixed GIF, or the nearest local size."""
    exact = find_asset(
        metadata_file,
        f"{external_id}-{preferred_resolution}.gif",
        asset_index,
    )
    if exact:
        return exact
    unsuffixed = find_asset(metadata_file, f"{external_id}.gif", asset_index)
    if unsuffixed:
        return unsuffixed

    pattern = re.compile(rf"^{re.escape(external_id)}-(\d+)\.gif$", re.IGNORECASE)
    candidates: list[tuple[int, int, Path]] = []
    for filename, paths in asset_index.items():
        match = pattern.fullmatch(filename)
        if not match or len(paths) != 1:
            continue
        resolution = int(match.group(1))
        candidates.append((abs(resolution - preferred_resolution), -resolution, paths[0]))
    return min(candidates, default=(0, 0, None))[2]


def extract_zip_safely(archive_path: Path, destination: Path) -> None:
    """Extract a local package while rejecting path traversal entries."""
    root = destination.resolve()
    try:
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (root / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise SystemExit(
                        f"Unsafe archive entry outside destination: {member.filename}"
                    )
            archive.extractall(root)
    except BadZipFile as exc:
        raise SystemExit(f"Invalid ZIP archive: {archive_path}") from exc


def iter_metadata_records(metadata_files: list[Path]):
    """Yield exercise objects from individual JSON files or JSON object arrays."""
    for metadata_file in metadata_files:
        try:
            payload = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            yield metadata_file, None, str(exc)
            continue

        if isinstance(payload, dict):
            yield metadata_file, payload, None
            continue
        if isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
            if not records:
                yield metadata_file, None, "JSON array contains no exercise objects"
                continue
            for record in records:
                yield metadata_file, record, None
            continue
        yield metadata_file, None, "JSON root must be an object or array of objects"


def inspect_gif(path: Path) -> tuple[int, int, int, int]:
    with Image.open(path) as image:
        durations = [int(frame.info.get("duration", image.info.get("duration", 0)) or 0) for frame in ImageSequence.Iterator(image)]
        duration_ms = sum(durations)
        return image.width, image.height, duration_ms, getattr(image, "n_frames", len(durations))


def write_poster(gif_path: Path, poster_path: Path) -> None:
    with Image.open(gif_path) as image:
        image.seek(0)
        frame = image.convert("RGBA")
        background = Image.new("RGBA", frame.size, "white")
        background.alpha_composite(frame)
        background.convert("RGB").save(poster_path, "PNG", optimize=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import licensed, local ExerciseDB GIF media.")
    parser.add_argument(
        "--source-dir",
        "--source",
        dest="source",
        required=True,
        type=Path,
        help="Directory or ZIP containing local ExerciseDB JSON/GIF files",
    )
    parser.add_argument("--preferred-resolution", type=int, default=720, help="GIF resolution suffix to import (default: 720)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without copying files or changing the database")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.source.expanduser().resolve()
    temporary_source: tempfile.TemporaryDirectory[str] | None = None
    if source_path.is_dir():
        source_dir = source_path
    elif source_path.is_file() and source_path.suffix.casefold() == ".zip":
        temporary_source = tempfile.TemporaryDirectory(prefix="gym-ai-exercisedb-")
        source_dir = Path(temporary_source.name)
        extract_zip_safely(source_path, source_dir)
        print(f"[source] Extracted local ZIP package: {source_path}")
    else:
        raise SystemExit(f"Source must be a directory or ZIP archive: {source_path}")
    if args.preferred_resolution <= 0:
        raise SystemExit("--preferred-resolution must be a positive integer")

    metadata_files = sorted(
        path for path in source_dir.rglob("*.json")
        if path.name.casefold() != "exerciselist.json"
    )
    if not metadata_files:
        raise SystemExit(f"No per-exercise JSON files found under: {source_dir}")
    asset_index = build_asset_index(source_dir)

    registered = 0
    skipped = 0
    invalid = 0
    retired = 0

    with SessionLocal() as db:
        exercises_by_name: dict[str, list[ExerciseModel]] = {}
        for exercise in db.scalars(select(ExerciseModel)).all():
            exercises_by_name.setdefault(normalize_name(exercise.name), []).append(exercise)

        rejected_rows = db.scalars(
            select(ExerciseMediaModel).where(ExerciseMediaModel.provider == REJECTED_PROVIDER)
        ).all()
        for row in rejected_rows:
            if row.status != HIDDEN_STATUS or row.is_primary:
                retired += 1
            if not args.dry_run:
                row.status = HIDDEN_STATUS
                row.is_primary = False
        print(f"[maintenance] {retired} legacy '{REJECTED_PROVIDER}' record(s) will be retired")

        for metadata_file, metadata, metadata_error in iter_metadata_records(metadata_files):
            if metadata_error or metadata is None:
                invalid += 1
                print(f"[-] Invalid metadata {metadata_file}: {metadata_error}")
                continue

            external_id = str(metadata.get("id", "")).strip()
            source_name = str(metadata.get("name", "")).strip()
            if not external_id or not source_name or not re.fullmatch(r"[A-Za-z0-9_-]+", external_id):
                invalid += 1
                print(f"[-] Invalid or missing id/name in {metadata_file}")
                continue

            source_gif = find_best_gif(
                metadata_file,
                external_id,
                args.preferred_resolution,
                asset_index,
            )
            if source_gif is None:
                skipped += 1
                print(f"[-] No local GIF for {external_id} ({source_name})")
                continue

            matches = exercises_by_name.get(normalize_name(source_name), [])
            if len(matches) != 1:
                skipped += 1
                reason = "no exact GymAI name match" if not matches else "ambiguous normalized GymAI name"
                print(f"[-] Skipped {external_id} ({source_name}): {reason}")
                continue

            exercise = matches[0]
            width, height, duration_ms, frames = inspect_gif(source_gif)
            thumbnail_source = find_asset(
                metadata_file,
                f"{external_id}-360.gif",
                asset_index,
            )
            target_dir = PUBLIC_MEDIA_ROOT / external_id
            media_name = source_gif.name
            thumbnail_name = thumbnail_source.name if thumbnail_source else None

            media_url = f"/exercise-media/exercisedb/{external_id}/{media_name}"
            thumbnail_url = (
                f"/exercise-media/exercisedb/{external_id}/{thumbnail_name}"
                if thumbnail_name else media_url
            )
            poster_url = f"/exercise-media/exercisedb/{external_id}/poster.png"

            existing = db.scalars(
                select(ExerciseMediaModel).where(
                    ExerciseMediaModel.exercise_id == exercise.id,
                    ExerciseMediaModel.provider == PROVIDER,
                )
            ).all()
            row = existing[0] if existing else ExerciseMediaModel(
                exercise_id=exercise.id,
                media_type="gif",
                media_url=media_url,
            )

            if not args.dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_gif, target_dir / media_name)
                if thumbnail_source and thumbnail_source.resolve() != source_gif.resolve():
                    shutil.copy2(thumbnail_source, target_dir / thumbnail_source.name)
                write_poster(source_gif, target_dir / "poster.png")

                for media_row in exercise.media:
                    media_row.is_primary = False
                for duplicate in existing[1:]:
                    duplicate.status = HIDDEN_STATUS
                    duplicate.is_primary = False

                row.media_type = "gif"
                row.media_url = media_url
                row.thumbnail_url = thumbnail_url
                row.poster_url = poster_url
                row.provider = PROVIDER
                row.license = "ExerciseDB.io license required"
                row.attribution = "Exercise visual by ExerciseDB.io; local asset supplied by the project owner"
                row.width = width
                row.height = height
                row.duration = (duration_ms + 999) // 1000 if duration_ms else None
                row.duration_ms = duration_ms or None
                row.camera_angle = "Instructional view"
                row.format = "gif"
                row.version = 1
                row.status = "ready"
                row.is_primary = True
                db.add(row)

            registered += 1
            verb = "Would register" if args.dry_run else "Registered"
            print(f"[+] {verb} {exercise.name}: {media_url} ({width}x{height}, {frames} frames, {duration_ms}ms)")

        if args.dry_run:
            db.rollback()
        else:
            db.commit()

    mode = "Dry run" if args.dry_run else "Import"
    print(f"\n{mode} complete: registered={registered}, skipped={skipped}, invalid={invalid}, retired={retired}")
    if temporary_source is not None:
        temporary_source.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
