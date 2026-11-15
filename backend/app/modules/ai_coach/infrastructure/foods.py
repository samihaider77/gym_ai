"""The desi food table (backend/data/desi_foods.json): calories and macros for Meal Snap.

The numbers come from USDA FoodData Central (FNDDS, public domain); scripts/build_desi_foods.py builds the file.
The AI only recognises foods and portions; every calorie and gram of protein is computed from this table.
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

DATA_FILE = Path(__file__).resolve().parents[4] / "data" / "desi_foods.json"


@dataclass(frozen=True)
class FoodUnit:
    label: str
    label_ur: str
    grams: float


@dataclass(frozen=True)
class Food:
    key: str
    name: str
    name_ur: str
    aliases: tuple
    kcal: float  # per 100 g
    protein_g: float
    carbs_g: float
    fat_g: float
    units: tuple  # FoodUnit, the first is the default

    def unit(self, label: Optional[str]) -> FoodUnit:
        return next((u for u in self.units if u.label == label), self.units[0])

    def macros(self, grams: float) -> Dict[str, float]:
        f = grams / 100.0
        return {
            "kcal": round(self.kcal * f),
            "protein_g": round(self.protein_g * f, 1),
            "carbs_g": round(self.carbs_g * f, 1),
            "fat_g": round(self.fat_g * f, 1),
        }


@lru_cache(maxsize=1)
def _table() -> Dict[str, Food]:
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    foods = {}
    for row in raw["foods"]:
        n = row["per_100g"]
        foods[row["key"]] = Food(
            key=row["key"], name=row["name"], name_ur=row["name_ur"], aliases=tuple(row["aliases"]),
            kcal=n["kcal"], protein_g=n["protein_g"], carbs_g=n["carbs_g"], fat_g=n["fat_g"],
            units=tuple(FoodUnit(u["label"], u["label_ur"], float(u["grams"])) for u in row["units"]),
        )
    return foods


def all_foods() -> List[Food]:
    return list(_table().values())


def get_food(key: str) -> Optional[Food]:
    return _table().get(key)
