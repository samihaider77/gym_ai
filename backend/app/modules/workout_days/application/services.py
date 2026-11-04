import uuid
from typing import List
from fastapi import HTTPException, status
from app.modules.workout_days.application.dtos import (
    WorkoutDayCreate,
    WorkoutDayUpdate,
    WorkoutDayResponse,
    WorkoutDayListResponse,
)
from app.modules.workout_days.infrastructure.models import WorkoutDayModel
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository


class WorkoutDayService:
    """
    Application Service orchestrating Workout Day use-cases and plan validation.
    """
    def __init__(self, day_repo: WorkoutDayRepository, plan_repo: WorkoutPlanRepository):
        self.day_repo = day_repo
        self.plan_repo = plan_repo

    def _verify_plan_ownership(self, workout_plan_id: uuid.UUID, user_id: uuid.UUID):
        """
        Helper method verifying parent plan existence and user ownership.
        """
        plan = self.plan_repo.get_plan_by_id(workout_plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent workout plan not found.",
            )
        if plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this workout plan.",
            )
        return plan

    def create_day(self, workout_plan_id: uuid.UUID, user_id: uuid.UUID, day_in: WorkoutDayCreate) -> WorkoutDayModel:
        """
        Creates a new workout day within a plan.
        Validates parent plan ownership, day_number >= 1, and day_number uniqueness per plan.
        """
        self._verify_plan_ownership(workout_plan_id, user_id)

        if day_in.day_number < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Day number must be greater than or equal to 1.",
            )

        existing_day = self.day_repo.get_day_by_plan_and_number(workout_plan_id, day_in.day_number)
        if existing_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workout day number {day_in.day_number} already exists in this plan.",
            )

        data = day_in.model_dump()
        return self.day_repo.create_day(workout_plan_id, data)

    def list_days(self, workout_plan_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutDayListResponse:
        """
        Lists all workout days in a plan ordered by day_number.
        """
        self._verify_plan_ownership(workout_plan_id, user_id)
        items = self.day_repo.list_days(workout_plan_id)
        responses = [WorkoutDayResponse.model_validate(item) for item in items]
        return WorkoutDayListResponse(items=responses, total=len(responses))

    def update_day(self, day_id: uuid.UUID, user_id: uuid.UUID, day_in: WorkoutDayUpdate) -> WorkoutDayModel:
        """
        Updates an existing workout day.
        Re-validates day_number uniqueness within the plan if changed.
        """
        day = self.day_repo.get_day_by_id(day_id)
        if not day:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout day not found.",
            )

        # Verify ownership via parent plan
        self._verify_plan_ownership(day.workout_plan_id, user_id)

        update_data = day_in.model_dump(exclude_unset=True)

        if "day_number" in update_data and update_data["day_number"] != day.day_number:
            if update_data["day_number"] < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Day number must be greater than or equal to 1.",
                )
            existing = self.day_repo.get_day_by_plan_and_number(day.workout_plan_id, update_data["day_number"])
            if existing and existing.id != day_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Workout day number {update_data['day_number']} already exists in this plan.",
                )

        return self.day_repo.update_day(day, update_data)

    def delete_day(self, day_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Deletes a workout day from a plan.
        """
        day = self.day_repo.get_day_by_id(day_id)
        if not day:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout day not found.",
            )

        self._verify_plan_ownership(day.workout_plan_id, user_id)
        self.day_repo.delete_day(day)
