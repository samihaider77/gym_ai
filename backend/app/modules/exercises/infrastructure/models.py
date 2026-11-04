import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Table, Column, UUID, and_, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db.base import Base
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel

exercise_muscle_association = Table(
    "exercise_muscles",
    Base.metadata,
    Column("exercise_id", UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("muscle_group_id", UUID(as_uuid=True), ForeignKey("muscle_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(20), nullable=False),
)


class ExerciseModel(Base):
    """
    SQLAlchemy ORM model mapping to the 'exercises' database table.
    """
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Roman Urdu shown when the app language is Roman Urdu; falls back to English when empty.
    name_ur: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    instructions_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(50), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    force_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mechanic_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    equipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_compound: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
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

    equipment = relationship("EquipmentModel", back_populates="exercises")
    primary_muscles = relationship(
        "MuscleGroupModel",
        secondary=exercise_muscle_association,
        primaryjoin=lambda: and_(ExerciseModel.id == exercise_muscle_association.c.exercise_id, exercise_muscle_association.c.role == "primary"),
        secondaryjoin=lambda: MuscleGroupModel.id == exercise_muscle_association.c.muscle_group_id,
        viewonly=True,
        lazy="selectin",
    )
    secondary_muscles = relationship(
        "MuscleGroupModel",
        secondary=exercise_muscle_association,
        primaryjoin=lambda: and_(ExerciseModel.id == exercise_muscle_association.c.exercise_id, exercise_muscle_association.c.role == "secondary"),
        secondaryjoin=lambda: MuscleGroupModel.id == exercise_muscle_association.c.muscle_group_id,
        viewonly=True,
        lazy="selectin",
    )
    media = relationship("ExerciseMediaModel", back_populates="exercise", cascade="all, delete-orphan", lazy="selectin", order_by="ExerciseMediaModel.is_primary.desc()")
