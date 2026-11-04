from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class WorkoutLogCreate(BaseModel):
    """
    Input DTO for creating a new Workout Log entry for a completed set.
    """
    workout_exercise_id: uuid.UUID = Field(..., description="ID of the workout exercise being logged")
    set_number: int = Field(..., ge=1, description="Set number position (must be positive)")
    completed_reps: int = Field(..., ge=0, description="Completed reps count (cannot be negative)")
    completed_weight: float = Field(..., ge=0.0, description="Completed weight in kg (cannot be negative)")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Optional time duration in seconds")
    rest_seconds: Optional[int] = Field(None, ge=0, description="Optional rest duration in seconds")
    is_completed: bool = Field(True, description="Whether the set was completed successfully")
    notes: Optional[str] = Field(None, description="Optional log notes")


class WorkoutLogUpdate(BaseModel):
    """
    Input DTO for updating an existing Workout Log entry.
    """
    set_number: Optional[int] = Field(None, ge=1, description="Set number position")
    completed_reps: Optional[int] = Field(None, ge=0, description="Completed reps count")
    completed_weight: Optional[float] = Field(None, ge=0.0, description="Completed weight in kg")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Optional duration in seconds")
    rest_seconds: Optional[int] = Field(None, ge=0, description="Optional rest duration in seconds")
    is_completed: Optional[bool] = Field(None, description="Completion status")
    notes: Optional[str] = Field(None, description="Optional log notes")


class WorkoutLogResponse(BaseModel):
    """
    Output DTO for Workout Log details.
    """
    id: uuid.UUID
    workout_session_id: uuid.UUID
    workout_exercise_id: uuid.UUID
    set_number: int
    completed_reps: int
    completed_weight: float
    duration_seconds: Optional[int]
    rest_seconds: Optional[int]
    is_completed: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutLogListResponse(BaseModel):
    """
    Output DTO for listing Workout Logs in a session.
    """
    items: List[WorkoutLogResponse]
    total: int
