from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class WorkoutDayCreate(BaseModel):
    """
    Input DTO for creating a new Workout Day.
    """
    day_number: int = Field(..., ge=1, description="Day number inside the plan (must start at 1 and be unique)")
    title: str = Field(..., min_length=1, max_length=150, description="Title of the workout day (e.g. Push Day)")
    notes: Optional[str] = Field(None, description="Optional workout instructions or notes")
    estimated_duration_minutes: Optional[int] = Field(60, ge=1, le=360, description="Estimated duration in minutes")


class WorkoutDayUpdate(BaseModel):
    """
    Input DTO for updating an existing Workout Day.
    """
    day_number: Optional[int] = Field(None, ge=1, description="Day number inside the plan")
    title: Optional[str] = Field(None, min_length=1, max_length=150, description="Title of the workout day")
    notes: Optional[str] = Field(None, description="Optional workout notes")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=360, description="Estimated duration in minutes")


class WorkoutDayResponse(BaseModel):
    """
    Output DTO for Workout Day details.
    """
    id: uuid.UUID
    workout_plan_id: uuid.UUID
    day_number: int
    title: str
    notes: Optional[str]
    estimated_duration_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutDayListResponse(BaseModel):
    """
    Output DTO for listing Workout Days in a plan.
    """
    items: List[WorkoutDayResponse]
    total: int
