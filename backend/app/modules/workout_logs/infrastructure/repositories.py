import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.modules.workout_logs.infrastructure.models import WorkoutLogModel


class WorkoutLogRepository:
    """
    SQLAlchemy repository implementation for Workout Log database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_log_by_id(self, log_id: uuid.UUID) -> Optional[WorkoutLogModel]:
        """
        Retrieves a workout log entry by unique UUID ID.
        """
        stmt = select(WorkoutLogModel).where(WorkoutLogModel.id == log_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_log_by_session_exercise_set(
        self,
        workout_session_id: uuid.UUID,
        workout_exercise_id: uuid.UUID,
        set_number: int
    ) -> Optional[WorkoutLogModel]:
        """
        Retrieves a log entry by workout_session_id, workout_exercise_id, and set_number.
        """
        stmt = select(WorkoutLogModel).where(
            and_(
                WorkoutLogModel.workout_session_id == workout_session_id,
                WorkoutLogModel.workout_exercise_id == workout_exercise_id,
                WorkoutLogModel.set_number == set_number
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_log(self, workout_session_id: uuid.UUID, data: dict) -> WorkoutLogModel:
        """
        Persists a new workout log entry in the database.
        """
        db_log = WorkoutLogModel(workout_session_id=workout_session_id, **data)
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    def list_logs_by_session(self, workout_session_id: uuid.UUID) -> List[WorkoutLogModel]:
        """
        Lists all log entries for a workout session ordered by created_at ascending.
        """
        stmt = (
            select(WorkoutLogModel)
            .where(WorkoutLogModel.workout_session_id == workout_session_id)
            .order_by(WorkoutLogModel.set_number.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_log(self, log: WorkoutLogModel, update_data: dict) -> WorkoutLogModel:
        """
        Updates an existing workout log entry.
        """
        for key, value in update_data.items():
            setattr(log, key, value)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def delete_log(self, log: WorkoutLogModel) -> None:
        """
        Deletes a workout log entry from the database.
        """
        self.db.delete(log)
        self.db.commit()
