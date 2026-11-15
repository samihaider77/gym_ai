import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.ai_coach.application.dtos import (
    AnalyzeRequest, AnalyzeResponse, DaySummary, FoodResponse, MealCreate, MealResponse,
)
from app.modules.ai_coach.application.services import MealSnapService
from app.modules.ai_coach.infrastructure.repositories import MealLogRepository
from app.modules.progress.infrastructure.repositories import BodyProgressRepository
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> MealSnapService:
    return MealSnapService(MealLogRepository(db), UserProfileRepository(db), BodyProgressRepository(db))


@router.get("/foods", response_model=List[FoodResponse], summary="List the desi food table")
def list_foods(_: UserModel = Depends(get_current_user)):
    return MealSnapService.list_foods()


@router.get("/foods/search", response_model=List[FoodResponse], summary="Search desi and USDA foods by name")
def search_foods(q: str = Query(..., min_length=1, max_length=60), _: UserModel = Depends(get_current_user)):
    return MealSnapService.search_foods(q)


@router.post("/meals/analyze", response_model=AnalyzeResponse, summary="Recognise the foods in a meal photo")
def analyze_meal(
    body: AnalyzeRequest,
    _: UserModel = Depends(get_current_user),
    service: MealSnapService = Depends(get_service),
):
    """Nothing is saved: the user checks and edits the items, then saves them with POST /ai/meals."""
    return service.analyze(body)


@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED, summary="Save a meal")
def create_meal(
    body: MealCreate,
    current_user: UserModel = Depends(get_current_user),
    service: MealSnapService = Depends(get_service),
):
    return service.create_meal(current_user.id, body)


@router.get("/meals/day", response_model=DaySummary, summary="Meals, totals, targets and a tip for one day")
def day_summary(
    start: datetime = Query(..., description="Start of the user's local day, ISO 8601 with offset"),
    end: datetime = Query(..., description="End of the user's local day, ISO 8601 with offset"),
    current_user: UserModel = Depends(get_current_user),
    service: MealSnapService = Depends(get_service),
):
    return service.day_summary(current_user.id, start, end)


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a meal")
def delete_meal(
    meal_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: MealSnapService = Depends(get_service),
):
    service.delete_meal(current_user.id, meal_id)
