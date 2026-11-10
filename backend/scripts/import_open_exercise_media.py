"""Import openly licensed exercise media (wger + Everkinetic) into GymAI.

Run from backend/:
    python scripts/import_open_exercise_media.py --source all
    python scripts/import_open_exercise_media.py --source wger --skip-videos --dry-run

Sources (both Creative Commons, attribution stored on every media row):
- wger.de public API: exercise photos/illustrations and real videos (CC BY-SA 3.0/4.0,
  CC BY 4.0, CC0 per item, with the author recorded per item).
- Everkinetic (github.com/everkinetic/data, pinned commit): start/end illustrations,
  CC BY-SA 4.0.

Two-frame sources become a looping cross-fade MP4 (start -> end -> start) plus a webp
poster; single images are stored as webp; wger videos are transcoded to small H.264 MP4
so every browser can play them. Exercises that don't exist yet are created from the
source metadata unless --no-create is passed. Re-running is idempotent: finished files
are skipped and rows are updated in place.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen

import imageio_ffmpeg
from PIL import Image
from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.db.session import SessionLocal  # noqa: E402
from app.core.utils.slug import generate_slug  # noqa: E402
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: E402
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel  # noqa: E402
from app.modules.exercises.infrastructure.models import ExerciseModel, exercise_muscle_association  # noqa: E402
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: E402
sys.path.append(str(Path(__file__).resolve().parent))
from catalog_names import canonical_equipment, display_name, is_house_style  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MEDIA_ROOT = ROOT / "frontend" / "public" / "exercise-media"
CACHE_ROOT = Path(__file__).resolve().parents[1] / ".media-cache"
HIDDEN_STATUSES = {"failed", "deprecated", "rejected"}
USER_AGENT = "GymAI-media-importer/1.0 (open-licensed exercise media)"

WGER_API = "https://wger.de/api/v2"
WGER_ENGLISH = 2
EVERKINETIC_REV = "446bb9a3d0c3beb6b84f7c9d77dfc8af707a2ab6"
EVERKINETIC_RAW = f"https://raw.githubusercontent.com/everkinetic/data/{EVERKINETIC_REV}"

# Lower rank wins when choosing the primary media for an exercise.
PROVIDER_RANK = {"Vital Animations": 0, "wger:video": 1, "Everkinetic": 2, "WorkoutGuide": 2, "wger:loop": 3, "wger:image": 4}

SYNONYMS = {
    "dumbbells": "dumbbell", "db": "dumbbell", "barbells": "barbell", "sz": "ez", "szbar": "ez",
    "curls": "curl", "rows": "row", "rowing": "row", "raises": "raise", "presses": "press",
    "squats": "squat", "lunges": "lunge", "deadlifts": "deadlift", "crunches": "crunch",
    "extensions": "extension", "flyes": "fly", "flys": "fly", "flies": "fly", "dips": "dip",
    "pushups": "pushup", "pullups": "pullup", "chinups": "chinup", "shrugs": "shrug",
    "kickbacks": "kickback", "pulldowns": "pulldown", "thrusts": "thrust", "bridges": "bridge",
    "planks": "plank", "twists": "twist", "swings": "swing", "jacks": "jack", "steps": "step",
    "benchpress": "bench press", "facepull": "face pull", "facepulls": "face pull",
    "skullcrushers": "skullcrusher", "triceps": "tricep", "biceps": "bicep", "calves": "calf",
}
JOINED = {("push", "up"): "pushup", ("pull", "up"): "pullup", ("chin", "up"): "chinup",
          ("pull", "down"): "pulldown", ("sit", "up"): "situp", ("step", "up"): "stepup",
          ("skull", "crusher"): "skullcrusher"}
# Implied equipment: "Bench Press" means the barbell version, "Dips" the bodyweight one.
IMPLIED_TOKENS = ["barbell", "bodyweight", "dumbbell"]
# Source name key -> existing GymAI exercise name, for the common lifts the token match misses.
ALIASES = {
    "deadlift": "Conventional Deadlift", "dip": "Chest Dip", "squat": "Barbell Back Squat",
    "back squat": "Barbell Back Squat", "crunch": "Crunches", "pushup": "Push-Up",
    "pullup": "Pull-Up", "chinup": "Chin-Up", "lat pulldown": "Lat Pulldown",
    "military press": "Barbell Overhead Press", "overhead press": "Barbell Overhead Press",
    "shoulder press": "Dumbbell Shoulder Press", "lateral raise": "Dumbbell Lateral Raise",
    "front raise": "Dumbbell Front Raise", "barbell shrug": "Barbell Shrug", "shrug": "Barbell Shrug",
    "leg curl lying": "Lying Leg Curl", "leg curl seated": "Seated Leg Curl", "leg press": "Leg Press",
    "lunge walking": "Walking Lunge", "plank": "Plank", "side plank": "Side Plank",
    "hip thrust": "Barbell Hip Thrust", "romanian deadlift": "Romanian Deadlift",
    "calf raise standing": "Standing Calf Raise", "calf raise seated": "Seated Calf Raise",
}
STOPWORDS = {"with", "the", "on", "a", "an", "using", "of", "and", "to", "in", "s", "exercise"}

WGER_MUSCLES = {
    "biceps brachii": "Biceps", "brachialis": "Biceps", "triceps brachii": "Triceps",
    "pectoralis major": "Chest", "serratus anterior": "Chest", "latissimus dorsi": "Back",
    "trapezius": "Shoulders", "anterior deltoid": "Shoulders", "shoulders": "Shoulders",
    "rectus abdominis": "Core", "obliquus externus abdominis": "Core", "abs": "Core",
    "gluteus maximus": "Glutes", "glutes": "Glutes", "quadriceps femoris": "Quadriceps",
    "quads": "Quadriceps", "biceps femoris": "Hamstrings", "hamstrings": "Hamstrings",
    "gastrocnemius": "Calves", "soleus": "Calves", "calves": "Calves", "lats": "Back",
    "chest": "Chest", "triceps": "Triceps", "biceps": "Biceps", "obliques": "Core",
}
WGER_CATEGORY_MUSCLE = {"Abs": "Core", "Arms": "Biceps", "Back": "Back", "Calves": "Calves",
                        "Cardio": "Full Body", "Chest": "Chest", "Legs": "Quadriceps",
                        "Shoulders": "Shoulders"}
EVERKINETIC_MUSCLES = {
    "chest": "Chest", "back": "Back", "lats": "Back", "middle back": "Back", "upper back": "Back",
    "lower back": "Lower Back", "shoulders": "Shoulders", "traps": "Shoulders", "neck": "Shoulders",
    "biceps": "Biceps", "triceps": "Triceps", "forearms": "Forearms", "abs": "Core",
    "abdominals": "Core", "obliques": "Core", "core": "Core", "glutes": "Glutes",
    "quadriceps": "Quadriceps", "quads": "Quadriceps", "hamstrings": "Hamstrings",
    "calves": "Calves", "adductors": "Quadriceps", "abductors": "Glutes", "hip flexors": "Hip Flexors",
}

@dataclass
class SourceItem:
    provider: str            # provider label stored on the row ("wger" / "Everkinetic")
    source_id: str
    name: str
    kind: str                # "video" | "loop" | "image"
    urls: list[str]
    license: str
    attribution: str
    instructions: str = ""
    primary_muscle: str = "Full Body"
    secondary_muscles: list[str] = field(default_factory=list)
    equipment: str = "None"
    exercise_type: str = "strength"
    mechanic: str | None = None

    @property
    def rank_key(self) -> str:
        return self.provider if self.provider == "Everkinetic" else f"wger:{self.kind}"

    @property
    def folder(self) -> Path:
        return PUBLIC_MEDIA_ROOT / self.provider.lower() / f"{self.source_id}-{self.kind}"

    @property
    def url_base(self) -> str:
        return f"/exercise-media/{self.provider.lower()}/{self.source_id}-{self.kind}"


def name_key(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    words = re.sub(r"\(.*?\)", " ", ascii_value.lower())
    words = re.sub(r"[^a-z0-9]+", " ", words.replace("'", "")).split()
    merged: list[str] = []
    for word in words:
        if merged and (merged[-1], word) in JOINED:
            merged[-1] = JOINED[(merged[-1], word)]
            continue
        merged.append(word)
    tokens: set[str] = set()
    for word in merged:
        for token in SYNONYMS.get(word, word).split():
            if token not in STOPWORDS:
                tokens.add(token)
    return " ".join(sorted(tokens))


def fetch(url: str, attempts: int = 4, timeout: int = 60) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:
                return response.read()
        except OSError:
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def fetch_json(url: str):
    return json.loads(fetch(url).decode("utf-8"))


def cached_download(url: str) -> Path:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    target = CACHE_ROOT / re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("://", 1)[-1])[-180:]
    if not target.exists():
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.write_bytes(fetch(url, timeout=300))
        temporary.replace(target)
    return target


def strip_html(value: str | None) -> str:
    text = re.sub(r"<\s*(br|/p|/li)\s*/?>", "\n", value or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


# --------------------------------------------------------------------------- sources

def load_wger(include_videos: bool) -> list[SourceItem]:
    licenses = {item["id"]: item for item in fetch_json(f"{WGER_API}/license/?limit=50")["results"]}
    payload = fetch_json(f"{WGER_API}/exerciseinfo/?limit=2000")
    items: list[SourceItem] = []
    for exercise in payload["results"]:
        english = next((t for t in exercise["translations"] if t["language"] == WGER_ENGLISH), None)
        if not english or not english.get("name", "").strip():
            continue
        name = re.sub(r"\s+", " ", english["name"]).strip()
        muscles = [m.get("name_en") or m["name"] for m in exercise["muscles"]]
        secondary = [m.get("name_en") or m["name"] for m in exercise["muscles_secondary"]]
        mapped = [WGER_MUSCLES.get(m.lower()) for m in muscles]
        primary = next((m for m in mapped if m), WGER_CATEGORY_MUSCLE.get(exercise["category"]["name"], "Full Body"))
        common = dict(
            name=name,
            instructions=strip_html(english.get("description")),
            primary_muscle=primary,
            secondary_muscles=[m for m in dict.fromkeys(WGER_MUSCLES.get(s.lower()) for s in secondary) if m and m != primary],
            equipment=(exercise["equipment"][0]["name"] if exercise["equipment"] else "none (bodyweight exercise)"),
            exercise_type="cardio" if exercise["category"]["name"] == "Cardio" else "strength",
        )

        def credit(media: dict, what: str) -> tuple[str, str]:
            lic = licenses.get(media["license"], {})
            author = media.get("license_author") or exercise.get("license_author") or "wger contributors"
            short = (lic.get("short_name") or "CC-BY-SA").replace("CC-", "CC ")
            return short, f"“{name}” {what} by {author} via wger.de, {short} ({lic.get('url', '')})"

        images = sorted(exercise["images"], key=lambda img: (not img["is_main"], img["id"]))
        # A loop only pairs pictures by the same author: wger often has an Everkinetic drawing next to
        # someone else's colour render, and flipping between the two looks like two different people.
        images = [img for img in images if images and img.get("license_author") == images[0].get("license_author")]
        if images:
            lic, attribution = credit(images[0], "illustration")
            kind = "loop" if len(images) >= 2 else "image"
            items.append(SourceItem(provider="wger", source_id=str(exercise["id"]), kind=kind,
                                    urls=[img["image"] for img in images[:2]], license=lic,
                                    attribution=attribution, **common))
        videos = sorted(exercise["videos"], key=lambda v: (not v["is_main"], v["id"]))
        if include_videos and videos:
            lic, attribution = credit(videos[0], "video")
            items.append(SourceItem(provider="wger", source_id=str(exercise["id"]), kind="video",
                                    urls=[videos[0]["video"]], license=lic, attribution=attribution, **common))
    return items


def load_everkinetic() -> list[SourceItem]:
    exercises = fetch_json(f"{EVERKINETIC_RAW}/exercises.json")
    tree = fetch_json(f"https://api.github.com/repos/everkinetic/data/git/trees/{EVERKINETIC_REV}?recursive=1")
    pngs = {entry["path"] for entry in tree["tree"] if entry["path"].startswith("dist/png/")}
    items: list[SourceItem] = []
    for record in exercises:
        id_num = str(record.get("id_num", "")).zfill(4)
        stem = f"dist/png/{id_num}"
        frames = [f"{stem}-relaxation.png", f"{stem}-tension.png"]
        if not all(frame in pngs for frame in frames):
            continue
        primary = EVERKINETIC_MUSCLES.get(str(record.get("primary", "")).lower(), "Full Body")
        secondary = [EVERKINETIC_MUSCLES.get(str(m).lower()) for m in record.get("secondary") or []]
        equipment = [str(e).lower() for e in record.get("equipment") or []]
        main_equipment = next((e for e in equipment if e != "bench"), equipment[0] if equipment else "bodyweight")
        items.append(SourceItem(
            provider="Everkinetic", source_id=id_num, name=record["title"].strip(), kind="loop",
            urls=[f"{EVERKINETIC_RAW}/{frame}" for frame in frames], license="CC BY-SA 4.0",
            attribution=f"“{record['title'].strip()}” illustration by Everkinetic (everkinetic.com), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)",
            instructions="\n".join(record.get("steps") or []),
            primary_muscle=primary,
            secondary_muscles=[m for m in dict.fromkeys(secondary) if m and m != primary],
            equipment=main_equipment,
            mechanic="compound" if record.get("type") == "compound" else "isolation",
        ))
    return items


# --------------------------------------------------------------------------- rendering

def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-1200:])


MIN_SOURCE_EDGE = 160  # smaller uploads on wger are channel logos/icons, not demonstrations


def load_frame(path: Path, size: int) -> Image.Image:
    with Image.open(path) as source:
        if max(source.size) < MIN_SOURCE_EDGE:
            raise ValueError(f"source image too small to be a demo ({source.size[0]}x{source.size[1]})")
        image = source.convert("RGBA")
    image.thumbnail((size - 24, size - 24), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2), image)
    return canvas


def render(item: SourceItem, size: int) -> dict:
    """Download and render one item; returns the row fields. Safe to call from threads."""
    if item.kind in {"image", "loop"}:
        # Validate sources even when output already exists, so earlier renders get re-checked.
        for url in item.urls:
            with Image.open(cached_download(url)) as source:
                if max(source.size) < MIN_SOURCE_EDGE:
                    raise ValueError(f"source image too small to be a demo ({source.size[0]}x{source.size[1]})")
    folder = item.folder
    folder.mkdir(parents=True, exist_ok=True)
    poster = folder / "poster.webp"
    if item.kind == "image":
        target = folder / "image.webp"
        if not target.exists():
            load_frame(cached_download(item.urls[0]), size).save(target, "WEBP", quality=82)
        return dict(media_type="image", format="webp", media_url=f"{item.url_base}/image.webp",
                    poster_url=f"{item.url_base}/image.webp", duration=None)

    target = folder / "animation.mp4"
    if item.kind == "loop" and not target.exists():
        start, end = (load_frame(cached_download(url), size) for url in item.urls)
        fps, hold, fade = 15, 10, 8
        sequence = [start] * hold + [Image.blend(start, end, i / fade) for i in range(1, fade)] \
            + [end] * hold + [Image.blend(end, start, i / fade) for i in range(1, fade)]
        frames_dir = folder / ".frames"
        frames_dir.mkdir(exist_ok=True)
        for index, frame in enumerate(sequence):
            frame.save(frames_dir / f"{index:03d}.png")
        try:
            run_ffmpeg(["-framerate", str(fps), "-i", str(frames_dir / "%03d.png"), "-c:v", "libx264",
                        "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        str(target.with_suffix(".tmp.mp4"))])
            target.with_suffix(".tmp.mp4").replace(target)
        finally:
            for file in frames_dir.glob("*.png"):
                file.unlink()
            frames_dir.rmdir()
        start.save(poster, "WEBP", quality=80)
    elif item.kind == "video" and not target.exists():
        source = cached_download(item.urls[0])
        # Real footage keeps its own aspect ratio (no white padding), capped at `size` pixels tall.
        run_ffmpeg(["-i", str(source), "-t", "15", "-an", "-vf", f"scale=-2:'min({size},ih)'",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "27", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(target.with_suffix(".tmp.mp4"))])
        target.with_suffix(".tmp.mp4").replace(target)
        run_ffmpeg(["-ss", "1", "-i", str(target), "-frames:v", "1", "-update", "1", "-c:v", "libwebp",
                    "-quality", "78", str(poster)])
    _, duration = imageio_ffmpeg.count_frames_and_secs(str(target))
    with Image.open(poster) as still:
        width, height = still.size
    return dict(media_type="video", format="mp4", media_url=f"{item.url_base}/animation.mp4",
                poster_url=f"{item.url_base}/poster.webp", duration=duration, width=width, height=height)


# --------------------------------------------------------------------------- database

class Catalog:
    def __init__(self, db, create_missing: bool):
        self.db = db
        self.create_missing = create_missing
        self.by_key: dict[str, ExerciseModel] = {}
        for exercise in db.scalars(select(ExerciseModel).where(ExerciseModel.is_active.is_(True))):
            self.by_key.setdefault(name_key(exercise.name), exercise)
        self.names = {name.lower() for name in db.scalars(select(ExerciseModel.name))}
        self.slugs = set(db.scalars(select(ExerciseModel.slug)))
        self.muscles = {m.name: m for m in db.scalars(select(MuscleGroupModel))}
        self.equipment = {e.name.lower(): e for e in db.scalars(select(EquipmentModel))}
        self.created = 0

    def equipment_for(self, raw: str) -> EquipmentModel:
        name = canonical_equipment(raw)
        found = self.equipment.get(name.lower())
        if found is None:
            found = EquipmentModel(name=name, slug=generate_slug(name), category=generate_slug(name).replace("-", "_"),
                                   description=f"{name} equipment")
            self.db.add(found)
            self.db.flush()
            self.equipment[name.lower()] = found
        return found

    def muscle_for(self, name: str) -> MuscleGroupModel:
        return self.muscles.get(name) or self.muscles["Full Body"]

    def resolve(self, item: SourceItem) -> ExerciseModel | None:
        key = name_key(item.name)
        alias = ALIASES.get(key)
        for candidate in (key, alias and name_key(alias), *(f"{key} {extra}" for extra in IMPLIED_TOKENS)):
            candidate = " ".join(sorted(set((candidate or "").split())))
            if candidate in self.by_key:
                return self.by_key[candidate]
        slug = generate_slug(item.name)
        if not self.create_missing or not key or item.name.lower() in self.names or slug in self.slugs:
            return None
        mechanic = item.mechanic or ("isolation" if not item.secondary_muscles else "compound")
        exercise = ExerciseModel(
            name=display_name(item.name)[:150], slug=slug[:150],
            description=f"A {mechanic} {item.exercise_type} movement for the {item.primary_muscle.lower()}.",
            instructions=item.instructions or "Perform the movement with controlled form and return to the starting position.",
            difficulty_level="beginner", exercise_type=item.exercise_type, force_type=None,
            mechanic_type=mechanic, equipment_id=self.equipment_for(item.equipment).id,
            is_compound=mechanic == "compound",
        )
        self.db.add(exercise)
        self.db.flush()
        primary = self.muscle_for(item.primary_muscle)
        rows = [{"exercise_id": exercise.id, "muscle_group_id": primary.id, "role": "primary"}]
        rows += [{"exercise_id": exercise.id, "muscle_group_id": self.muscle_for(m).id, "role": "secondary"}
                 for m in item.secondary_muscles if self.muscle_for(m).id != primary.id]
        self.db.execute(exercise_muscle_association.insert(), list({r["muscle_group_id"]: r for r in rows}.values()))
        self.by_key[key] = exercise
        self.names.add(item.name.lower())
        self.slugs.add(slug)
        self.created += 1
        return exercise


def upsert_media(db, exercise: ExerciseModel, item: SourceItem, fields: dict, size: int, all_styles: bool) -> None:
    provider = item.provider
    row = db.scalar(select(ExerciseMediaModel).where(
        ExerciseMediaModel.exercise_id == exercise.id,
        ExerciseMediaModel.provider == provider,
        ExerciseMediaModel.media_url == fields["media_url"],
    ))
    if row is None:
        row = ExerciseMediaModel(exercise_id=exercise.id, media_type=fields["media_type"], media_url=fields["media_url"])
        db.add(row)
    duration = fields["duration"]
    row.media_type = fields["media_type"]
    row.thumbnail_url = fields["poster_url"]
    row.poster_url = fields["poster_url"]
    row.provider = provider
    row.license = item.license
    row.attribution = item.attribution[:500]
    row.width = fields.get("width", size)
    row.height = fields.get("height", size)
    row.duration = max(1, round(duration)) if duration else None
    row.duration_ms = max(1, round(duration * 1000)) if duration else None
    row.camera_angle = "Real video" if item.kind == "video" else "Start / end position"
    row.format = fields["format"]
    row.version = 1
    # Only one drawing style is shown so the library looks consistent; --all-styles shows everything.
    row.status = "ready" if all_styles or is_house_style(provider, row.attribution) else "deprecated"
    row.is_primary = False


def rank(media: ExerciseMediaModel) -> int:
    if media.provider == "wger":
        key = "wger:video" if "-video/" in media.media_url else ("wger:image" if media.media_type == "image" else "wger:loop")
    else:
        key = media.provider or ""
    return PROVIDER_RANK.get(key, 9)


def choose_primaries(db, exercise_ids: set) -> None:
    for exercise_id in exercise_ids:
        rows = [m for m in db.scalars(select(ExerciseMediaModel).where(ExerciseMediaModel.exercise_id == exercise_id))
                if m.status.lower() not in HIDDEN_STATUSES]
        rows.sort(key=rank)
        for index, media in enumerate(rows):
            media.is_primary = index == 0


# --------------------------------------------------------------------------- main

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import open-licensed exercise media (wger, Everkinetic)")
    parser.add_argument("--source", choices=["wger", "everkinetic", "all"], default="all")
    parser.add_argument("--skip-videos", action="store_true", help="Skip wger videos (~35 MB download each)")
    parser.add_argument("--no-create", action="store_true", help="Only attach media to existing exercises")
    parser.add_argument("--size", type=int, default=480, help="Square output resolution")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true", help="Match only; no downloads or DB writes")
    parser.add_argument("--all-styles", action="store_true",
                        help="Show media in every style, not only the Everkinetic line drawings")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    items: list[SourceItem] = []
    if args.source in {"wger", "all"}:
        items += load_wger(include_videos=not args.skip_videos)
    if args.source in {"everkinetic", "all"}:
        items += load_everkinetic()
    print(f"Loaded {len(items)} media items from source(s): {args.source}")

    with SessionLocal() as db:
        catalog = Catalog(db, create_missing=not args.no_create)
        planned: list[tuple[ExerciseModel, SourceItem]] = []
        skipped = 0
        for item in items:
            exercise = catalog.resolve(item)
            if exercise is None:
                skipped += 1
                continue
            planned.append((exercise, item))
        print(f"Matched/created {len(planned)} items ({catalog.created} new exercises), skipped {skipped}")
        if args.dry_run:
            for exercise, item in planned[:60]:
                print(f"  {item.provider:<11} {item.kind:<5} {item.name!r} -> {exercise.name!r}")
            db.rollback()
            return 0
        db.commit()

        done, failed, rejected, touched = 0, 0, 0, set()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(render, item, args.size): (exercise, item) for exercise, item in planned}
            for future in as_completed(futures):
                exercise, item = futures[future]
                try:
                    fields = future.result()
                except Exception as exc:  # keep going; a re-run retries failures
                    print(f"[-] {item.provider} {item.source_id} {item.kind} ({item.name}): {str(exc)[-200:]}")
                    if not isinstance(exc, ValueError):
                        failed += 1
                    else:
                        rejected += 1
                        # Unusable source: hide any row an earlier run created for it.
                        for stale in db.scalars(select(ExerciseMediaModel).where(
                            ExerciseMediaModel.provider == item.provider,
                            ExerciseMediaModel.media_url.like(f"{item.url_base}/%"),
                        )):
                            stale.status = "rejected"
                            stale.is_primary = False
                            touched.add(stale.exercise_id)
                    continue
                upsert_media(db, exercise, item, fields, args.size, args.all_styles)
                touched.add(exercise.id)
                done += 1
                if done % 25 == 0:
                    db.commit()
                    print(f"[+] {done}/{len(planned)} rendered")
        choose_primaries(db, touched)
        db.commit()
    print(f"Import complete: media={done}, failed={failed}, rejected={rejected}, exercises_with_new_media={len(touched)}, "
          f"new_exercises={catalog.created}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
