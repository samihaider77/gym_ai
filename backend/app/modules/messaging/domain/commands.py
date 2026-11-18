"""Turn a chat message into a command. Pure functions: no database, no network.

Members type short words in English or Roman Urdu ("today", "aaj", "kal ka workout", "wazan 78"); buttons send
their command id. Anything we don't recognise becomes UNKNOWN and gets the help menu.
"""
import re
from dataclasses import dataclass
from typing import Optional

LINK = "link"
STOP = "stop"
HELP = "help"
TODAY = "today"
TOMORROW = "tomorrow"
WEEK = "week"
DIET = "diet"
DONE = "done"
WEIGHT = "weight"
LANGUAGE = "language"
UNKNOWN = "unknown"

# Letters for link codes: no 0/O, 1/I/L, so a code read off a screen can't be mistyped.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8

_LINK_RE = re.compile(rf"^\s*link\s*[:#-]?\s*([{CODE_ALPHABET.lower()}]{{4}})[\s-]?([{CODE_ALPHABET.lower()}]{{4}})\s*$")
_NUMBER_RE = re.compile(r"(\d{2,3}(?:[.,]\d)?)")

# Checked in order; the first group with a matching word wins. Words are matched whole.
_WORDS = [
    (STOP, {"stop", "unsubscribe", "unlink", "disconnect", "band"}),
    (WEIGHT, {"weight", "wazan", "wazn", "weigh"}),
    (DONE, {"done", "finished", "complete", "completed", "khatam", "hogaya", "hogya", "ho"}),
    (DIET, {"diet", "food", "khana", "khaun", "eat", "meal", "meals", "protein", "calories", "calorie", "kcal",
            "nutrition", "macros"}),
    (TOMORROW, {"tomorrow", "kal", "next"}),
    (WEEK, {"week", "hafta", "schedule", "weekly"}),
    (TODAY, {"today", "aaj", "aj", "workout", "exercise", "exercises", "warzish"}),
    (WEEK, {"plan"}),
    (HELP, {"help", "menu", "madad", "hi", "hello", "salam", "assalam", "aoa", "start", "commands"}),
]
_LANG = {"urdu": "ur", "english": "en", "angrezi": "en"}


@dataclass(frozen=True)
class Command:
    name: str
    code: Optional[str] = None  # LINK: the 8-letter code, upper case, no dash
    weight_kg: Optional[float] = None  # WEIGHT
    language: Optional[str] = None  # LANGUAGE: "en" | "ur"


def parse(text: str) -> Command:
    raw = (text or "").strip().lower()
    if not raw:
        return Command(UNKNOWN)
    link = _LINK_RE.match(raw)
    if link:
        return Command(LINK, code=(link.group(1) + link.group(2)).upper())
    words = set(re.findall(r"[a-z]+", raw))
    if len(words) <= 2:
        for word, lang in _LANG.items():
            if word in words:
                return Command(LANGUAGE, language=lang)
    for name, keys in _WORDS:
        if words & keys:
            if name == DONE and "ho" in words and not words & {"gaya", "gya", "gai"}:
                continue  # "ho" alone is too common; only "ho gaya" means done
            if name == WEIGHT:
                number = _NUMBER_RE.search(raw)
                kg = float(number.group(1).replace(",", ".")) if number else None
                return Command(WEIGHT, weight_kg=kg)
            return Command(name)
    if raw in {"?", "/start", "/help"}:
        return Command(HELP)
    return Command(UNKNOWN)


def format_code(code: str) -> str:
    """'7KQ2M9XD' -> '7KQ2-M9XD', easier to read."""
    return f"{code[:4]}-{code[4:]}"
