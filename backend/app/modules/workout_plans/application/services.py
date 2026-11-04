import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.modules.workout_plans.application.dtos import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    WorkoutPlanResponse,
    WorkoutPlanListResponse,
)
from app.modules.workout_plans.infrastructure.models import WorkoutPlanModel
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository


class WorkoutPlanService:
    """
    Application Service orchestrating Workout Plan use-cases and ownership validation.
    """
    def __init__(self, plan_repo: WorkoutPlanRepository):
        self.plan_repo = plan_repo

    def create_plan(self, user_id: uuid.UUID, plan_in: WorkoutPlanCreate) -> WorkoutPlanModel:
        """
        Creates a new workout plan for the user.
        Enforces rule: Plan names must be unique per user.
        """
        existing_plan = self.plan_repo.get_plan_by_user_and_name(user_id, plan_in.name)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workout plan with name '{plan_in.name}' already exists for your account.",
            )

        plan_data = plan_in.model_dump()
        plan_data["is_active"] = True
        return self.plan_repo.create_plan(user_id, plan_data)

    def get_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutPlanModel:
        """
        Retrieves a workout plan owned by the user.
        Raises HTTP 404 if not found and HTTP 403 if owned by another user.
        """
        plan = self.plan_repo.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout plan not found.",
            )
        if plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this workout plan.",
            )
        return plan

    def list_user_plans(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
    ) -> WorkoutPlanListResponse:
        """
        Retrieves a paginated list of workout plans owned by the user.
        """
        items, total = self.plan_repo.list_user_plans(
            user_id=user_id,
            page=page,
            page_size=page_size,
            is_active=is_active,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [WorkoutPlanResponse.model_validate(item) for item in items]

        return WorkoutPlanListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID, plan_in: WorkoutPlanUpdate) -> WorkoutPlanModel:
        """
        Updates an existing workout plan owned by the user.
        Re-validates plan name uniqueness per user if the name is changed.
        """
        plan = self.get_plan(plan_id, user_id)

        update_data = plan_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"].lower() != plan.name.lower():
            existing = self.plan_repo.get_plan_by_user_and_name(user_id, update_data["name"])
            if existing and existing.id != plan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Workout plan with name '{update_data['name']}' already exists for your account.",
                )

        return self.plan_repo.update_plan(plan, update_data)

    def archive_plan(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutPlanModel:
        """
        Soft deletes (archives) a workout plan owned by the user by setting is_active = False.
        """
        plan = self.get_plan(plan_id, user_id)
        return self.plan_repo.archive_plan(plan)
