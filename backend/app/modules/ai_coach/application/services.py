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


def _item(food: food_table.Food, quantity: float, unit_label: Optional[str], confidence: Optional[float] = None) -> MealItem:
    unit = food.unit(unit_label)
    grams = round(quantity * unit.grams, 1)
    return MealItem(
        food_key=food.key, name=food.name, name_ur=food.name_ur, quantity=quantity, unit=unit.label,
        unit_ur=unit.label_ur, grams=grams, confidence=confidence, **food.macros(grams),
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
            food = food_table.get_food(item.food_key)
            if not food:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown food: {item.food_key}")
            built.append(_item(food, item.quantity, item.unit))
        return built

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

        items, seen = [], set()
        for raw in result["items"]:
            food = food_table.get_food(str(raw.get("food_key", "")))
            try:
                quantity = round(float(raw.get("quantity", 0)) * 2) / 2  # nearest half unit
            except (TypeError, ValueError):
                continue
            if not food or quantity <= 0 or food.key in seen:
                continue
            seen.add(food.key)
            confidence = raw.get("confidence")
            items.append(_item(food, min(quantity, 20), None,
                               round(float(confidence), 2) if isinstance(confidence, (int, float)) else None))
        return AnalyzeResponse(is_food=result["is_food"], items=items, other_foods=result["other_foods"][:5])

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
