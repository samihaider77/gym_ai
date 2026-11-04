"""GymAI drawing pipeline: learn the Everkinetic line-art style, then draw new exercises in it.

Steps (each is a sub-command):
  train     Fine-tune a small LoRA on the Everkinetic drawings (everkinetic-style.zip / metadata.jsonl).
  poses     Read exercise clips or photos and save a start and an end pose skeleton for each.
  specposes Make the start/end skeletons from written pose descriptions (exercise-poses.json), no video.
  generate  Draw each exercise's start and end frame from its poses, in the learned style.
  stylize   Redraw clean 3D line renders (tools/3d) in the learned style; the outline keeps its exact shape.

Clip naming (in the clips folder): "<Exercise Name>.mp4" (any common video type), or two photos
"<Exercise Name>__start.jpg" and "<Exercise Name>__end.jpg". Use the exercise name exactly as the app shows it
in English, so the importer can match it.

Runs on a GPU (Kaggle T4). --tiny swaps in very small test models so the code can be checked on a CPU.
"""
import argparse
import json
import math
import random
import re
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps

BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET = "lllyasviel/control_v11p_sd15_openpose"
TINY_BASE = "hf-internal-testing/tiny-stable-diffusion-pipe"
TRIGGER = "evkdraw"
# Kept under CLIP's 77-token limit so nothing is cut off. The first run drew walls, floors and stray weights,
# so those lead the list.
NEGATIVE = ("background, wall, bricks, floor, tiles, room, gym, frame, border, extra barbell, extra dumbbell, "
            "color, shading, gray, photo, text, blurry, extra limbs, deformed")
VIDEO_TYPES = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp"}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def square(image: Image.Image, size: int, fill) -> Image.Image:
    """Pad to a square without distorting, then resize."""
    image = ImageOps.contain(image, (size, size), Image.LANCZOS)
    canvas = Image.new(image.mode, (size, size), fill)
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def device_and_dtype(tiny: bool):
    if torch.cuda.is_available() and not tiny:
        return "cuda", torch.float16
    return "cpu", torch.float32


# --------------------------------------------------------------------------- train

