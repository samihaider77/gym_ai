"""Food data for Meal Snap: calories and macros per 100 g.

Two tables, both built by scripts/build_desi_foods.py from USDA FoodData Central (FNDDS, public domain):
- desi_foods.json: 35 everyday Pakistani foods with household units (roti, katori, plate). Checked first.
- usda_foods.json: all ~5,400 FNDDS foods, for anything else on the plate (salad, fries, fruit, pasta...).
The AI only recognises foods and portions; every calorie and gram of protein is computed from these tables.
"""
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA = Path(__file__).resolve().parents[4] / "data"
DESI_FILE = DATA / "desi_foods.json"
USDA_FILE = DATA / "usda_foods.json"


@dataclass(frozen=True)
class FoodUnit:
    label: str
    label_ur: str
    grams: float


@dataclass(frozen=True)
class Food:
    key: str  # desi key ("roti") or "usda:<fdc_id>"
    name: str
    name_ur: str
    aliases: tuple
    kcal: float  # per 100 g
    protein_g: float
    carbs_g: float
    fat_g: float
    units: tuple  # FoodUnit, the first is the default
    words: frozenset = field(default=frozenset(), compare=False)

    def unit(self, label: Optional[str]) -> FoodUnit:
        return next((u for u in self.units if u.label == label), self.units[0])

    def macros(self, grams: float) -> Dict[str, float]:
        return macros_for(grams, self.kcal, self.protein_g, self.carbs_g, self.fat_g)


def macros_for(grams: float, kcal: float, protein_g: float, carbs_g: float, fat_g: float) -> Dict[str, float]:
    f = grams / 100.0
    return {"kcal": round(kcal * f), "protein_g": round(protein_g * f, 1),
            "carbs_g": round(carbs_g * f, 1), "fat_g": round(fat_g * f, 1)}


# Words that describe preparation or packaging rather than the food; ignored when matching names.
STOP = {"a", "an", "the", "and", "or", "with", "of", "in", "on", "style", "plain", "fresh", "homemade", "home",
        "made", "indian", "pakistani", "desi", "piece", "pieces", "slice", "slices", "bowl", "plate", "cup", "glass",
        "side", "serving", "some", "small", "large", "medium", "ns", "nfs", "as", "to", "type", "from", "added",
        "fat", "no", "sliced", "chopped", "dish"}


ALCOHOL = {"rum", "beer", "wine", "vodka", "whiskey", "gin", "liqueur", "cocktail", "margarita", "brandy", "tequila"}


def _words(text: str) -> List[str]:
    out = []
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 4 and w.endswith("oes"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


@lru_cache(maxsize=1)
def _desi() -> Dict[str, Food]:
    raw = json.loads(DESI_FILE.read_text(encoding="utf-8"))
    foods = {}
    for row in raw["foods"]:
        n = row["per_100g"]
        foods[row["key"]] = Food(
            key=row["key"], name=row["name"], name_ur=row["name_ur"], aliases=tuple(row["aliases"]),
            kcal=n["kcal"], protein_g=n["protein_g"], carbs_g=n["carbs_g"], fat_g=n["fat_g"],
            units=tuple(FoodUnit(u["label"], u["label_ur"], float(u["grams"])) for u in row["units"]),
            words=frozenset(_words(" ".join((row["name"], row["name_ur"], *row["aliases"])))),
        )
    return foods


@lru_cache(maxsize=1)
def _usda() -> Dict[str, Food]:
    raw = json.loads(USDA_FILE.read_text(encoding="utf-8"))
    foods = {}
    for fdc_id, desc, kcal, protein, carbs, fat, portions in raw["foods"]:
        units = [FoodUnit(label, label, float(g)) for label, g in portions] + [FoodUnit("100 g", "100 g", 100.0)]
        key = f"usda:{fdc_id}"
        foods[key] = Food(key=key, name=desc, name_ur=desc, aliases=(), kcal=kcal, protein_g=protein,
                          carbs_g=carbs, fat_g=fat, units=tuple(units), words=frozenset(_words(desc)))
    return foods


def all_foods() -> List[Food]:
    """The desi table: the list the AI is shown and the quick-pick list in the app."""
    return list(_desi().values())


def get_food(key: str) -> Optional[Food]:
    return _desi().get(key) or (_usda().get(key) if key.startswith("usda:") else None)


def _score(query: List[str], food: Food) -> float:
    """Share of the query's words found in the food's name, with a small bonus for short, general names."""
    if not query:
        return 0.0
    hits = sum(1 for w in query if w in food.words)
    if hits == 0:
        return 0.0
    name = food.name.lower()
    general_bonus = 0.04 if (" nfs" in name or "raw" in food.words) else 0.0
    # USDA names the main food first ("Pizza, cheese, thin crust"); prefer those over "Pizza rolls" for "pizza".
    head_bonus = 0.2 if re.match(rf"{re.escape(query[0])}[a-z]{{0,3}},", name) else 0.0
    alcohol = 0.5 if (food.words & ALCOHOL) and not (set(query) & ALCOHOL) else 0.0
    extra = max(0, len(food.words) - len(query))
    return hits / len(query) + general_bonus + head_bonus - alcohol - 0.03 * min(extra, 6)


def search(query: str, limit: int = 15) -> List[Food]:
    """Desi foods first, then USDA foods, ranked by how well their names match the query."""
    words = _words(query)
    if not words:
        return all_foods()[:limit]
    scored: List[Tuple[float, int, Food]] = []
    for rank, table in enumerate((_desi(), _usda())):
        for food in table.values():
            s = _score(words, food)
            if s >= 0.5:
                scored.append((s + (0.3 if rank == 0 else 0.0), -len(food.name), food))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [f for _, _, f in scored[:limit]]


def match(name: str) -> Optional[Food]:
    """The USDA food that best fits a name from the AI ("cucumber raw"), or None if nothing fits well enough.
    A candidate must contain every word of a one- or two-word name, or two thirds of a longer one; among those,
    the shortest, most general name wins."""
    words = _words(name)
    if not words:
        return None
    needed = len(words) if len(words) <= 2 else -(-2 * len(words) // 3)
    best, best_score = None, float("-inf")
    for food in _usda().values():
        if sum(1 for w in words if w in food.words) < needed:
            continue
        s = _score(words, food)
        if s > best_score:
            best, best_score = food, s
    return best
