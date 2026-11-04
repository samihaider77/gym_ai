import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.workout_plans.application.dtos import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    WorkoutPlanResponse,
    WorkoutPlanListResponse,
)
from app.modules.workout_plans.application.services import WorkoutPlanService
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository

router = APIRouter()


@router.post(
    "",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workout plan",
    description="Creates a new workout plan for the currently authenticated user."
)
def create_plan_endpoint(
    plan_in: WorkoutPlanCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for workout plan creation.
    """
    repo = WorkoutPlanRepository(db)
    service = WorkoutPlanService(repo)
    return service.create_plan(current_user.id, plan_in)


@router.get(
    "",
    response_model=WorkoutPlanListResponse,
    status_code=status.HTTP_200_OK,
    summary="List workout plans of authenticated user",
    description="Retrieves a paginated list of workout plans owned by the currently authenticated user."
)
def list_plans_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for paginated workout plans listing.
    """
    repo = WorkoutPlanRepository(db)
    service = WorkoutPlanService(repo)
    return service.list_user_plans(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_active=is_active,
    )


@router.get(
    "/{id}",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workout plan details by ID",
    description="Retrieves details for a specific workout plan owned by the authenticated user."
)
def get_plan_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for retrieving a workout plan by ID.
    """
    repo = WorkoutPlanRepository(db)
    service = WorkoutPlanService(repo)
    return service.get_plan(id, current_user.id)


@router.put(
    "/{id}",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workout plan by ID",
    description="Updates attributes of an existing workout plan owned by the authenticated user."
)
def update_plan_endpoint(
    id: uuid.UUID,
    plan_in: WorkoutPlanUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for workout plan modification.
    """
    repo = WorkoutPlanRepository(db)
    service = WorkoutPlanService(repo)
    return service.update_plan(id, current_user.id, plan_in)


@router.delete(
    "/{id}",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete (archive) workout plan by ID",
    description="Soft deletes a workout plan by setting is_active = false."
)
def delete_plan_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP DELETE handler for archiving a workout plan.
    """
    repo = WorkoutPlanRepository(db)
    service = WorkoutPlanService(repo)
    return service.archive_plan(id, current_user.id)
