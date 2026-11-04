"""
Body Progress Domain Layer

Contains pure domain entities for Body Progress.
No framework dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class BodyProgressEntity:
    """
    Pure domain representation of a Body Progress tracking record.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    weight_kg: float
    body_fat_percentage: Optional[float]
    bmi: Optional[float]
    chest_cm: Optional[float]
    waist_cm: Optional[float]
    hips_cm: Optional[float]
    left_arm_cm: Optional[float]
    right_arm_cm: Optional[float]
    left_thigh_cm: Optional[float]
    right_thigh_cm: Optional[float]
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime
