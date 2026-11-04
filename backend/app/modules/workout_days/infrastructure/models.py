import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db.base import Base


class WorkoutDayModel(Base):
    """
    SQLAlchemy ORM model mapping to the 'workout_days' database table.
    Enforces a One-to-Many relationship with WorkoutPlanModel and UniqueConstraint on (workout_plan_id, day_number).
    """
    __tablename__ = "workout_days"
    __table_args__ = (
        UniqueConstraint("workout_plan_id", "day_number", name="uq_plan_day_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=60, nullable=True)
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

    # Relationship back to WorkoutPlanModel
    workout_plan = relationship("WorkoutPlanModel", backref="days")
