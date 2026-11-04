from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class BodyProgressCreate(BaseModel):
    """
    Input DTO for logging a new Body Progress measurement entry.
    """
    weight_kg: float = Field(..., ge=0.0, le=500.0, description="Body weight in kilograms")
    body_fat_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Body fat percentage")
    chest_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Chest circumference in cm")
    waist_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Waist circumference in cm")
    hips_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Hips circumference in cm")
    left_arm_cm: Optional[float] = Field(None, ge=0.0, le=100.0, description="Left arm circumference in cm")
    right_arm_cm: Optional[float] = Field(None, ge=0.0, le=100.0, description="Right arm circumference in cm")
    left_thigh_cm: Optional[float] = Field(None, ge=0.0, le=200.0, description="Left thigh circumference in cm")
    right_thigh_cm: Optional[float] = Field(None, ge=0.0, le=200.0, description="Right thigh circumference in cm")
    notes: Optional[str] = Field(None, description="Optional progress entry notes")
    recorded_at: Optional[datetime] = Field(None, description="Date & time when measurements were taken (defaults to current time)")


class BodyProgressUpdate(BaseModel):
    """
    Input DTO for updating an existing Body Progress entry.
    """
    weight_kg: Optional[float] = Field(None, ge=0.0, le=500.0, description="Body weight in kg")
    body_fat_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Body fat percentage")
    chest_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Chest circumference in cm")
    waist_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Waist circumference in cm")
    hips_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Hips circumference in cm")
    left_arm_cm: Optional[float] = Field(None, ge=0.0, le=100.0, description="Left arm circumference in cm")
    right_arm_cm: Optional[float] = Field(None, ge=0.0, le=100.0, description="Right arm circumference in cm")
    left_thigh_cm: Optional[float] = Field(None, ge=0.0, le=200.0, description="Left thigh circumference in cm")
    right_thigh_cm: Optional[float] = Field(None, ge=0.0, le=200.0, description="Right thigh circumference in cm")
    notes: Optional[str] = Field(None, description="Optional notes")
    recorded_at: Optional[datetime] = Field(None, description="Recorded date & time")


class BodyProgressResponse(BaseModel):
    """
    Output DTO for Body Progress details including computed BMI.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    weight_kg: float
    body_fat_percentage: Optional[float]
    bmi: Optional[float]
    chest_cm: Optional[float]
    waist_cm: Optional[float]
    hips_cm: Optional[float]
    left_arm_cm: Optional[float]
    right_arm_cm: Optional[float]
    left_thigh_cm: Optional[float]
    right_thigh_cm: Optional[float]
    notes: Optional[str]
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BodyProgressListResponse(BaseModel):
    """
    Output DTO for paginated Body Progress history responses.
    """
    items: List[BodyProgressResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
