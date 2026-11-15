from datetime import datetime
from typing import List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class FoodUnitResponse(BaseModel):
    label: str
    label_ur: str
    grams: float


class FoodResponse(BaseModel):
    key: str
    name: str
    name_ur: str
    aliases: List[str]
    units: List[FoodUnitResponse]
    per_100g: dict


class MealItemIn(BaseModel):
    food_key: str = Field(..., max_length=50)
    quantity: float = Field(..., gt=0, le=50)
    unit: Optional[str] = Field(None, max_length=40, description="Unit label; defaults to the food's first unit")


class MealItem(BaseModel):
    """A food with its portion and macros computed from the food table."""
    food_key: str
    name: str
    name_ur: str
    quantity: float
    unit: str
    unit_ur: str
    grams: float
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: Optional[float] = None


class AnalyzeRequest(BaseModel):
    image_base64: str = Field(..., min_length=100, max_length=6_000_000, description="JPEG/PNG/WebP, base64")
    mime_type: Literal["image/jpeg", "image/png", "image/webp"] = "image/jpeg"


class AnalyzeResponse(BaseModel):
    is_food: bool
    items: List[MealItem]
    other_foods: List[str]


class MealCreate(BaseModel):
    items: List[MealItemIn] = Field(..., min_length=1, max_length=20)
    eaten_at: Optional[datetime] = None
    source: Literal["photo", "manual"] = "manual"


class MealResponse(BaseModel):
    id: uuid.UUID
    eaten_at: datetime
    source: str
    items: List[MealItem]
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float

    model_config = ConfigDict(from_attributes=True)


class Totals(BaseModel):
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class TargetsResponse(BaseModel):
    kcal: int
    protein_g: int


class Tip(BaseModel):
    en: str
    ur: str


class DaySummary(BaseModel):
    meals: List[MealResponse]
    totals: Totals
    targets: Optional[TargetsResponse]
    tip: Tip
    photo_recognition: bool
