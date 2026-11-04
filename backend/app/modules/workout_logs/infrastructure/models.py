import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db.base import Base


class WorkoutLogModel(Base):
    """
    SQLAlchemy ORM model mapping to the 'workout_logs' database table.
    Enforces a UniqueConstraint on (workout_session_id, workout_exercise_id, set_number).
    """
    __tablename__ = "workout_logs"
    __table_args__ = (
        UniqueConstraint("workout_session_id", "workout_exercise_id", "set_number", name="uq_session_exercise_set"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_weight: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    workout_session = relationship("WorkoutSessionModel", backref="workout_logs")
    workout_exercise = relationship("WorkoutExerciseModel", backref="workout_logs")
