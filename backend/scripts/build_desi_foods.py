"""Build backend/data/desi_foods.json, the food table Meal Snap uses for calories and macros.

Every number comes from USDA FoodData Central, FNDDS 2021-2023 (public domain, CC0):
https://fdc.nal.usda.gov/download-datasets/ -> "FoodData_Central_survey_food_json_2024-10-31.zip".

Usage:
    python scripts/build_desi_foods.py <path-to-surveyDownload.json>

Each dish maps to one FNDDS food (or a small recipe of FNDDS foods for chai and lassi). Household units
(roti, katori, plate, piece) use FNDDS portion weights where FNDDS has them, otherwise a stated multiple
of the FNDDS "1 cup" weight (katori = 3/4 cup, plate = 1.5 cups).
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "desi_foods.json"
USDA_OUT = Path(__file__).resolve().parents[1] / "data" / "usda_foods.json"

KATORI = ("cup", 0.75)
PLATE = ("cup", 1.5)
GLASS = ("cup", 1.0)

# key, English name, Roman Urdu name, aliases, FNDDS description (or recipe), units
# A unit is (label, label_ur, source) where source is ("portion", "<text in FNDDS portion>"), ("cup", factor)
# or ("grams", g).
DISHES = [
    ("roti", "Roti (chapati)", "Roti", ["chapati", "phulka"], "Bread, chappatti or roti",
     [("roti", "roti", ("portion", "1 medium chappatti"))]),
    ("paratha", "Paratha", "Paratha", ["parantha"], "Bread, paratha",
     [("paratha", "paratha", ("portion", "1 paratha"))]),
    ("naan", "Naan", "Naan", ["nan", "roghni naan"], "Bread, naan",
     [("naan", "naan", ("portion", "1 Naan (10"))]),
    ("rice", "Plain rice", "Saada chawal", ["boiled rice", "chawal"], "Rice, white, cooked, no added fat",
     [("plate", "plate", PLATE), ("katori", "katori", KATORI)]),
    ("pulao", "Pulao", "Pulao", ["yakhni pulao", "rice pilaf"], "Rice pilaf",
     [("plate", "plate", PLATE), ("katori", "katori", KATORI)]),
    ("chicken_biryani", "Chicken biryani", "Chicken biryani", ["biryani"], "Biryani with chicken",
     [("plate", "plate", PLATE), ("katori", "katori", KATORI)]),
    ("meat_biryani", "Beef or mutton biryani", "Gosht biryani", ["mutton biryani", "beef biryani"], "Biryani with meat",
     [("plate", "plate", PLATE), ("katori", "katori", KATORI)]),
    ("daal", "Daal (lentil curry)", "Daal", ["dal", "daal masoor", "daal mash", "daal chana"], "Lentil curry",
     [("katori", "katori", KATORI)]),
    ("chana", "Chana (chickpeas)", "Chanay", ["cholay", "chana masala"], "Chickpeas, from dried, fat added",
     [("katori", "katori", KATORI)]),
    ("chicken_curry", "Chicken curry / karahi", "Chicken salan / karahi", ["chicken karahi", "chicken qorma", "chicken salan"],
     "Chicken curry", [("katori", "katori", KATORI)]),
    ("beef_curry", "Beef or mutton curry", "Gosht ka salan", ["aloo gosht", "qorma", "nihari", "mutton karahi"],
     "Beef curry", [("katori", "katori", KATORI)]),
    ("fish_curry", "Fish curry", "Machli ka salan", ["machli"], "Fish curry", [("katori", "katori", KATORI)]),
    ("sabzi", "Vegetable curry", "Sabzi", ["aloo gobi", "mix sabzi", "aloo matar"], "Vegetable curry",
     [("katori", "katori", KATORI)]),
    ("bhindi", "Bhindi (okra)", "Bhindi", ["okra"], "Okra, fresh, cooked, fat added", [("katori", "katori", KATORI)]),
    ("palak_paneer", "Palak paneer", "Palak paneer", ["saag paneer"], "Palak Paneer", [("katori", "katori", KATORI)]),
    ("chicken_tikka", "Chicken tikka / grilled chicken", "Chicken tikka", ["tandoori chicken", "bbq chicken", "grilled chicken"],
     "Chicken, NS as to part, grilled without sauce, skin not eaten", [("piece", "piece", ("grams", 100))]),
    ("chicken_breast", "Chicken breast", "Chicken breast", ["boiled chicken"],
     "Chicken breast, baked, broiled, or roasted, skin not eaten, from raw", [("100 g", "100 g", ("grams", 100))]),
    ("kabab", "Kabab (beef)", "Kabab", ["seekh kabab", "shami kabab", "chapli kabab"], "Beef, ground, patty",
     [("kabab", "kabab", ("grams", 60))]),
    ("samosa", "Samosa", "Samosa", [], "Samosa", [("samosa", "samosa", ("portion", "1 regular/large"))]),
    ("pakora", "Pakora", "Pakora", ["pakoray"], "Pakora", [("pakora", "pakora", ("portion", "1 pakora"))]),
    ("egg_boiled", "Boiled egg", "Ubla anda", ["anda"], "Egg, whole, boiled or poached",
     [("egg", "anda", ("portion", "1 egg"))]),
    ("egg_fried", "Fried egg", "Fried anda", [], "Egg, whole, fried with oil", [("egg", "anda", ("portion", "1 egg"))]),
    ("omelette", "Omelette", "Omelette", ["anda bhurji"], "Egg omelet or scrambled egg, made with oil",
     [("2-egg omelette", "2 anday ka omelette", ("grams", 110))]),
    ("dahi", "Dahi (plain yogurt)", "Dahi", ["yogurt", "raita"], "Yogurt, whole milk, plain", [("katori", "katori", KATORI)]),
    ("milk", "Milk", "Doodh", [], "Milk, whole", [("glass", "glass", GLASS)]),
    ("chai", "Chai (milk tea with sugar)", "Chai", ["doodh patti", "tea"],
     [("Milk, whole", 75), ("Tea, hot, leaf, black", 75), ("Sugar, white, granulated or lump", 8)],
     [("cup", "cup", ("grams", 158))]),
    ("lassi", "Sweet lassi", "Meethi lassi", ["lassi"],
     [("Yogurt, whole milk, plain", 180), ("Sugar, white, granulated or lump", 15)],
     [("glass", "glass", ("grams", 195))]),
    ("kheer", "Kheer / firni", "Kheer", ["firni"], "Firni, Indian pudding", [("katori", "katori", KATORI)]),
    ("mithai", "Mithai (barfi)", "Mithai", ["barfi", "burfi"], "Barfi or Burfi, Indian dessert",
     [("piece", "piece", ("portion", "1 piece"))]),
    ("bread", "White bread", "Double roti", ["toast", "bread slice"], "Bread, white",
     [("slice", "slice", ("portion", "1 medium or regular slice"))]),
    ("oats", "Oats with milk", "Oats", ["oatmeal", "daliya"], "Oatmeal, regular or quick, made with milk, no added fat",
     [("katori", "katori", ("grams", 180))]),
    ("peanut_butter", "Peanut butter", "Peanut butter", [], "Peanut butter", [("tablespoon", "chamach", ("portion", "1 tablespoon"))]),
    ("whey", "Whey protein shake (water)", "Whey protein", ["protein shake"], "Nutritional powder mix, whey based, NFS",
     [("scoop", "scoop", ("grams", 30))]),
    ("banana", "Banana", "Kela", [], "Banana, raw", [("banana", "kela", ("portion", "1 banana"))]),
    ("apple", "Apple", "Saib", [], "Apple, raw", [("apple", "saib", ("portion", "1 medium"))]),
]

NUTRIENTS = {"208": "kcal", "203": "protein_g", "205": "carbs_g", "204": "fat_g"}


def per100(food):
    out = {v: 0.0 for v in NUTRIENTS.values()}
    for n in food["foodNutrients"]:
        key = NUTRIENTS.get(n["nutrient"]["number"])
        if key:
            out[key] = float(n["amount"])
    return out


def main(src):
    foods = {f["description"]: f for f in json.load(open(src, encoding="utf-8"))["SurveyFoods"]}
    rows = []
    for key, name, name_ur, aliases, fndds, units in DISHES:
        if isinstance(fndds, str):
            food = foods[fndds]
            nutr = per100(food)
            portions = food["foodPortions"]
            source = {"fdc_id": food["fdcId"], "description": fndds}
        else:  # small recipe of FNDDS foods: (description, grams)
            total = sum(g for _, g in fndds)
            nutr = {v: 0.0 for v in NUTRIENTS.values()}
            for desc, g in fndds:
                for k, v in per100(foods[desc]).items():
                    nutr[k] += v * g / total
            portions = []
            source = {"recipe": [{"fdc_id": foods[d]["fdcId"], "description": d, "grams": g} for d, g in fndds]}
        cup = next((p["gramWeight"] for p in portions if p["portionDescription"].lower().startswith("1 cup")), None)
        built_units = []
        for label, label_ur, (kind, value) in units:
            if kind == "portion":
                match = next((p for p in portions if p["portionDescription"].lower().startswith(value.lower())), None)
                if not match:
                    raise SystemExit(f"{key}: no FNDDS portion starting '{value}': "
                                     f"{[p['portionDescription'] for p in portions]}")
                grams = match["gramWeight"]
            elif kind == "cup":
                if not cup:
                    raise SystemExit(f"{key}: no '1 cup' portion")
                grams = round(cup * value)
            else:
                grams = value
            built_units.append({"label": label, "label_ur": label_ur, "grams": grams})
        rows.append({
            "key": key, "name": name, "name_ur": name_ur, "aliases": aliases,
            "per_100g": {k: round(v, 1) for k, v in nutr.items()},
            "units": built_units, "source": source,
        })
    OUT.write_text(json.dumps({
        "source": "USDA FoodData Central, FNDDS 2021-2023 (public domain). Built by scripts/build_desi_foods.py.",
        "foods": rows,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(rows)} foods to {OUT}")
    build_usda(foods.values())


def build_usda(foods):
    """Every FNDDS food in a compact form, so Meal Snap can price foods outside the desi table.
    Row: [fdc_id, description, kcal, protein_g, carbs_g, fat_g, [[portion, grams], ...]] (per 100 g)."""
    rows = []
    for food in foods:
        n = per100(food)
        portions = [[p["portionDescription"], p["gramWeight"]] for p in food["foodPortions"]
                    if p["gramWeight"] and p["portionDescription"] != "Quantity not specified"
                    and "surface inch" not in p["portionDescription"] and "cubic inch" not in p["portionDescription"]]
        rows.append([food["fdcId"], food["description"], round(n["kcal"]), round(n["protein_g"], 1),
                     round(n["carbs_g"], 1), round(n["fat_g"], 1), portions[:4]])
    USDA_OUT.write_text(json.dumps({
        "source": "USDA FoodData Central, FNDDS 2021-2023 (public domain). Built by scripts/build_desi_foods.py.",
        "columns": ["fdc_id", "description", "kcal", "protein_g", "carbs_g", "fat_g", "portions"],
        "foods": rows,
    }, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(rows)} foods to {USDA_OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
