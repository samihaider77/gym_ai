"""
Workout Days Domain Layer

Contains pure domain entities for Workout Days.
No framework dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class WorkoutDayEntity:
    """
    Pure domain representation of a Workout Day entity.
    """
    id: uuid.UUID
    workout_plan_id: uuid.UUID
    day_number: int
    title: str
    notes: Optional[str]
    estimated_duration_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime
