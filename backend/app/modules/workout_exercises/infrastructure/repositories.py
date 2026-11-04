import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.modules.workout_exercises.infrastructure.models import WorkoutExerciseModel


class WorkoutExerciseRepository:
    """
    SQLAlchemy repository implementation for Workout Exercise database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: uuid.UUID) -> Optional[WorkoutExerciseModel]:
        """
        Retrieves a workout exercise by unique UUID ID.
        """
        stmt = select(WorkoutExerciseModel).where(WorkoutExerciseModel.id == id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_day_and_order(self, workout_day_id: uuid.UUID, order_index: int) -> Optional[WorkoutExerciseModel]:
        """
        Retrieves a workout exercise by workout_day_id and order_index position.
        """
        stmt = select(WorkoutExerciseModel).where(
            and_(
                WorkoutExerciseModel.workout_day_id == workout_day_id,
                WorkoutExerciseModel.order_index == order_index
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, workout_day_id: uuid.UUID, data: dict) -> WorkoutExerciseModel:
        """
        Persists a new workout exercise in the database.
        """
        db_exercise = WorkoutExerciseModel(workout_day_id=workout_day_id, **data)
        self.db.add(db_exercise)
        self.db.commit()
        self.db.refresh(db_exercise)
        return db_exercise

    def list_by_day(self, workout_day_id: uuid.UUID) -> List[WorkoutExerciseModel]:
        """
        Lists all workout exercises for a workout day ordered by order_index ascending.
        """
        stmt = (
            select(WorkoutExerciseModel)
            .where(WorkoutExerciseModel.workout_day_id == workout_day_id)
            .order_by(WorkoutExerciseModel.order_index.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update(self, exercise: WorkoutExerciseModel, update_data: dict) -> WorkoutExerciseModel:
        """
        Updates an existing workout exercise.
        """
        for key, value in update_data.items():
            setattr(exercise, key, value)
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def delete(self, exercise: WorkoutExerciseModel) -> None:
        """
        Deletes a workout exercise from the database.
        """
        self.db.delete(exercise)
        self.db.commit()

    def reorder(self, items: List[dict]) -> None:
        """
        Updates order_index for a batch of workout exercise records.
        """
        rows = [(self.get_by_id(item["id"]), item["order_index"]) for item in items]
        rows = [(ex, order_index) for ex, order_index in rows if ex]
        # Park every row on a unique negative index first, so swapping positions never
        # collides with uq_day_order_index halfway through the batch.
        for position, (ex, _) in enumerate(rows):
            ex.order_index = -(position + 1)
        self.db.flush()
        for ex, order_index in rows:
            ex.order_index = order_index
        self.db.commit()
