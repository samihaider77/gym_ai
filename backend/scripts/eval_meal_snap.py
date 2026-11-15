"""Measure how many foods Meal Snap finds on real multi-dish plates.

Test set: SOHL Multi-Dish Indian Food (MIT licence, huggingface.co/datasets/SohlHealth/sohl-multidish-yolo-dataset).
Each photo has boxes for 16 broad food types (bread, curry, rice, daal, salad, drink...). We send the photo through
the same code the app uses and check which of those food types Meal Snap reported.

Usage (from backend/, with GEMINI_API_KEY in .env):
    python scripts/eval_meal_snap.py <sample.json> <label>
    python scripts/eval_meal_snap.py --rescore <eval_results_label.json>
sample.json: [{"image": "<path>", "classes": [0, 3, 7]}, ...]  (paths relative to the json file)
Writes eval_results_<label>.json next to sample.json and prints the found / missed counts.
"""
import base64
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException  # noqa: E402

from app.modules.ai_coach.application.dtos import AnalyzeRequest  # noqa: E402
from app.modules.ai_coach.application.services import MealSnapService  # noqa: E402

CLASSES = ["bread", "curry", "rice", "dry vegetable", "snack", "sweet", "side (raita, chutney)", "daal", "drink",
           "eggs", "fish", "fruit", "pasta", "salad", "soup", "south indian breakfast"]

# The dataset's label files number the classes in alphabetical order of their names (uppercase first), not in the
# order its README and dataset.yaml list them. Checked by eye: a plate of chicken curry, rice and cucumber is
# labelled 3, 10, 11 = curry_dish, rice_dish, salad. This maps a label-file number to the CLASSES index above.
LABEL_FILE_ORDER = ["Dal_or_sambar", "accompaniment", "bread_or_Roti_naan", "curry_dish", "drink", "dry_vegetable",
                    "eggs", "fish_dish", "fruits", "pasta", "rice_dish", "salad", "snack_item", "soup",
                    "south_indian_breakfast", "sweet_item"]
README_ORDER = ["bread_or_Roti_naan", "curry_dish", "rice_dish", "dry_vegetable", "snack_item", "sweet_item",
                "accompaniment", "Dal_or_sambar", "drink", "eggs", "fish_dish", "fruits", "pasta", "salad", "soup",
                "south_indian_breakfast"]
FROM_LABEL_FILE = {i: README_ORDER.index(name) for i, name in enumerate(LABEL_FILE_ORDER)}

# Words in a reported food's name (or key) that place it in one of the 16 test-set types.
KEYWORDS = [
    (0, r"roti|naan|nan\b|paratha|chapati|bread|puri|kulcha|bhatura|toast"),
    (1, r"curry|korma|qorma|karahi|masala|paneer|chole|chana|gravy|salan|gosht|keema|nihari|kofta|makhani"),
    (2, r"rice|biryani|pulao|pilaf|chawal|khichdi"),
    (3, r"sabzi|vegetable|bhindi|okra|aloo|potato|cabbage|beans|gobi|cauliflower|stir|bhaji|poriyal"),
    (4, r"samosa|pakora|fries|chips|snack|kebab|kabab|vada|cutlet|tikki|bhel|nuggets|momo|dumpling|fox nut|makhana"),
    (5, r"sweet|dessert|kheer|halwa|gulab|cake|mithai|ice cream|barfi|jalebi|ladoo|firni"),
    (6, r"raita|chutney|pickle|achar|papad|yogurt|dahi|sauce|ketchup"),
    (7, r"daal|dal\b|lentil|sambar|sambhar"),
    (8, r"tea|chai|coffee|juice|milk|lassi|soda|coke|cola|drink|water|shake|smoothie"),
    (9, r"egg|omelet|anda"),
    (10, r"fish|prawn|shrimp|machli|seafood"),
    (11, r"fruit|banana|apple|mango|orange|grape|papaya|melon|kela|saib|pomegranate|guava"),
    (12, r"pasta|noodle|spaghetti|macaroni|penne|chow mein"),
    # The dataset labels raw onion, lemon and chilli garnish on the side of a plate as "salad".
    (13, r"salad|cucumber|lettuce|kachumber|sliced tomato|onion|lemon|lime|green chil"),
    (14, r"soup|broth|rasam|yakhni"),
    (15, r"dosa|idli|uttapam|upma|poha|appam"),
]


