"""Food photo recognition with the Google Gemini API (REST, no extra dependency).

The model lists every food in the photo with a name, an estimated weight and, for our 35 desi foods, the dish key and
a count in its household unit. Calories come from our tables; the model's own per-100 g numbers are used only for a
food that is in neither table, and such items are marked as estimates.
"""
import base64
import json
import urllib.error
import urllib.request
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.modules.ai_coach.infrastructure.foods import Food

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class VisionUnavailable(Exception):
    """No API key is configured, or the provider refused the request (quota, auth)."""


class VisionFailed(Exception):
    """The provider answered, but not with something we could use."""


def is_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def _prompt(foods: List[Food]) -> str:
    menu = [
        f"- {f.key}: {f.name} (also called {', '.join((f.name_ur,) + f.aliases)}); unit = {f.units[0].label} "
        f"(about {f.units[0].grams:g} g)"
        for f in foods
    ]
    lines = [
        "You look at a photo of a meal and list EVERY food and drink you can see: mains, breads, rice, sides, "
        "salad, raita, chutney, pickle, sweets, fruit and drinks. Do not skip small items.",
        "For each item give:",
        "- name: short English name (e.g. 'cucumber salad', 'mint raita').",
        "- name_ur: the same name in Roman Urdu as people in Pakistan say it (e.g. 'kheera salad').",
        "- food_key: one of the keys below if the item is that food, otherwise 'other'.",
        "- quantity: for a listed key, how many of its unit (e.g. 2 roti, 1.5 katori, 0.5 plate). For 'other', 1.",
        "- grams: your estimate of the item's weight in grams. Judge from how full each bowl or plate is and from "
        "objects of known size (spoon, roti, hand, glass).",
        "- usda_name: for 'other' items, a generic name in the style of the USDA food database "
        "(e.g. 'Cucumber, raw', 'Soft drink, cola', 'Fish, fried', 'Pasta with tomato sauce').",
        "- kcal_100g, protein_100g, carbs_100g, fat_100g: typical values per 100 g, used only if the food is not "
        "in our database.",
        "- confidence: 0 to 1.",
        "Known foods:",
        *menu,
        "If the photo is not food, return no items and set `is_food` to false.",
    ]
    return "\n".join(lines)


def _schema(foods: List[Food]) -> dict:
    number = {"type": "NUMBER"}
    return {
        "type": "OBJECT",
        "properties": {
            "is_food": {"type": "BOOLEAN"},
            "items": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "name_ur": {"type": "STRING"},
                        "food_key": {"type": "STRING", "enum": [f.key for f in foods] + ["other"]},
                        "quantity": number,
                        "grams": number,
                        "usda_name": {"type": "STRING"},
                        "kcal_100g": number,
                        "protein_100g": number,
                        "carbs_100g": number,
                        "fat_100g": number,
                        "confidence": number,
                    },
                    "required": ["name", "food_key", "quantity", "grams", "kcal_100g", "protein_100g", "carbs_100g",
                                 "fat_100g", "confidence"],
                },
            },
        },
        "required": ["is_food", "items"],
    }


def recognise(image: bytes, mime_type: str, foods: List[Food], timeout: float = 45.0) -> dict:
    """Returns {"is_food": bool, "items": [{name, name_ur, food_key, quantity, grams, usda_name, *_100g, confidence}]}."""
    if not is_configured():
        raise VisionUnavailable("Photo recognition isn't set up yet. Add the foods by hand for now.")
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image).decode("ascii")}},
            {"text": _prompt(foods)},
        ]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": _schema(foods),
        },
    }
    request = urllib.request.Request(
        API.format(model=settings.GEMINI_MODEL),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY or ""},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        logger.warning(f"Gemini returned {error.code}: {detail}")
        if error.code in (401, 403, 429):
            raise VisionUnavailable(
                "Photo recognition is busy or has hit today's free limit. Add the foods by hand, or try later."
            ) from error
        raise VisionFailed("Couldn't read the photo. Try again or add the foods by hand.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        logger.warning(f"Gemini request failed: {error}")
        raise VisionFailed("Couldn't reach the photo service. Try again or add the foods by hand.") from error

    text: Optional[str] = None
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        logger.warning(f"Unexpected Gemini answer: {str(text or payload)[:300]}")
        raise VisionFailed("Couldn't read the photo. Try again or add the foods by hand.") from error
    return {
        "is_food": bool(result.get("is_food", True)),
        "items": [i for i in result.get("items", []) if isinstance(i, dict)],
    }
