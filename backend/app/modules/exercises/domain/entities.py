"""
Exercise Domain Layer

Contains pure domain entities and business validation constants for Exercises.
No framework imports (FastAPI, SQLAlchemy, Pydantic) belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

# Domain Validation Constants
VALID_DIFFICULTY_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_EXERCISE_TYPES = {"strength", "cardio", "flexibility", "calisthenics", "plyometrics", "stretching"}
VALID_FORCE_TYPES = {"push", "pull", "static", "dynamic"}
VALID_MECHANIC_TYPES = {"compound", "isolation"}


@dataclass
class ExerciseEntity:
    """
    Pure domain representation of an Exercise entity.
    """
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    instructions: Optional[str]
    difficulty_level: str
    exercise_type: str
    force_type: Optional[str]
    mechanic_type: Optional[str]
    equipment_id: Optional[uuid.UUID]
    is_compound: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
