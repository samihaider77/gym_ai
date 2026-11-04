import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.modules.workout_days.infrastructure.models import WorkoutDayModel


class WorkoutDayRepository:
    """
    SQLAlchemy repository implementation for Workout Day database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_day_by_id(self, day_id: uuid.UUID) -> Optional[WorkoutDayModel]:
        """
        Retrieves a workout day by unique UUID ID.
        """
        stmt = select(WorkoutDayModel).where(WorkoutDayModel.id == day_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_day_by_plan_and_number(self, workout_plan_id: uuid.UUID, day_number: int) -> Optional[WorkoutDayModel]:
        """
        Retrieves a workout day by parent workout_plan_id and day_number.
        """
        stmt = select(WorkoutDayModel).where(
            and_(
                WorkoutDayModel.workout_plan_id == workout_plan_id,
                WorkoutDayModel.day_number == day_number
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_day(self, workout_plan_id: uuid.UUID, data: dict) -> WorkoutDayModel:
        """
        Persists a new workout day in the database.
        """
        db_day = WorkoutDayModel(workout_plan_id=workout_plan_id, **data)
        self.db.add(db_day)
        self.db.commit()
        self.db.refresh(db_day)
        return db_day

    def list_days(self, workout_plan_id: uuid.UUID) -> List[WorkoutDayModel]:
        """
        Lists all workout days for a workout plan ordered by day_number ascending.
        """
        stmt = (
            select(WorkoutDayModel)
            .where(WorkoutDayModel.workout_plan_id == workout_plan_id)
            .order_by(WorkoutDayModel.day_number.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_day(self, day: WorkoutDayModel, update_data: dict) -> WorkoutDayModel:
        """
        Updates an existing workout day.
        """
        for key, value in update_data.items():
            setattr(day, key, value)
        self.db.add(day)
        self.db.commit()
        self.db.refresh(day)
        return day

    def delete_day(self, day: WorkoutDayModel) -> None:
        """
        Deletes a workout day record from the database.
        """
        self.db.delete(day)
        self.db.commit()
