"""
Workout Sessions Domain Layer

Contains pure domain entities and status constants for Workout Sessions.
No framework dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

# Domain Session Status Values
STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_CANCELLED = "CANCELLED"

VALID_SESSION_STATUSES = {
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
}


@dataclass
class WorkoutSessionEntity:
    """
    Pure domain representation of an active or historical Workout Session entity.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    workout_plan_id: uuid.UUID
    workout_day_id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: int
    calories_burned: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
