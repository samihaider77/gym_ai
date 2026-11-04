"""Build the training set for the GymAI drawing style (Everkinetic line art, CC BY-SA 4.0).

Run from the project root: backend/.venv/Scripts/python.exe tools/ai-drawings/build_dataset.py
Writes tools/ai-drawings/everkinetic-style.zip: every start/end drawing as a white-background PNG plus
metadata.jsonl with one caption per image, ready to upload to Kaggle as a dataset.
"""
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

REV = "446bb9a3d0c3beb6b84f7c9d77dfc8af707a2ab6"
RAW = f"https://raw.githubusercontent.com/everkinetic/data/{REV}"
OUT = Path(__file__).resolve().parent / "everkinetic-style.zip"
TRIGGER = "evkdraw"  # the LoRA learns this word as "the GymAI drawing style"


def fetch(url: str, attempts: int = 5) -> bytes:
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(2 + attempt * 3)
    raise RuntimeError(url)


def caption(record: dict, phase: str) -> str:
    equipment = [e for e in record.get("equipment") or [] if e]
    gear = f", with {' and '.join(equipment)}" if equipment and equipment != ["none"] else ""
    position = "start position" if phase == "relaxation" else "end position"
    return (f"{TRIGGER}, black ink line drawing of a muscular bald man in shorts doing {record['title'].strip().lower()}"
            f"{gear}, {position}, thick black outlines, white background")


def main() -> None:
    records = json.loads(fetch(f"{RAW}/exercises.json"))
    tree = json.loads(fetch(f"https://api.github.com/repos/everkinetic/data/git/trees/{REV}?recursive=1"))
    pngs = {entry["path"] for entry in tree["tree"] if entry["path"].startswith("dist/png/")}
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        lines, written = [], set()
        for record in records:
            stem = str(record.get("id_num", "")).zfill(4)
            for phase in ("relaxation", "tension"):
                path = f"dist/png/{stem}-{phase}.png"
                if path not in pngs:
                    continue
                image = Image.open(io.BytesIO(fetch(f"{RAW}/{path}"))).convert("RGBA")
                page = Image.new("RGB", image.size, "white")
                page.paste(image, mask=image.split()[3])
                buffer = io.BytesIO()
                page.save(buffer, "PNG")
                name = f"{stem}-{phase}.png"
                if name in written:  # a few Everkinetic records share an id_num; keep the first
                    continue
                written.add(name)
                archive.writestr(f"images/{name}", buffer.getvalue())
                lines.append(json.dumps({"file_name": name, "text": caption(record, phase), "exercise": record["title"].strip(),
                                         "phase": "start" if phase == "relaxation" else "end"}))
                count += 1
        archive.writestr("images/metadata.jsonl", "\n".join(lines) + "\n")
        archive.writestr("LICENSE.txt", "Drawings by Everkinetic (everkinetic.com), CC BY-SA 4.0 "
                                        "(https://creativecommons.org/licenses/by-sa/4.0/). Source: "
                                        f"github.com/everkinetic/data at {REV}.\n")
    print(f"{count} images written to {OUT}")


if __name__ == "__main__":
    main()
