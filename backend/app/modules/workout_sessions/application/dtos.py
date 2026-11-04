from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class WorkoutSessionStart(BaseModel):
    """
    Input DTO for starting a new Workout Session.
    """
    workout_plan_id: uuid.UUID = Field(..., description="ID of the parent workout plan")
    workout_day_id: uuid.UUID = Field(..., description="ID of the workout day being performed")
    notes: Optional[str] = Field(None, description="Optional initial session notes")


class WorkoutSessionFinish(BaseModel):
    """
    Input DTO for completing an active Workout Session.
    """
    calories_burned: Optional[int] = Field(None, ge=0, description="Optional total calories burned")
    notes: Optional[str] = Field(None, description="Optional post-workout session notes")


class WorkoutSessionCancel(BaseModel):
    """
    Input DTO for cancelling an active Workout Session.
    """
    notes: Optional[str] = Field(None, description="Optional cancellation notes or reason")


class WorkoutSessionResponse(BaseModel):
    """
    Output DTO for Workout Session details.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    workout_plan_id: uuid.UUID
    workout_day_id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: int
    calories_burned: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutSessionListResponse(BaseModel):
    """
    Output DTO for paginated Workout Session list responses.
    """
    items: List[WorkoutSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
