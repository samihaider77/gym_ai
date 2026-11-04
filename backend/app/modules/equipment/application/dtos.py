from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class EquipmentCreate(BaseModel):
    """
    Input DTO for creating a new Equipment item.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Equipment name (must be unique)")
    category: str = Field(..., max_length=50, description="Equipment category (e.g. barbell, dumbbell, machine, cable, bodyweight)")
    description: Optional[str] = Field(None, description="Description of equipment specifications and usage")


class EquipmentUpdate(BaseModel):
    """
    Input DTO for updating an existing Equipment item.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Equipment name")
    category: Optional[str] = Field(None, max_length=50, description="Equipment category")
    description: Optional[str] = Field(None, description="Description of equipment")
    is_active: Optional[bool] = Field(None, description="Active status")


class EquipmentResponse(BaseModel):
    """
    Output DTO for Equipment details.
    """
    id: uuid.UUID
    name: str
    slug: str
    category: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentListResponse(BaseModel):
    """
    Output DTO for paginated Equipment list responses.
    """
    items: List[EquipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
