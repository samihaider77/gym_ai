"""Food photo recognition with the Google Gemini API (REST, no extra dependency).

The model is told which foods exist in our table and must answer with their keys, a quantity in each food's
household unit, and a confidence. It never gives calories: those come from the food table.
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
    menu = "\n".join(
        f"- {f.key}: {f.name} (also called {', '.join((f.name_ur,) + f.aliases)}); unit = {f.units[0].label} "
        f"(about {f.units[0].grams:g} g)"
        for f in foods
    )
    return (
        "You look at a photo of a meal from Pakistan or South Asia and list what is on the plate.\n"
        "Use only these food keys. Give the quantity in the food's unit (for example 2 roti, 1.5 katori, "
        "0.5 plate). Estimate portions from plate, bowl and hand size.\n"
        f"{menu}\n"
        "If a visible food is not in the list, put its name in `other_foods` instead of guessing a key.\n"
        "If the photo is not food, return no items and set `is_food` to false."
    )


def _schema(foods: List[Food]) -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "is_food": {"type": "BOOLEAN"},
            "items": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "food_key": {"type": "STRING", "enum": [f.key for f in foods]},
                        "quantity": {"type": "NUMBER"},
                        "confidence": {"type": "NUMBER", "description": "0 to 1"},
                    },
                    "required": ["food_key", "quantity", "confidence"],
                },
            },
            "other_foods": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": ["is_food", "items", "other_foods"],
    }


def recognise(image: bytes, mime_type: str, foods: List[Food], timeout: float = 25.0) -> dict:
    """Returns {"is_food": bool, "items": [{food_key, quantity, confidence}], "other_foods": [str]}."""
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
        "other_foods": [str(o) for o in result.get("other_foods", []) if str(o).strip()],
    }
