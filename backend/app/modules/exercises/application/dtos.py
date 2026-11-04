from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class ExerciseCreate(BaseModel):
    """
    Input DTO for creating a new Exercise.
    """
    name: str = Field(..., min_length=2, max_length=150, description="Exercise name (must be unique)")
    description: Optional[str] = Field(None, description="Detailed description of the exercise")
    instructions: Optional[str] = Field(None, description="Step-by-step performance instructions")
    difficulty_level: str = Field(..., description="Difficulty level (beginner, intermediate, advanced)")
    exercise_type: str = Field(..., description="Category (strength, cardio, flexibility, calisthenics)")
    force_type: Optional[str] = Field(None, description="Force movement type (push, pull, static)")
    mechanic_type: Optional[str] = Field(None, description="Mechanic classification (compound, isolation)")
    equipment_id: Optional[uuid.UUID] = Field(None, description="Optional equipment FK reference")
    is_compound: bool = Field(True, description="Whether the exercise engages multiple joints")
    primary_muscle_ids: List[uuid.UUID] = Field(default_factory=list)
    secondary_muscle_ids: List[uuid.UUID] = Field(default_factory=list)


class ExerciseUpdate(BaseModel):
    """
    Input DTO for updating an existing Exercise.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=150, description="Exercise name")
    description: Optional[str] = Field(None, description="Detailed description of the exercise")
    instructions: Optional[str] = Field(None, description="Step-by-step performance instructions")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    exercise_type: Optional[str] = Field(None, description="Category")
    force_type: Optional[str] = Field(None, description="Force movement type")
    mechanic_type: Optional[str] = Field(None, description="Mechanic classification")
    equipment_id: Optional[uuid.UUID] = Field(None, description="Optional equipment FK reference")
    is_compound: Optional[bool] = Field(None, description="Whether the exercise engages multiple joints")
    is_active: Optional[bool] = Field(None, description="Active status")
    primary_muscle_ids: Optional[List[uuid.UUID]] = None
    secondary_muscle_ids: Optional[List[uuid.UUID]] = None


class EquipmentSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class MuscleSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    body_region: str

    model_config = ConfigDict(from_attributes=True)

class ExerciseMediaResponse(BaseModel):
    id: uuid.UUID
    media_type: str
    media_url: str
    thumbnail_url: Optional[str]
    poster_url: Optional[str]
    provider: Optional[str]
    license: Optional[str]
    attribution: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    duration_ms: Optional[int]
    camera_angle: Optional[str]
    format: Optional[str]
    version: int
    status: str
    is_primary: bool
    model_config = ConfigDict(from_attributes=True)


class ExerciseResponse(BaseModel):
    """
    Output DTO for Exercise details.
    """
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    instructions: Optional[str]
    name_ur: Optional[str] = None
    instructions_ur: Optional[str] = None
    difficulty_level: str
    exercise_type: str
    force_type: Optional[str]
    mechanic_type: Optional[str]
    equipment_id: Optional[uuid.UUID]
    is_compound: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    equipment: Optional[EquipmentSummary] = None
    primary_muscles: List[MuscleSummary] = Field(default_factory=list)
    secondary_muscles: List[MuscleSummary] = Field(default_factory=list)
    media: List[ExerciseMediaResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExerciseListResponse(BaseModel):
    """
    Output DTO for paginated exercise list responses.
    """
    items: List[ExerciseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FacetCount(BaseModel):
    """
    One filter option (an ID or a plain value) and how many exercises it would show.
    """
    value: str
    count: int


class ExerciseFacetsResponse(BaseModel):
    """
    Output DTO for the filter options that still return exercises under the current filters.
    """
    muscles: List[FacetCount]
    equipment: List[FacetCount]
    types: List[FacetCount]
    levels: List[FacetCount]
