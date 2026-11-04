import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db.base import Base


class WorkoutExerciseModel(Base):
    """
    SQLAlchemy ORM model mapping to the 'workout_exercises' database table.
    Enforces a UniqueConstraint on (workout_day_id, order_index).
    """
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_day_id", "order_index", name="uq_day_order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    workout_day_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    target_weight: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, default=60, nullable=True)
    tempo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    workout_day = relationship("WorkoutDayModel", backref="workout_exercises")
    exercise = relationship("ExerciseModel", backref="workout_exercises")
