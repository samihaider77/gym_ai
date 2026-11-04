"""
User Profile Domain Layer

Contains pure domain entities for User Profile.
No web framework or database dependencies belong here.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class UserProfileEntity:
    """
    Pure domain representation of a User Profile entity.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: Optional[date]
    gender: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    fitness_goal: Optional[str]
    activity_level: Optional[str]
    experience_level: Optional[str]
    profile_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
