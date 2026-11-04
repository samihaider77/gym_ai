"""Build gymai_drawings.ipynb (the Kaggle notebook) from pipeline.py and exercise-poses.json.

Run after editing either file: python tools/ai-drawings/make_notebook.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Versions the pipeline was checked with; Kaggle already has torch.
PACKAGES = "diffusers==0.42.1 transformers==5.22.1 peft==0.21.2 accelerate controlnet_aux==0.0.10 opencv-python-headless"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip().splitlines(keepends=True)}


def main() -> None:
    pipeline = (HERE / "pipeline.py").read_text(encoding="utf-8")
    poses = (HERE / "exercise-poses.json").read_text(encoding="utf-8")
    cells = [
        md("""
# GymAI drawings

Draws the exercises that have no picture yet, in the same black-ink style as the library (Everkinetic,
CC BY-SA 4.0). The pose of every exercise is already written in `exercise-poses.json` below, so no videos are
needed. (Optional: add clips as an input dataset and those exercises use the clip's pose instead.)

**Before running:** Settings → Accelerator → **GPU T4 x2** (not P100: current PyTorch no longer supports it),
and Settings → **Internet on**. Add the `everkinetic-style` dataset with **+ Add Input**. Then **Run All**.

The first run learns the style (~1 hour) and draws the first `LIMIT` exercises so you can check the quality.
Set `LIMIT = 0` to draw all of them (~3-4 hours). Download **gymai-drawings.zip** and **gymai-style-lora.zip**
from the Output panel; adding the LoRA zip as an input next time skips the training.
"""),
        # Kaggle ships an old torchao that peft refuses to load next to; nothing here needs it.
        code(f"!pip uninstall -y -q torchao\n!pip install -q {PACKAGES}"),
        code("%%writefile pipeline.py\n" + pipeline),
        code("%%writefile exercise-poses.json\n" + poses),
        code('''
import subprocess
from pathlib import Path

import torch


def run(*args):
    """Run one pipeline step and stop the notebook if it fails."""
    subprocess.run(["python", "pipeline.py", *map(str, args)], check=True)


print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE - turn on GPU T4 in Settings")
inputs = Path("/kaggle/input")
DATA = next((p.parent for p in inputs.rglob("metadata.jsonl")), None)
LORA = next((p.parent for p in inputs.rglob("pytorch_lora_weights.safetensors")), None)
MEDIA = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"}
clip_files = [p for p in inputs.rglob("*") if p.suffix.lower() in MEDIA
              and (DATA is None or DATA not in p.parents) and (LORA is None or LORA not in p.parents)]
CLIPS = Path("/kaggle/working/clips")
CLIPS.mkdir(exist_ok=True)
for p in clip_files:  # optional clips, gathered in one folder
    target = CLIPS / p.name
    if not target.exists():
        target.symlink_to(p)
print("style data:", DATA)
print("saved style (LoRA):", LORA or "none yet, it will be trained")
print("optional clips/photos:", len(clip_files))
'''),
        md("## 1. Learn the drawing style (skipped when a saved LoRA was added as input)"),
        code('''
if LORA is None:
    run("train", "--data", DATA, "--lora", "/kaggle/working/lora", "--steps", 2000)
    LORA = "/kaggle/working/lora"
    !cd /kaggle/working && zip -qr gymai-style-lora.zip lora
'''),
        md("## 2. Start and end pose of every exercise"),
        code('''
run("specposes", "--specs", "exercise-poses.json", "--poses", "/kaggle/working/poses")
if clip_files:  # clips you added win over the written poses
    run("poses", "--clips", "/kaggle/working/clips", "--poses", "/kaggle/working/clip-poses")
    import json, shutil
    written = json.load(open("/kaggle/working/poses/manifest.json"))
    from_clips = json.load(open("/kaggle/working/clip-poses/manifest.json"))
    for entry in from_clips:
        shutil.copytree(f"/kaggle/working/clip-poses/{entry['slug']}", f"/kaggle/working/poses/{entry['slug']}",
                        dirs_exist_ok=True)
    slugs = {e["slug"] for e in from_clips}
    merged = from_clips + [e for e in written if e["slug"] not in slugs]
    json.dump(merged, open("/kaggle/working/poses/manifest.json", "w"), indent=1)
'''),
        md("## 3. Draw each exercise (LIMIT = how many; 0 = all)"),
        code('''
LIMIT = 20
run("generate", "--lora", LORA, "--poses", "/kaggle/working/poses", "--out", "/kaggle/working/drawings",
    "--candidates", 3, "--limit", LIMIT)
'''),
        md("## 4. Review and download"),
        code('''
from IPython.display import Image as Show, display
display(Show("/kaggle/working/drawings/review.png"))
!cd /kaggle/working && zip -qr gymai-drawings.zip drawings && ls -la /kaggle/working/*.zip
'''),
    ]
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                             "language_info": {"name": "python"}},
                "nbformat": 4, "nbformat_minor": 5}
    out = HERE / "gymai_drawings.ipynb"
    out.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