def types_of(item) -> set:
    text = f"{item.get('name', '')} {item.get('food_key', '')}".lower().replace("_", " ")
    return {cls for cls, pattern in KEYWORDS if re.search(pattern, text)}


def rescore(results_path: str):
    """Score saved answers again (for example after fixing the label mapping) without calling the API."""
    path = Path(results_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    sample = {r["image"]: r["classes"] for r in json.loads((path.parent / "sample.json").read_text(encoding="utf-8"))}
    found = total = extra = 0
    missed = {}
    for r in data["results"]:
        if "error" in r:
            continue
        truth = {FROM_LABEL_FILE[c] for c in sample[r["image"]]}
        reported = set().union(*[types_of({"name": i}) for i in r["items"]]) if r["items"] else set()
        found += len(truth & reported)
        total += len(truth)
        extra += len(reported - truth)
        for c in truth - reported:
            missed[CLASSES[c]] = missed.get(CLASSES[c], 0) + 1
    print(json.dumps({"food_types": total, "found": found, "found_pct": round(100 * found / total, 1),
                      "reported_but_not_in_labels": extra,
                      "missed_by_type": dict(sorted(missed.items(), key=lambda kv: -kv[1]))}, indent=1))


def main(sample_path: str, label: str, delay: float = 4.5):
    sample_file = Path(sample_path)
    rows = json.loads(sample_file.read_text(encoding="utf-8"))
    service = MealSnapService(None, None, None)
    results, found, found_priced, total, extra, failed = [], 0, 0, 0, 0, 0
    for n, row in enumerate(rows, 1):
        image = (sample_file.parent / row["image"]).read_bytes()
        mime = "image/png" if row["image"].lower().endswith(".png") else "image/jpeg"
        try:
            answer = service.analyze(AnalyzeRequest(image_base64=base64.b64encode(image).decode(), mime_type=mime))
            items = [i.model_dump() for i in answer.items] + [{"name": o} for o in answer.other_foods]
        except HTTPException as error:
            print(f"{n:3}/{len(rows)} failed: {error.detail}")
            failed += 1
            results.append({"image": row["image"], "error": error.detail})
            if error.status_code == 503:
                break
            time.sleep(delay)
            continue
        reported = set().union(*[types_of(i) for i in items]) if items else set()
        priced_items = [i for i in items if "kcal" in i]  # other_foods were seen but got no calories
        priced = set().union(*[types_of(i) for i in priced_items]) if priced_items else set()
        truth = {FROM_LABEL_FILE[c] for c in row["classes"]}
        hit = truth & reported
        found += len(hit)
        found_priced += len(truth & priced)
        total += len(truth)
        extra += len(reported - truth)
        results.append({"image": row["image"], "truth": sorted(truth), "reported": sorted(reported),
                        "missed": [CLASSES[c] for c in sorted(truth - reported)],
                        "unpriced": [CLASSES[c] for c in sorted((truth & reported) - priced)],
                        "items": [i.get("name") or i.get("food_key") for i in items],
                        "priced_items": [{"name": i["name"], "key": i["food_key"], "grams": i["grams"],
                                          "kcal": i["kcal"], "estimated": i.get("estimated")} for i in priced_items]})
        print(f"{n:3}/{len(rows)} found {len(hit)}/{len(truth)}  missed: {', '.join(CLASSES[c] for c in sorted(truth - reported)) or '-'}")
        time.sleep(delay)
    missed = {}
    for r in results:
        for m in r.get("missed", []):
            missed[m] = missed.get(m, 0) + 1
    summary = {"label": label, "photos": len(results) - failed, "failed": failed, "food_types": total,
               "found": found, "found_pct": round(100 * found / total, 1) if total else None,
               "found_with_calories": found_priced,
               "found_with_calories_pct": round(100 * found_priced / total, 1) if total else None,
               "estimated_items": sum(1 for r in results for i in r.get("priced_items", []) if i["estimated"]),
               "priced_items": sum(len(r.get("priced_items", [])) for r in results),
               "reported_but_not_in_labels": extra,
               "missed_by_type": dict(sorted(missed.items(), key=lambda kv: -kv[1]))}
    (sample_file.parent / f"eval_results_{label}.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "--rescore":
        rescore(sys.argv[2])
    else:
        main(sys.argv[1], sys.argv[2])
