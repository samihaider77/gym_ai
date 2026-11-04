import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db.base import Base


class BodyProgressModel(Base):
    """
    SQLAlchemy ORM model mapping to the 'body_progress' database table.
    """
    __tablename__ = "body_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    body_fat_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    left_arm_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    right_arm_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    left_thigh_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    right_thigh_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user = relationship("UserModel", backref="progress_entries")
