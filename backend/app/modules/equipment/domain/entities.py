"""
Equipment Domain Layer

Contains pure domain entities for Equipment.
No web framework or database dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

# Domain Equipment Categories
VALID_EQUIPMENT_CATEGORIES = {"barbell", "dumbbell", "kettlebell", "machine", "cable", "bodyweight", "cardio", "accessory", "bands"}


@dataclass
class EquipmentEntity:
    """
    Pure domain representation of an Equipment entity.
    """
    id: uuid.UUID
    name: str
    slug: str
    category: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
