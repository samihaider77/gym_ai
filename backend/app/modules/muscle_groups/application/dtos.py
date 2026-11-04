from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class MuscleGroupCreate(BaseModel):
    """
    Input DTO for creating a new Muscle Group.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Muscle group name (must be unique)")
    description: Optional[str] = Field(None, description="Description of muscle group location & function")
    body_region: str = Field(..., max_length=50, description="Body region (e.g. chest, back, legs, arms, shoulders, core)")


class MuscleGroupUpdate(BaseModel):
    """
    Input DTO for updating an existing Muscle Group.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Muscle group name")
    description: Optional[str] = Field(None, description="Description of muscle group")
    body_region: Optional[str] = Field(None, max_length=50, description="Body region")
    is_active: Optional[bool] = Field(None, description="Active status")


class MuscleGroupResponse(BaseModel):
    """
    Output DTO for Muscle Group details.
    """
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    body_region: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MuscleGroupListResponse(BaseModel):
    """
    Output DTO for paginated Muscle Group list responses.
    """
    items: List[MuscleGroupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
