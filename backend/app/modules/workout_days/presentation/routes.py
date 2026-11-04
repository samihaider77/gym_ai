import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.workout_days.application.dtos import (
    WorkoutDayCreate,
    WorkoutDayUpdate,
    WorkoutDayResponse,
    WorkoutDayListResponse,
)
from app.modules.workout_days.application.services import WorkoutDayService
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository

router = APIRouter()


@router.post(
    "/workout-plans/{plan_id}/days",
    response_model=WorkoutDayResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workout day in a plan",
    description="Adds a new workout day to a specific workout plan owned by the authenticated user."
)
def create_day_endpoint(
    plan_id: uuid.UUID,
    day_in: WorkoutDayCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for adding a day to a workout plan.
    """
    day_repo = WorkoutDayRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    service = WorkoutDayService(day_repo, plan_repo)
    return service.create_day(plan_id, current_user.id, day_in)


@router.get(
    "/workout-plans/{plan_id}/days",
    response_model=WorkoutDayListResponse,
    status_code=status.HTTP_200_OK,
    summary="List workout days in a plan",
    description="Retrieves all workout days for a workout plan ordered by day_number."
)
def list_days_endpoint(
    plan_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for listing days in a workout plan.
    """
    day_repo = WorkoutDayRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    service = WorkoutDayService(day_repo, plan_repo)
    return service.list_days(plan_id, current_user.id)


@router.put(
    "/workout-days/{id}",
    response_model=WorkoutDayResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workout day by ID",
    description="Updates attributes of a workout day owned by the authenticated user."
)
def update_day_endpoint(
    id: uuid.UUID,
    day_in: WorkoutDayUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for workout day modification.
    """
    day_repo = WorkoutDayRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    service = WorkoutDayService(day_repo, plan_repo)
    return service.update_day(id, current_user.id, day_in)


@router.delete(
    "/workout-days/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workout day by ID",
    description="Deletes a workout day from a plan."
)
def delete_day_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP DELETE handler for removing a workout day.
    """
    day_repo = WorkoutDayRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    service = WorkoutDayService(day_repo, plan_repo)
    service.delete_day(id, current_user.id)
    return None
