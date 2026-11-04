"""
Workout Exercises Domain Layer

Contains pure domain entities for Workout Exercises.
No framework dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class WorkoutExerciseEntity:
    """
    Pure domain representation of an Exercise configured inside a Workout Day.
    """
    id: uuid.UUID
    workout_day_id: uuid.UUID
    exercise_id: uuid.UUID
    order_index: int
    sets: int
    reps: int
    target_weight: Optional[float]
    rest_seconds: Optional[int]
    tempo: Optional[str]
    duration_seconds: Optional[int]
    distance: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
