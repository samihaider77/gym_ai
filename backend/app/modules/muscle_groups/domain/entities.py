"""
Muscle Groups Domain Layer

Contains pure domain entities for Muscle Groups.
No web framework or database dependencies belong here.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

# Domain Body Region Constants
VALID_BODY_REGIONS = {"chest", "back", "arms", "shoulders", "legs", "core", "full_body"}


@dataclass
class MuscleGroupEntity:
    """
    Pure domain representation of a Muscle Group entity.
    """
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    body_region: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