def load_captions(data: Path) -> list[tuple[Path, str]]:
    meta = next(data.rglob("metadata.jsonl"))
    rows = [json.loads(line) for line in meta.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [(meta.parent / row["file_name"], row["text"]) for row in rows]


def train(args) -> None:
    from diffusers import AutoencoderKL, DDPMScheduler, StableDiffusionPipeline, UNet2DConditionModel
    from diffusers.utils import convert_state_dict_to_diffusers
    from peft import LoraConfig
    from peft.utils import get_peft_model_state_dict
    from transformers import CLIPTextModel, CLIPTokenizer

    device, dtype = device_and_dtype(args.tiny)
    base = TINY_BASE if args.tiny else args.base
    size = 64 if args.tiny else args.resolution
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    tokenizer = CLIPTokenizer.from_pretrained(base, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(base, subfolder="text_encoder").to(device, dtype)
    vae = AutoencoderKL.from_pretrained(base, subfolder="vae").to(device, dtype)
    unet = UNet2DConditionModel.from_pretrained(base, subfolder="unet").to(device, dtype)
    scheduler = DDPMScheduler.from_pretrained(base, subfolder="scheduler")
    for model in (text_encoder, vae, unet):
        model.requires_grad_(False)
    unet.add_adapter(LoraConfig(r=args.rank, lora_alpha=args.rank, init_lora_weights="gaussian",
                                target_modules=["to_k", "to_q", "to_v", "to_out.0"]))
    params = [p for p in unet.parameters() if p.requires_grad]
    for p in params:  # trainable LoRA weights stay in fp32 even when the base model is fp16
        p.data = p.data.float()
    if device == "cuda":
        unet.enable_gradient_checkpointing()
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=1e-2)
    scaler = torch.amp.GradScaler("cuda", enabled=device == "cuda")

    samples = load_captions(Path(args.data))
    print(f"training on {len(samples)} drawings for {args.steps} steps ({device})")

    def batch():
        picks = random.sample(samples, min(args.batch, len(samples)))
        pixels = []
        for path, _ in picks:
            image = square(Image.open(path).convert("RGB"), size, "white")
            if random.random() < 0.5:
                image = ImageOps.mirror(image)
            array = np.asarray(image, dtype=np.float32) / 127.5 - 1.0
            pixels.append(torch.from_numpy(array).permute(2, 0, 1))
        ids = tokenizer([caption for _, caption in picks], padding="max_length", truncation=True,
                        max_length=tokenizer.model_max_length, return_tensors="pt").input_ids
        return torch.stack(pixels).to(device, dtype), ids.to(device)

    unet.train()
    for step in range(1, args.steps + 1):
        pixels, ids = batch()
        with torch.no_grad():
            latents = vae.encode(pixels).latent_dist.sample() * vae.config.scaling_factor
            hidden = text_encoder(ids)[0]
        noise = torch.randn_like(latents)
        timesteps = torch.randint(0, scheduler.config.num_train_timesteps, (latents.shape[0],), device=device).long()
        noisy = scheduler.add_noise(latents, noise, timesteps)
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=device == "cuda"):
            pred = unet(noisy, timesteps, hidden).sample
        loss = torch.nn.functional.mse_loss(pred.float(), noise.float())
        optimizer.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        scaler.step(optimizer)
        scaler.update()
        # cosine decay to 10% of the starting rate
        for group in optimizer.param_groups:
            group["lr"] = args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * step / args.steps)))
        if step % max(1, args.steps // 20) == 0 or step == 1:
            print(f"step {step}/{args.steps} loss {loss.item():.4f}")

    out = Path(args.lora)
    out.mkdir(parents=True, exist_ok=True)
    layers = convert_state_dict_to_diffusers(get_peft_model_state_dict(unet))
    StableDiffusionPipeline.save_lora_weights(save_directory=str(out), unet_lora_layers=layers, safe_serialization=True)
    print("saved LoRA to", out)


# --------------------------------------------------------------------------- poses

class PoseReader:
    def __init__(self, tiny: bool):
        self.tiny = tiny
        if not tiny:
            import sys

            # controlnet_aux imports its mediapipe face tool on load, which breaks on new mediapipe releases.
            # OpenPose does not need mediapipe, so hide it while the package loads.
            hidden = sys.modules.get("mediapipe")
            sys.modules["mediapipe"] = None
            try:
                from controlnet_aux import OpenposeDetector
            finally:
                if hidden is None:
                    sys.modules.pop("mediapipe", None)
                else:
                    sys.modules["mediapipe"] = hidden
            self.detector = OpenposeDetector.from_pretrained("lllyasviel/Annotators")

    def __call__(self, image: Image.Image, size: int) -> Image.Image:
        # Pad the frame to a square first so the skeleton keeps the body's real proportions.
        frame = square(image.convert("RGB"), size, (127, 127, 127))
        if self.tiny:  # test stand-in: edges instead of a skeleton
            import cv2
            edges = cv2.Canny(np.asarray(frame.convert("L")), 80, 160)
            return Image.fromarray(edges).convert("RGB")
        pose = self.detector(frame, detect_resolution=size, image_resolution=size,
                             include_body=True, include_hand=False, include_face=False)
        return pose.resize((size, size))


def video_frames(path: Path, count: int) -> list[Image.Image]:
    import cv2
    capture = cv2.VideoCapture(str(path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frames = []
    for index in np.linspace(0, total - 1, num=min(count, total)).astype(int):
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = capture.read()
        if ok:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    capture.release()
    return frames


def pick_start_end(poses: list[Image.Image]) -> tuple[int, int]:
    """The two sampled frames whose skeletons differ most: the start and end of the movement."""
    small = [np.asarray(p.convert("L").resize((64, 64)), dtype=np.float32) for p in poses]
    usable = [i for i, s in enumerate(small) if (s > 20).mean() > 0.002] or list(range(len(small)))
    best, pair = -1.0, (usable[0], usable[-1])
    for a in usable:
        for b in usable:
            if a < b:
                score = float(np.abs(small[a] - small[b]).mean())
                if score > best:
                    best, pair = score, (a, b)
    return pair


def person_box(skeletons: list[Image.Image], margin: float = 0.3):
    """One square crop box around the skeletons of both frames, with room for head, feet and equipment."""
    union = np.zeros(np.asarray(skeletons[0].convert("L")).shape, bool)
    for skeleton in skeletons:
        union |= np.asarray(skeleton.convert("L")) > 20
    ys, xs = np.nonzero(union)
    if len(xs) < 20:
        return None
    height, width = union.shape
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) * (1 + 2 * margin)
    side = int(min(max(side, min(width, height) * 0.25), width, height))
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    left = int(min(max(cx - side / 2, 0), width - side))
    top = int(min(max(cy - side / 2, 0), height - side))
    return left, top, left + side, top + side


def poses(args) -> None:
    clips, out = Path(args.clips), Path(args.poses)
    size = 64 if args.tiny else args.resolution
    reader = PoseReader(args.tiny)
    jobs: dict[str, dict] = {}
    for path in sorted(clips.rglob("*")):
        suffix = path.suffix.lower()
        if suffix in VIDEO_TYPES:
            jobs.setdefault(path.stem, {})["video"] = path
        elif suffix in PHOTO_TYPES and "__" in path.stem:
            name, phase = path.stem.rsplit("__", 1)
            if phase.lower() in {"start", "end"}:
                jobs.setdefault(name, {})[phase.lower()] = path
    manifest = []
    for name, job in jobs.items():
        folder = out / slugify(name)
        folder.mkdir(parents=True, exist_ok=True)
        if "start" in job and "end" in job:
            frames = [Image.open(job["start"]), Image.open(job["end"])]
            skeletons = [reader(f, size) for f in frames]
            first, last = 0, 1
        elif "video" in job:
            frames = video_frames(job["video"], args.samples)
            if len(frames) < 2:
                print("skipped (could not read video):", name)
                continue
            skeletons = [reader(f, size) for f in frames]
            first, last = pick_start_end(skeletons)
        else:
            print("skipped (need a video or both __start and __end photos):", name)
            continue
        chosen = [square(frames[i].convert("RGB"), size, (127, 127, 127)) for i in (first, last)]
        box = person_box([skeletons[first], skeletons[last]])
        if box:  # zoom both frames on the same area so the person fills the drawing
            chosen = [frame.crop(box).resize((size, size), Image.LANCZOS) for frame in chosen]
            skeleton_pair = [reader(frame, size) for frame in chosen]
        else:
            skeleton_pair = [skeletons[first], skeletons[last]]
        for phase, frame, skeleton in zip(("start", "end"), chosen, skeleton_pair):
            skeleton.save(folder / f"{phase}-pose.png")
            frame.save(folder / f"{phase}-frame.jpg")
        manifest.append({"name": name, "slug": slugify(name)})
        print("poses ready:", name)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{len(manifest)} exercises have start/end poses in {out}")


# --------------------------------------------------------------------------- poses from a description

# Body proportions as a fraction of standing height, and OpenPose's 18-point drawing order and colours.
LENGTHS = {"torso": 0.30, "head": 0.11, "upper_arm": 0.165, "forearm": 0.15, "thigh": 0.245, "shin": 0.245}
LIMBS = [(2, 3), (2, 6), (3, 4), (4, 5), (6, 7), (7, 8), (2, 9), (9, 10), (10, 11), (2, 12), (12, 13), (13, 14),
         (2, 1), (1, 15), (15, 17), (1, 16), (16, 18)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
          (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
          (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]
FACING = {"up": 90, "down": -90, "left": 180, "right": 0}


def _towards(point, angle: float, length: float):
    return (point[0] + length * math.cos(math.radians(angle)), point[1] + length * math.sin(math.radians(angle)))


def spec_keypoints(frame: dict, view: str) -> list:
    """OpenPose keypoints (x right, y up) from segment angles.

    Angles are degrees in the picture: 0 = towards the side the person faces (right), 90 = up, -90 = down,
    180 = behind. "arms" and "legs" are [[upper, lower], [upper, lower]]: near side first (in front view: the
    limb on the picture's left first). "face" (up/down/left/right) overrides which way the face points.
    """
    side = view != "front"
    hip = (0.0, 0.0)
    neck = _towards(hip, frame["torso"], LENGTHS["torso"])
    head_angle = frame.get("head", frame["torso"])
    across = frame["torso"] - 90  # in front view: from the body's centre towards the picture's right
    if side:
        shoulders = [neck, neck]
        hips = [hip, hip]
    else:
        shoulders = [_towards(neck, across + 180, 0.11), _towards(neck, across, 0.11)]
        hips = [_towards(hip, across + 180, 0.07), _towards(hip, across, 0.07)]
    points: list = [None] * 18
    points[1] = neck
    face = FACING.get(frame.get("face", ""), head_angle - 90)
    top = _towards(neck, head_angle, LENGTHS["head"])
    if side:
        points[0] = _towards(top, face, 0.04)                            # nose, on the face side
        points[15] = _towards(_towards(top, head_angle, 0.025), face, 0.02)  # near eye
        points[17] = _towards(top, face + 180, 0.035)                    # near ear, back of the head
    else:
        points[0] = top
        for eye, ear, sign in ((14, 16, 180), (15, 17, 0)):
            points[eye] = _towards(_towards(top, head_angle, 0.025), across + sign, 0.025)
            points[ear] = _towards(top, across + sign, 0.055)
    # In side view the near limbs are drawn as the body's left side (OpenPose points 5-7 and 11-13).
    arm_slots = [(5, 6, 7), (2, 3, 4)] if side else [(2, 3, 4), (5, 6, 7)]
    leg_slots = [(11, 12, 13), (8, 9, 10)] if side else [(8, 9, 10), (11, 12, 13)]
    for i, (s, e, w) in enumerate(arm_slots):
        upper, lower = frame["arms"][i]
        points[s] = shoulders[i]
        points[e] = _towards(points[s], upper, LENGTHS["upper_arm"])
        points[w] = _towards(points[e], lower, LENGTHS["forearm"])
    for i, (h, k, a) in enumerate(leg_slots):
        thigh, shin = frame["legs"][i]
        points[h] = hips[i]
        points[k] = _towards(points[h], thigh, LENGTHS["thigh"])
        points[a] = _towards(points[k], shin, LENGTHS["shin"])
    if side:
        points[14] = points[16] = None  # far eye and ear are hidden behind the head
    return points


def draw_skeleton(points: list, size: int, box) -> Image.Image:
    import cv2

    (x0, y0), scale = box
    canvas = np.zeros((size, size, 3), np.uint8)
    pixels = [None if p is None else ((p[0] - x0) * scale, size - (p[1] - y0) * scale) for p in points]
    width = max(2, round(size / 128))
    for (a, b), color in zip(LIMBS, COLORS):
        p, q = pixels[a - 1], pixels[b - 1]
        if p is None or q is None:
            continue
        length = math.hypot(p[0] - q[0], p[1] - q[1])
        angle = math.degrees(math.atan2(p[1] - q[1], p[0] - q[0]))
        polygon = cv2.ellipse2Poly((int((p[0] + q[0]) / 2), int((p[1] + q[1]) / 2)), (int(length / 2), width),
                                   int(angle), 0, 360, 1)
        cv2.fillConvexPoly(canvas, polygon, [int(c * 0.6) for c in color])
    for point, color in zip(pixels, COLORS):
        if point is not None:
            cv2.circle(canvas, (int(point[0]), int(point[1])), width, color, thickness=-1)
    return Image.fromarray(canvas)


def specposes(args) -> None:
    """Make the start/end skeletons from written pose descriptions (exercise-poses.json), no video needed."""
    specs = json.loads(Path(args.specs).read_text(encoding="utf-8"))
    out = Path(args.poses)
    size = 64 if args.tiny else args.resolution
    manifest = []
    for spec in specs:
        view = spec.get("view", "side")
        frames = [spec_keypoints(spec[phase], view) for phase in ("start", "end")]
        # One shared scale for both frames, so the person keeps the same size and the loop doesn't jump.
        everything = [p for frame in frames for p in frame if p is not None]
        xs, ys = [p[0] for p in everything], [p[1] for p in everything]
        span = max(max(xs) - min(xs), max(ys) - min(ys), 0.5)
        scale = size * 0.76 / span
        x0 = (min(xs) + max(xs)) / 2 - size / 2 / scale
        y0 = (min(ys) + max(ys)) / 2 - size / 2 / scale
        folder = out / slugify(spec["name"])
        folder.mkdir(parents=True, exist_ok=True)
        for phase, points in zip(("start", "end"), frames):
            draw_skeleton(points, size, ((x0, y0), scale)).save(folder / f"{phase}-pose.png")
        manifest.append({"name": spec["name"], "slug": slugify(spec["name"]), "prompt": spec.get("prompt", "")})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{len(manifest)} exercises have start/end poses in {out}")


# --------------------------------------------------------------------------- generate

def clean(image: Image.Image, size: int) -> Image.Image:
    """Pure black ink on white, cropped to the figure and centred like the library drawings."""
    gray = np.asarray(image.convert("L"))
    ink = gray < 128
    page = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
    ys, xs = np.nonzero(ink)
    if len(xs):
        pad = 12
        page = page.crop((max(0, xs.min() - pad), max(0, ys.min() - pad),
                          min(page.width, xs.max() + pad), min(page.height, ys.max() + pad)))
    page = ImageOps.contain(page, (size - 24, size - 24), Image.LANCZOS)
    canvas = Image.new("L", (size, size), 255)
    canvas.paste(page, ((size - page.width) // 2, (size - page.height) // 2))
    return canvas.convert("RGB")


def clutter(image: Image.Image) -> float:
    """How much of a drawing looks like background: ink in the outer band, plus a little for ink overall."""
    ink = np.asarray(image.convert("L")) < 128
    band = max(1, ink.shape[0] // 10)
    edges = np.concatenate([ink[:band].ravel(), ink[-band:].ravel(), ink[:, :band].ravel(), ink[:, -band:].ravel()])
    return float(edges.mean() + 0.3 * ink.mean())


def generate(args) -> None:
    from diffusers import (ControlNetModel, StableDiffusionControlNetPipeline, UNet2DConditionModel,
                           UniPCMultistepScheduler)

    device, dtype = device_and_dtype(args.tiny)
    size = 64 if args.tiny else args.resolution
    if args.tiny:
        from diffusers import AutoencoderKL, DDIMScheduler
        from transformers import CLIPTextModel, CLIPTokenizer

        # The tiny test repo declares Flax classes in model_index.json, so assemble the pipeline by hand.
        unet = UNet2DConditionModel.from_pretrained(TINY_BASE, subfolder="unet")
        pipe = StableDiffusionControlNetPipeline(
            vae=AutoencoderKL.from_pretrained(TINY_BASE, subfolder="vae"),
            text_encoder=CLIPTextModel.from_pretrained(TINY_BASE, subfolder="text_encoder"),
            tokenizer=CLIPTokenizer.from_pretrained(TINY_BASE, subfolder="tokenizer"),
            # the tiny VAE only halves the image, so the pose embedding must downsample once, not 8x
            unet=unet, controlnet=ControlNetModel.from_unet(unet, conditioning_embedding_out_channels=(16, 32)),
            scheduler=DDIMScheduler.from_pretrained(TINY_BASE, subfolder="scheduler"),
            safety_checker=None, feature_extractor=None, requires_safety_checker=False)
    else:
        controlnet = ControlNetModel.from_pretrained(args.controlnet, torch_dtype=dtype)
        pipe = StableDiffusionControlNetPipeline.from_pretrained(args.base, controlnet=controlnet, torch_dtype=dtype,
                                                                 safety_checker=None, requires_safety_checker=False)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(args.lora)
    pipe.to(device)
    pipe.set_progress_bar_config(disable=True)

    poses_dir, out = Path(args.poses), Path(args.out)
    manifest = json.loads((poses_dir / "manifest.json").read_text(encoding="utf-8"))
    if args.limit:
        manifest = manifest[:args.limit]
    results = []
    for entry in manifest:
        folder = out / entry["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        detail = f", {entry['prompt']}" if entry.get("prompt") else ""
        prompt = (f"{TRIGGER}, black ink line drawing of a muscular bald man in shorts doing "
                  f"{entry['name'].lower()}{detail}, isolated figure on plain white background, thick black outlines")
        pairs = []
        for candidate in range(args.candidates):
            seed = args.seed + candidate  # same seed for start and end keeps the two frames alike
            pair = []
            for phase in ("start", "end"):
                pose = Image.open(poses_dir / entry["slug"] / f"{phase}-pose.png").convert("RGB").resize((size, size))
                generator = torch.Generator(device="cpu").manual_seed(seed)
                image = pipe(f"{prompt}, {phase} position", image=pose, negative_prompt=NEGATIVE,
                             num_inference_steps=2 if args.tiny else args.steps, guidance_scale=args.guidance,
                             controlnet_conditioning_scale=args.pose_strength, generator=generator,
                             height=size, width=size).images[0]
                pair.append(clean(image, 480))
            pairs.append(pair)
        # Cleanest pair first: library drawings have empty margins, so ink near the edges means a background.
        pairs.sort(key=lambda pair: sum(clutter(image) for image in pair))
        for rank, pair in enumerate(pairs, 1):
            for phase, image in zip(("start", "end"), pair):
                image.save(folder / f"{phase}-{rank}.png")
        results.append({**entry, "candidates": args.candidates})
        print("drawn:", entry["name"])
    (out / "manifest.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    contact_sheet(out, results, args.candidates)
    print(f"{len(results)} exercises drawn in {out}")


LINEART = "lllyasviel/control_v11p_sd15_lineart"


def stylize(args) -> None:
    """Redraw clean 3D line renders (<slug>-start.png / <slug>-end.png) in the learned style.

    The lineart ControlNet holds the exact outline from the 3D model, so the body and equipment keep their
    shape; the LoRA adds the Everkinetic look (muscle lines, ink weight).
    """
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler

    device, dtype = device_and_dtype(args.tiny)
    size = args.resolution
    controlnet = ControlNetModel.from_pretrained(args.controlnet if args.controlnet != CONTROLNET else LINEART,
                                                 torch_dtype=dtype)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(args.base, controlnet=controlnet, torch_dtype=dtype,
                                                             safety_checker=None, requires_safety_checker=False)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(args.lora)
    pipe.to(device)
    pipe.set_progress_bar_config(disable=True)

    specs = {slugify(s["name"]): s for s in json.loads(Path(args.specs).read_text(encoding="utf-8"))}
    renders = Path(args.renders)
    slugs = sorted({p.name.rsplit("-", 1)[0] for p in renders.rglob("*-start.png")})
    out = Path(args.out)
    results = []
    for slug in slugs:
        spec = specs.get(slug, {"name": slug.replace("-", " ").title(), "prompt": ""})
        detail = f", {spec['prompt']}" if spec.get("prompt") else ""
        prompt = (f"{TRIGGER}, black ink line drawing of a muscular bald man in shorts doing {spec['name'].lower()}"
                  f"{detail}, isolated figure on plain white background, thick black outlines")
        lines = {}
        for phase in ("start", "end"):
            source = next(renders.rglob(f"{slug}-{phase}.png"))
            # The lineart ControlNet expects white lines on black.
            lines[phase] = ImageOps.invert(square(Image.open(source).convert("L"), size, 255)).convert("RGB")
        pairs = []
        for candidate in range(args.candidates):
            seed = args.seed + candidate
            pair = []
            for phase in ("start", "end"):
                generator = torch.Generator(device="cpu").manual_seed(seed)
                image = pipe(f"{prompt}, {phase} position", image=lines[phase], negative_prompt=NEGATIVE,
                             num_inference_steps=args.steps, guidance_scale=args.guidance,
                             controlnet_conditioning_scale=args.pose_strength, generator=generator,
                             height=size, width=size).images[0]
                pair.append(clean(image, 480))
            pairs.append(pair)
        pairs.sort(key=lambda pair: sum(clutter(image) for image in pair))
        folder = out / slug
        folder.mkdir(parents=True, exist_ok=True)
        for rank, pair in enumerate(pairs, 1):
            for phase, image in zip(("start", "end"), pair):
                image.save(folder / f"{phase}-{rank}.png")
        for phase in ("start", "end"):  # keep the plain 3D drawing too, for comparison or as a fallback
            clean(Image.open(next(renders.rglob(f"{slug}-{phase}.png"))), 480).save(folder / f"{phase}-3d.png")
        results.append({"name": spec["name"], "slug": slug, "candidates": args.candidates})
        print("stylized:", spec["name"])
    (out / "manifest.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    contact_sheet(out, results, args.candidates)
    print(f"{len(results)} exercises stylized in {out}")


def contact_sheet(out: Path, results: list[dict], candidates: int) -> None:
    """One review image: each row is an exercise, each pair of columns a start/end candidate."""
    if not results:
        return
    tile = 160
    sheet = Image.new("RGB", (tile * 2 * candidates, tile * len(results)), "white")
    for row, entry in enumerate(results):
        for candidate in range(candidates):
            for col, phase in enumerate(("start", "end")):
                path = out / entry["slug"] / f"{phase}-{candidate + 1}.png"
                if path.exists():
                    sheet.paste(Image.open(path).resize((tile, tile)), ((candidate * 2 + col) * tile, row * tile))
    sheet.save(out / "review.png")


# --------------------------------------------------------------------------- cli

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["train", "poses", "specposes", "generate", "stylize"])
    parser.add_argument("--data", default="/kaggle/input", help="folder that contains metadata.jsonl")
    parser.add_argument("--clips", default="/kaggle/input", help="folder with exercise clips or start/end photos")
    parser.add_argument("--specs", default="exercise-poses.json", help="written start/end poses (specposes)")
    parser.add_argument("--renders", default="/kaggle/input", help="3D line renders <slug>-start/end.png (stylize)")
    parser.add_argument("--lora", default="/kaggle/working/lora")
    parser.add_argument("--poses", default="/kaggle/working/poses")
    parser.add_argument("--out", default="/kaggle/working/drawings")
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--controlnet", default=CONTROLNET)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--steps", type=int, default=None, help="training steps (train) or denoising steps (generate)")
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--samples", type=int, default=24, help="frames sampled from each video")
    parser.add_argument("--candidates", type=int, default=3, help="drawings per exercise; the cleanest is saved as 1")
    parser.add_argument("--limit", type=int, default=0, help="draw only the first N exercises (0 = all)")
    parser.add_argument("--guidance", type=float, default=7.0)
    parser.add_argument("--pose-strength", type=float, default=1.2)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--tiny", action="store_true", help="tiny test models, for checking the code on a CPU")
    args = parser.parse_args(argv)
    if args.steps is None:
        args.steps = {"train": 2000, "generate": 30}.get(args.command, 30)
    {"train": train, "poses": poses, "specposes": specposes, "generate": generate, "stylize": stylize}[args.command](args)


if __name__ == "__main__":
    main()
