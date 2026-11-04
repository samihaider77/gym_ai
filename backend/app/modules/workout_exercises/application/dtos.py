from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class WorkoutExerciseCreate(BaseModel):
    """
    Input DTO for adding an Exercise to a Workout Day.
    """
    exercise_id: uuid.UUID = Field(..., description="ID of the target exercise in exercise library")
    order_index: int = Field(..., ge=0, description="Order position inside the workout day")
    sets: int = Field(3, ge=1, description="Number of target sets")
    reps: int = Field(10, ge=1, description="Number of target repetitions per set")
    target_weight: Optional[float] = Field(0.0, ge=0.0, description="Target weight in kg")
    rest_seconds: Optional[int] = Field(60, ge=0, description="Rest period in seconds between sets")
    tempo: Optional[str] = Field(None, max_length=50, description="Movement tempo e.g., '3-0-1-0'")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Optional timed duration in seconds")
    distance: Optional[float] = Field(None, ge=0.0, description="Optional target distance in meters/km")
    notes: Optional[str] = Field(None, description="Optional exercise execution notes")


class WorkoutExerciseUpdate(BaseModel):
    """
    Input DTO for updating an existing Workout Exercise configuration.
    """
    exercise_id: Optional[uuid.UUID] = Field(None, description="ID of the target exercise")
    order_index: Optional[int] = Field(None, ge=0, description="Order position inside the workout day")
    sets: Optional[int] = Field(None, ge=1, description="Number of target sets")
    reps: Optional[int] = Field(None, ge=1, description="Number of target repetitions per set")
    target_weight: Optional[float] = Field(None, ge=0.0, description="Target weight in kg")
    rest_seconds: Optional[int] = Field(None, ge=0, description="Rest period in seconds between sets")
    tempo: Optional[str] = Field(None, max_length=50, description="Movement tempo")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Optional timed duration in seconds")
    distance: Optional[float] = Field(None, ge=0.0, description="Optional target distance")
    notes: Optional[str] = Field(None, description="Optional notes")


class ReorderExerciseItem(BaseModel):
    """
    Item payload for batch exercise reordering.
    """
    id: uuid.UUID = Field(..., description="ID of the workout exercise")
    order_index: int = Field(..., ge=0, description="New order index position")


class ReorderExercisesRequest(BaseModel):
    """
    Payload for batch exercise reordering within a day.
    """
    items: List[ReorderExerciseItem] = Field(..., min_length=1, description="List of exercises with new order indices")


class WorkoutExerciseResponse(BaseModel):
    """
    Output DTO for Workout Exercise details.
    """
    id: uuid.UUID
    workout_day_id: uuid.UUID
    exercise_id: uuid.UUID
    order_index: int
    sets: int
    reps: int
    target_weight: Optional[float]
    rest_seconds: Optional[int]
    tempo: Optional[str]
    duration_seconds: Optional[int]
    distance: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutExerciseListResponse(BaseModel):
    """
    Output DTO for listing Workout Exercises in a day.
    """
    items: List[WorkoutExerciseResponse]
    total: int
