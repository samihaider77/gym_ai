import uuid
from typing import List
from fastapi import HTTPException, status
from app.modules.workout_logs.application.dtos import (
    WorkoutLogCreate,
    WorkoutLogUpdate,
    WorkoutLogResponse,
    WorkoutLogListResponse,
)
from app.modules.workout_logs.infrastructure.models import WorkoutLogModel
from app.modules.workout_logs.infrastructure.repositories import WorkoutLogRepository
from app.modules.workout_sessions.infrastructure.repositories import WorkoutSessionRepository
from app.modules.workout_exercises.infrastructure.repositories import WorkoutExerciseRepository


class WorkoutLogService:
    """
    Application Service orchestrating Workout Log creation, validation, and session tracking.
    """
    def __init__(
        self,
        log_repo: WorkoutLogRepository,
        session_repo: WorkoutSessionRepository,
        we_repo: WorkoutExerciseRepository,
    ):
        self.log_repo = log_repo
        self.session_repo = session_repo
        self.we_repo = we_repo

    def _verify_session_ownership(self, workout_session_id: uuid.UUID, user_id: uuid.UUID):
        """
        Helper method verifying workout session existence and user ownership.
        """
        session = self.session_repo.get_session_by_id(workout_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout session not found.",
            )
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this workout session.",
            )
        return session

    def create_log(
        self,
        workout_session_id: uuid.UUID,
        user_id: uuid.UUID,
        log_in: WorkoutLogCreate
    ) -> WorkoutLogModel:
        """
        Creates a set log entry for an active workout session.
        Validates set_number > 0, completed_reps >= 0, completed_weight >= 0.
        """
        self._verify_session_ownership(workout_session_id, user_id)

        # 1. Verify workout exercise configuration existence
        we = self.we_repo.get_by_id(log_in.workout_exercise_id)
        if not we:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout exercise configuration not found.",
            )

        # 2. Validate business rules
        if log_in.set_number <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set number must be greater than zero.",
            )
        if log_in.completed_reps < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed reps cannot be negative.",
            )
        if log_in.completed_weight < 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed weight cannot be negative.",
            )

        # 3. Check duplicate set number for same exercise in session
        existing = self.log_repo.get_log_by_session_exercise_set(
            workout_session_id,
            log_in.workout_exercise_id,
            log_in.set_number
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Set number {log_in.set_number} has already been logged for this exercise in this session.",
            )

        data = log_in.model_dump()
        return self.log_repo.create_log(workout_session_id, data)

    def list_logs_by_session(self, workout_session_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutLogListResponse:
        """
        Lists all completed set logs for a workout session.
        """
        self._verify_session_ownership(workout_session_id, user_id)
        items = self.log_repo.list_logs_by_session(workout_session_id)
        responses = [WorkoutLogResponse.model_validate(item) for item in items]
        return WorkoutLogListResponse(items=responses, total=len(responses))

    def update_log(self, log_id: uuid.UUID, user_id: uuid.UUID, log_in: WorkoutLogUpdate) -> WorkoutLogModel:
        """
        Updates an existing set log entry.
        """
        log = self.log_repo.get_log_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout log entry not found.",
            )

        self._verify_session_ownership(log.workout_session_id, user_id)
        update_data = log_in.model_dump(exclude_unset=True)

        if "set_number" in update_data and update_data["set_number"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set number must be greater than zero.",
            )
        if "completed_reps" in update_data and update_data["completed_reps"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed reps cannot be negative.",
            )
        if "completed_weight" in update_data and update_data["completed_weight"] < 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed weight cannot be negative.",
            )

        return self.log_repo.update_log(log, update_data)

    def delete_log(self, log_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Deletes a set log entry.
        """
        log = self.log_repo.get_log_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout log entry not found.",
            )

        self._verify_session_ownership(log.workout_session_id, user_id)
        self.log_repo.delete_log(log)
