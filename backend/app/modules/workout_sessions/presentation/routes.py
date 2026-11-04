import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.workout_sessions.application.dtos import (
    WorkoutSessionStart,
    WorkoutSessionFinish,
    WorkoutSessionCancel,
    WorkoutSessionResponse,
    WorkoutSessionListResponse,
)
from app.modules.workout_sessions.application.services import WorkoutSessionService
from app.modules.workout_sessions.infrastructure.repositories import WorkoutSessionRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> WorkoutSessionService:
    session_repo = WorkoutSessionRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    day_repo = WorkoutDayRepository(db)
    return WorkoutSessionService(session_repo, plan_repo, day_repo)


@router.post(
    "/start",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new workout session",
    description="Starts an active workout session. Only one session can be active at a time."
)
def start_session_endpoint(
    start_in: WorkoutSessionStart,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutSessionService = Depends(get_service)
):
    """
    HTTP POST handler for starting a workout session.
    """
    return service.start_session(current_user.id, start_in)


@router.post(
    "/{id}/finish",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Finish active workout session by ID",
    description="Completes an active workout session and automatically computes duration in minutes."
)
def finish_session_endpoint(
    id: uuid.UUID,
    finish_in: WorkoutSessionFinish,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutSessionService = Depends(get_service)
):
    """
    HTTP POST handler for completing a workout session.
    """
    return service.finish_session(id, current_user.id, finish_in)


@router.post(
    "/{id}/cancel",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel active workout session by ID",
    description="Cancels an active workout session."
)
def cancel_session_endpoint(
    id: uuid.UUID,
    cancel_in: WorkoutSessionCancel,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutSessionService = Depends(get_service)
):
    """
    HTTP POST handler for cancelling a workout session.
    """
    return service.cancel_session(id, current_user.id, cancel_in)


@router.get(
    "",
    response_model=WorkoutSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List workout sessions of authenticated user",
    description="Retrieves a paginated list of workout sessions owned by the currently authenticated user."
)
def list_sessions_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by session status (IN_PROGRESS, COMPLETED, CANCELLED)"),
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutSessionService = Depends(get_service)
):
    """
    HTTP GET handler for paginated workout session listing.
    """
    return service.list_user_sessions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.get(
    "/{id}",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workout session details by ID",
    description="Retrieves details for a specific workout session owned by the authenticated user."
)
def get_session_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutSessionService = Depends(get_service)
):
    """
    HTTP GET handler for retrieving a workout session by ID.
    """
    return service.get_session(id, current_user.id)
