from datetime import datetime, timezone
import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.modules.workout_sessions.application.dtos import (
    WorkoutSessionStart,
    WorkoutSessionFinish,
    WorkoutSessionCancel,
    WorkoutSessionResponse,
    WorkoutSessionListResponse,
)
from app.modules.workout_sessions.domain.entities import (
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
)
from app.modules.workout_sessions.infrastructure.models import WorkoutSessionModel
from app.modules.workout_sessions.infrastructure.repositories import WorkoutSessionRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository


class WorkoutSessionService:
    """
    Application Service orchestrating Workout Session lifecycle and business rules.
    """
    def __init__(
        self,
        session_repo: WorkoutSessionRepository,
        plan_repo: WorkoutPlanRepository,
        day_repo: WorkoutDayRepository,
    ):
        self.session_repo = session_repo
        self.plan_repo = plan_repo
        self.day_repo = day_repo

    def start_session(self, user_id: uuid.UUID, start_in: WorkoutSessionStart) -> WorkoutSessionModel:
        """
        Starts a new workout session for the user.
        Enforces rule: Only ONE active workout session per user.
        """
        # 1. Check active session
        active_session = self.session_repo.get_active_session_by_user(user_id)
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active workout session in progress. Finish or cancel it first.",
            )

        # 2. Verify plan ownership
        plan = self.plan_repo.get_plan_by_id(start_in.workout_plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this workout plan.",
            )

        # 3. Verify day exists in plan
        day = self.day_repo.get_day_by_id(start_in.workout_day_id)
        if not day or day.workout_plan_id != start_in.workout_plan_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout day not found in the specified workout plan.",
            )

        session_data = start_in.model_dump()
        session_data["started_at"] = datetime.now(timezone.utc)
        session_data["status"] = STATUS_IN_PROGRESS
        session_data["duration_minutes"] = 0

        return self.session_repo.create_session(user_id, session_data)

    def finish_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        finish_in: WorkoutSessionFinish
    ) -> WorkoutSessionModel:
        """
        Completes an active workout session.
        Calculates duration automatically in minutes.
        """
        session = self.session_repo.get_session_by_id(session_id)
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
        if session.status != STATUS_IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot finish a session with status '{session.status}'. Only IN_PROGRESS sessions can be finished.",
            )

        now = datetime.now(timezone.utc)
        # Calculate duration in minutes (minimum 1 minute)
        elapsed_seconds = (now - session.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        duration_minutes = max(1, int(elapsed_seconds // 60))

        update_data = {
            "completed_at": now,
            "duration_minutes": duration_minutes,
            "status": STATUS_COMPLETED,
        }
        if finish_in.calories_burned is not None:
            update_data["calories_burned"] = finish_in.calories_burned
        if finish_in.notes:
            update_data["notes"] = finish_in.notes

        return self.session_repo.update_session(session, update_data)

    def cancel_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        cancel_in: WorkoutSessionCancel
    ) -> WorkoutSessionModel:
        """
        Cancels an active workout session.
        """
        session = self.session_repo.get_session_by_id(session_id)
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
        if session.status != STATUS_IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel a session with status '{session.status}'. Only IN_PROGRESS sessions can be cancelled.",
            )

        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - session.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        duration_minutes = max(0, int(elapsed_seconds // 60))

        update_data = {
            "completed_at": now,
            "duration_minutes": duration_minutes,
            "status": STATUS_CANCELLED,
        }
        if cancel_in.notes:
            update_data["notes"] = cancel_in.notes

        return self.session_repo.update_session(session, update_data)

    def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutSessionModel:
        """
        Retrieves a workout session by ID.
        """
        session = self.session_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout session not found.",
            )
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this workout session.",
            )
        return session

    def list_user_sessions(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> WorkoutSessionListResponse:
        """
        Retrieves a paginated list of workout sessions owned by the user.
        """
        items, total = self.session_repo.list_user_sessions(
            user_id=user_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [WorkoutSessionResponse.model_validate(item) for item in items]

        return WorkoutSessionListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
