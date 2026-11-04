import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.modules.workout_plans.infrastructure.models import WorkoutPlanModel


class WorkoutPlanRepository:
    """
    SQLAlchemy repository implementation for Workout Plan database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_plan_by_id(self, plan_id: uuid.UUID) -> Optional[WorkoutPlanModel]:
        """
        Retrieves a workout plan by unique UUID ID.
        """
        stmt = select(WorkoutPlanModel).where(WorkoutPlanModel.id == plan_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_plan_by_user_and_name(self, user_id: uuid.UUID, name: str) -> Optional[WorkoutPlanModel]:
        """
        Retrieves a workout plan by user ID and plan name (case-insensitive).
        """
        stmt = select(WorkoutPlanModel).where(
            and_(
                WorkoutPlanModel.user_id == user_id,
                func.lower(WorkoutPlanModel.name) == name.lower()
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_plan(self, user_id: uuid.UUID, plan_data: dict) -> WorkoutPlanModel:
        """
        Persists a new workout plan for the user in the database.
        """
        db_plan = WorkoutPlanModel(user_id=user_id, **plan_data)
        self.db.add(db_plan)
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

    def list_user_plans(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[WorkoutPlanModel], int]:
        """
        Lists workout plans owned by a specific user with pagination and is_active filtering.
        Returns a tuple of (items, total_count).
        """
        query = select(WorkoutPlanModel).where(WorkoutPlanModel.user_id == user_id)

        if is_active is not None:
            query = query.where(WorkoutPlanModel.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(WorkoutPlanModel.created_at.desc())

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    def update_plan(self, plan: WorkoutPlanModel, update_data: dict) -> WorkoutPlanModel:
        """
        Updates an existing workout plan record.
        """
        for key, value in update_data.items():
            setattr(plan, key, value)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def archive_plan(self, plan: WorkoutPlanModel) -> WorkoutPlanModel:
        """
        Soft deletes a workout plan record by setting is_active = False.
        """
        plan.is_active = False
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
