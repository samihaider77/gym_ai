"""Shared naming rules for catalog imports, so every source maps onto one equipment list."""
import re

# Lower-case source spelling -> canonical equipment name shown in the app.
EQUIPMENT_ALIASES = {
    "": "Bodyweight", "none": "Bodyweight", "body": "Bodyweight", "body only": "Bodyweight",
    "bodyweight": "Bodyweight", "body weight": "Bodyweight", "none (bodyweight exercise)": "Bodyweight",
    "gym mat": "Bodyweight",
    "bar": "Barbell", "barbell": "Barbell",
    "dumbbell": "Dumbbell", "dumbbells": "Dumbbell",
    "kettlebell": "Kettlebell", "kettlebells": "Kettlebell",
    "band": "Resistance Band", "bands": "Resistance Band", "exercise band": "Resistance Band",
    "resistance band": "Resistance Band",
    "cable": "Cable Machine", "cable machine": "Cable Machine",
    "machine": "Machine", "chest machine": "Machine",
    "smith machine": "Smith Machine",
    "bench": "Bench", "flat bench": "Bench", "incline bench": "Bench",
    "swiss ball": "Exercise Ball", "exercise ball": "Exercise Ball", "stability ball": "Exercise Ball",
    "sz-bar": "E-Z Curl Bar", "ez-bar": "E-Z Curl Bar", "e-z curl bar": "E-Z Curl Bar",
    "pull-up bar": "Pull-Up Bar",
}

_SMALL_WORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "or", "the", "to", "with"}


def canonical_equipment(raw: str | None) -> str:
    key = (raw or "").strip().lower()
    return EQUIPMENT_ALIASES.get(key) or key.title()


def display_name(name: str) -> str:
    """Title-case names that arrive in sentence case ("Alternating bicep curls"); leave mixed case alone."""
    name = re.sub(r"\s+", " ", name).strip()
    words = name.split(" ")
    if any(w[:1].isupper() for w in words[1:]):
        return name
    return " ".join(
        w if i and w.lower() in _SMALL_WORDS else w[:1].upper() + w[1:]
        for i, w in enumerate(words)
    )


def is_house_style(provider: str | None, attribution: str | None) -> bool:
    """True for the Everkinetic line drawings, the largest set of demos in one visual style.

    They come straight from Everkinetic, through wger ("... illustration by Everkinetic via wger.de"), or from
    the GymAI drawing notebook, which draws new exercises in the same style (tools/ai-drawings).
    Media in other styles (photos, real videos, other illustrators, the GymAI3D test renders) is kept but hidden.
    """
    return provider in {"Everkinetic", "GymAI"} or "by Everkinetic" in (attribution or "")
