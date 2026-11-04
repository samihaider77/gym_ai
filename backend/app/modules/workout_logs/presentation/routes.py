import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.workout_logs.application.dtos import (
    WorkoutLogCreate,
    WorkoutLogUpdate,
    WorkoutLogResponse,
    WorkoutLogListResponse,
)
from app.modules.workout_logs.application.services import WorkoutLogService
from app.modules.workout_logs.infrastructure.repositories import WorkoutLogRepository
from app.modules.workout_sessions.infrastructure.repositories import WorkoutSessionRepository
from app.modules.workout_exercises.infrastructure.repositories import WorkoutExerciseRepository

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> WorkoutLogService:
    log_repo = WorkoutLogRepository(db)
    session_repo = WorkoutSessionRepository(db)
    we_repo = WorkoutExerciseRepository(db)
    return WorkoutLogService(log_repo, session_repo, we_repo)


@router.post(
    "/workout-sessions/{session_id}/logs",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a set log to a workout session",
    description="Logs a completed set (reps, weight, duration, rest) for an exercise within a workout session."
)
def create_log_endpoint(
    session_id: uuid.UUID,
    log_in: WorkoutLogCreate,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutLogService = Depends(get_service)
):
    """
    HTTP POST handler for logging a workout set.
    """
    return service.create_log(session_id, current_user.id, log_in)


@router.get(
    "/workout-sessions/{session_id}/logs",
    response_model=WorkoutLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List set logs for a workout session",
    description="Retrieves all logged sets for a specific workout session."
)
def list_logs_endpoint(
    session_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutLogService = Depends(get_service)
):
    """
    HTTP GET handler for listing set logs in a workout session.
    """
    return service.list_logs_by_session(session_id, current_user.id)


@router.put(
    "/workout-logs/{id}",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Update set log entry by ID",
    description="Updates reps, weight, duration, or rest time of a logged set."
)
def update_log_endpoint(
    id: uuid.UUID,
    log_in: WorkoutLogUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutLogService = Depends(get_service)
):
    """
    HTTP PUT handler for modifying a set log entry.
    """
    return service.update_log(id, current_user.id, log_in)


@router.delete(
    "/workout-logs/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete set log entry by ID",
    description="Removes a set log entry from a workout session."
)
def delete_log_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutLogService = Depends(get_service)
):
    """
    HTTP DELETE handler for removing a set log entry.
    """
    service.delete_log(id, current_user.id)
    return None
