"""
Workout Plans Domain Layer

Contains pure domain entities and business domain constants for Workout Plans.
No web framework or ORM dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

VALID_WORKOUT_GOALS = {"muscle_gain", "fat_loss", "strength", "endurance", "general_fitness", "rehab"}
VALID_WORKOUT_DIFFICULTIES = {"beginner", "intermediate", "advanced"}


@dataclass
class WorkoutPlanEntity:
    """
    Pure domain representation of a Workout Plan entity.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    goal: str
    difficulty: str
    duration_weeks: int
    days_per_week: int
    is_template: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
