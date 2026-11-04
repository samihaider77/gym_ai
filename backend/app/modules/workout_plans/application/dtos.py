from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class WorkoutPlanCreate(BaseModel):
    """
    Input DTO for creating a new Workout Plan.
    """
    name: str = Field(..., min_length=2, max_length=150, description="Plan name (must be unique per user)")
    description: Optional[str] = Field(None, description="Detailed plan description")
    goal: str = Field(..., max_length=100, description="Primary fitness goal (e.g. muscle_gain, fat_loss, strength)")
    difficulty: str = Field(..., max_length=50, description="Target difficulty level (beginner, intermediate, advanced)")
    duration_weeks: int = Field(4, ge=1, le=52, description="Target duration in weeks")
    days_per_week: int = Field(4, ge=1, le=7, description="Number of workout days per week")
    is_template: bool = Field(False, description="Whether this plan is a reusable template")


class WorkoutPlanUpdate(BaseModel):
    """
    Input DTO for updating an existing Workout Plan.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=150, description="Plan name")
    description: Optional[str] = Field(None, description="Detailed plan description")
    goal: Optional[str] = Field(None, max_length=100, description="Primary fitness goal")
    difficulty: Optional[str] = Field(None, max_length=50, description="Target difficulty level")
    duration_weeks: Optional[int] = Field(None, ge=1, le=52, description="Target duration in weeks")
    days_per_week: Optional[int] = Field(None, ge=1, le=7, description="Number of workout days per week")
    is_template: Optional[bool] = Field(None, description="Whether this plan is a reusable template")
    is_active: Optional[bool] = Field(None, description="Active status")


class WorkoutPlanResponse(BaseModel):
    """
    Output DTO for Workout Plan details.
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

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanListResponse(BaseModel):
    """
    Output DTO for paginated Workout Plan list responses.
    """
    items: List[WorkoutPlanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
