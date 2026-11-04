"""
Workout Logs Domain Layer

Contains pure domain entities for Workout Logs.
No framework dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class WorkoutLogEntity:
    """
    Pure domain representation of a completed or logged exercise set inside a Workout Session.
    """
    id: uuid.UUID
    workout_session_id: uuid.UUID
    workout_exercise_id: uuid.UUID
    set_number: int
    completed_reps: int
    completed_weight: float
    duration_seconds: Optional[int]
    rest_seconds: Optional[int]
    is_completed: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
