import base64
import binascii
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from app.modules.ai_coach.application.dtos import (
    AnalyzeRequest, AnalyzeResponse, DaySummary, FoodResponse, MealCreate, MealItem, MealItemIn, MealResponse,
    TargetsResponse, Tip, Totals,
)
from app.modules.ai_coach.domain.nutrition import age_on, coaching_tip, daily_targets
from app.modules.ai_coach.infrastructure import foods as food_table
from app.modules.ai_coach.infrastructure import vision
from app.modules.ai_coach.infrastructure.repositories import MealLogRepository
from app.modules.progress.infrastructure.repositories import BodyProgressRepository
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository

MAX_IMAGE_BYTES = 4 * 1024 * 1024


SERVING = "serving"


def _num(value, low: float, high: float) -> Optional[float]:
    try:
        return min(high, max(low, float(value)))
    except (TypeError, ValueError):
        return None


def _units(food: food_table.Food, unit_grams: Optional[float]) -> List[food_table.FoodUnit]:
    """The food's own units, with a 'serving' of the photo-estimated weight first when there is one."""
    units = list(food.units)
    if unit_grams:
        units.insert(0, food_table.FoodUnit(SERVING, SERVING, round(unit_grams)))
    return units


def _item(food: food_table.Food, quantity: float, unit_label: Optional[str], confidence: Optional[float] = None,
          unit_grams: Optional[float] = None, name: Optional[str] = None, name_ur: Optional[str] = None,
          estimated: bool = False) -> MealItem:
    units = _units(food, unit_grams if unit_label in (None, SERVING) else None)
    unit = next((u for u in units if u.label == unit_label), units[0])
    grams = round(quantity * unit.grams, 1)
    desi = not (food.key.startswith("usda:") or food.key.startswith("est:"))
    return MealItem(
        food_key=food.key, name=(name if name and not desi else food.name),
        name_ur=(name_ur or name if (name_ur or name) and not desi else food.name_ur),
        quantity=quantity, unit=unit.label, unit_ur=unit.label_ur, grams=grams, confidence=confidence,
        estimated=estimated, unit_grams=unit.grams if unit.label == SERVING else None,
        per_100g={"kcal": food.kcal, "protein_g": food.protein_g, "carbs_g": food.carbs_g, "fat_g": food.fat_g},
        units=[{"label": u.label, "label_ur": u.label_ur, "grams": u.grams} for u in units],
        **food.macros(grams),
    )


def _estimate(name: str, per_100g: dict) -> food_table.Food:
    """A food in neither table, priced from the AI's per-100 g estimate."""
    slug = "-".join(name.lower().split())[:50] or "food"
    return food_table.Food(
        key=f"est:{slug}", name=name, name_ur=name, aliases=(), kcal=per_100g["kcal"],
        protein_g=per_100g["protein_g"], carbs_g=per_100g["carbs_g"], fat_g=per_100g["fat_g"],
        units=(food_table.FoodUnit("100 g", "100 g", 100.0),),
    )


def _sum(items: List[MealItem]) -> Totals:
    return Totals(
        kcal=round(sum(i.kcal for i in items)),
        protein_g=round(sum(i.protein_g for i in items), 1),
        carbs_g=round(sum(i.carbs_g for i in items), 1),
        fat_g=round(sum(i.fat_g for i in items), 1),
    )


class MealSnapService:
    def __init__(self, meals: MealLogRepository, profiles: UserProfileRepository, progress: BodyProgressRepository):
        self.meals = meals
        self.profiles = profiles
        self.progress = progress

    # Foods -------------------------------------------------------------------------------------------------------

    @staticmethod
    def list_foods() -> List[FoodResponse]:
        return [
            FoodResponse(
                key=f.key, name=f.name, name_ur=f.name_ur, aliases=list(f.aliases),
                units=[{"label": u.label, "label_ur": u.label_ur, "grams": u.grams} for u in f.units],
                per_100g={"kcal": f.kcal, "protein_g": f.protein_g, "carbs_g": f.carbs_g, "fat_g": f.fat_g},
            )
            for f in food_table.all_foods()
        ]

    @staticmethod
    def build_items(items_in: List[MealItemIn]) -> List[MealItem]:
        built = []
        for item in items_in:
            estimated = item.food_key.startswith("est:")
            if estimated:
                if not item.per_100g or not item.name:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{item.food_key} needs a name and per_100g.")
                food = _estimate(item.name, item.per_100g.model_dump())
            else:
                food = food_table.get_food(item.food_key)
            if not food:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown food: {item.food_key}")
            built.append(_item(food, item.quantity, item.unit, unit_grams=item.unit_grams, name=item.name,
                               name_ur=item.name_ur, estimated=estimated))
        return built

    @staticmethod
    def search_foods(query: str) -> List[FoodResponse]:
        return [
            FoodResponse(
                key=f.key, name=f.name, name_ur=f.name_ur, aliases=list(f.aliases),
                units=[{"label": u.label, "label_ur": u.label_ur, "grams": u.grams} for u in f.units],
                per_100g={"kcal": f.kcal, "protein_g": f.protein_g, "carbs_g": f.carbs_g, "fat_g": f.fat_g},
            )
            for f in food_table.search(query)
        ]

    # Photo -------------------------------------------------------------------------------------------------------

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        try:
            image = base64.b64decode(request.image_base64, validate=True)
        except (binascii.Error, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "The photo couldn't be read. Try another one.")
        if len(image) > MAX_IMAGE_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "The photo is too large. Use one under 4 MB.")
        foods = food_table.all_foods()
        try:
            result = vision.recognise(image, request.mime_type, foods)
        except vision.VisionUnavailable as error:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error))
        except vision.VisionFailed as error:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error))

        items, seen, unpriced = [], set(), []
        for raw in result["items"]:
            name = str(raw.get("name") or "").strip()[:80]
            name_ur = str(raw.get("name_ur") or "").strip()[:80] or None
            grams = _num(raw.get("grams"), 5, 1500)
            confidence = _num(raw.get("confidence"), 0, 1)
            confidence = round(confidence, 2) if confidence is not None else None
            food = food_table.get_food(str(raw.get("food_key", "")))
            if food and not food.key.startswith("usda:"):  # one of our desi foods: count in its household unit
                quantity = _num(raw.get("quantity"), 0, 20)
                quantity = round((quantity or 0) * 2) / 2
                if quantity <= 0 or food.key in seen:
                    continue
                seen.add(food.key)
                items.append(_item(food, quantity, None, confidence))
                continue
            if not name or name.lower() in seen or not grams:
                continue
            seen.add(name.lower())
            match = food_table.match(str(raw.get("usda_name") or "")) or food_table.match(name)
            if match:  # priced from the USDA table, one 'serving' of the estimated weight
                items.append(_item(match, 1, SERVING, confidence, unit_grams=grams, name=name, name_ur=name_ur))
                continue
            per_100g = {k: _num(raw.get(f"{src}_100g"), 0, 900 if k == "kcal" else 100)
                        for k, src in (("kcal", "kcal"), ("protein_g", "protein"), ("carbs_g", "carbs"), ("fat_g", "fat"))}
            if per_100g["kcal"] is None:
                unpriced.append(name)
                continue
            per_100g = {k: v or 0.0 for k, v in per_100g.items()}
            items.append(_item(_estimate(name, per_100g), grams / 100, None, confidence, name=name,
                               name_ur=name_ur, estimated=True))
        return AnalyzeResponse(is_food=result["is_food"], items=items[:20], other_foods=unpriced[:5])

    # Meals -------------------------------------------------------------------------------------------------------

    def create_meal(self, user_id: uuid.UUID, meal_in: MealCreate) -> MealResponse:
        items = self.build_items(meal_in.items)
        totals = _sum(items)
        now = datetime.now(timezone.utc)
        eaten_at = meal_in.eaten_at or now
        if eaten_at.tzinfo is None:
            eaten_at = eaten_at.replace(tzinfo=timezone.utc)
        if eaten_at > now + timedelta(minutes=5):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "A meal can't be in the future.")
        meal = self.meals.create(user_id, {
            "eaten_at": eaten_at, "source": meal_in.source,
            "items": [i.model_dump() for i in items], **totals.model_dump(),
        })
        return MealResponse.model_validate(meal)

    def delete_meal(self, user_id: uuid.UUID, meal_id: uuid.UUID) -> None:
        meal = self.meals.get(meal_id)
        if not meal or meal.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found.")
        self.meals.delete(meal)

    def day_summary(self, user_id: uuid.UUID, start: datetime, end: datetime) -> DaySummary:
        if end <= start or end - start > timedelta(hours=26):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ask for one day at a time.")
        meals = [MealResponse.model_validate(m) for m in self.meals.between(user_id, start, end)]
        totals = Totals(
            kcal=round(sum(m.kcal for m in meals)),
            protein_g=round(sum(m.protein_g for m in meals), 1),
            carbs_g=round(sum(m.carbs_g for m in meals), 1),
            fat_g=round(sum(m.fat_g for m in meals), 1),
        )
        profile = self.profiles.get_profile_by_user_id(user_id)
        latest = self.progress.get_latest_progress_by_user(user_id)
        weight = (latest.weight_kg if latest else None) or (profile.weight_kg if profile else None)
        targets = daily_targets(
            weight_kg=weight,
            height_cm=profile.height_cm if profile else None,
            age=age_on(profile.date_of_birth if profile else None, datetime.now(timezone.utc).date()),
            gender=profile.gender if profile else None,
            activity=profile.activity_level if profile else None,
            goal=profile.fitness_goal if profile else None,
        )
        egg = food_table.get_food("egg_boiled")
        per_unit = {"egg_boiled": egg.macros(egg.units[0].grams)["protein_g"]} if egg else {}
        tip = coaching_tip(totals.model_dump(), targets, len(meals), per_unit)
        return DaySummary(
            meals=meals, totals=totals,
            targets=TargetsResponse(kcal=targets.kcal, protein_g=targets.protein_g) if targets else None,
            tip=Tip(**tip), photo_recognition=vision.is_configured(),
        )
