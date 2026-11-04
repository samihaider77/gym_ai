from datetime import date, datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class UserProfileCreate(BaseModel):
    """
    Input DTO for creating a User Profile.
    """
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=50, description="Gender identity")
    height_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=0.0, le=500.0, description="Weight in kilograms")
    fitness_goal: Optional[str] = Field(None, max_length=100, description="Primary fitness goal")
    activity_level: Optional[str] = Field(None, max_length=100, description="Daily activity level")
    experience_level: Optional[str] = Field(None, max_length=100, description="Workout experience level")
    profile_image_url: Optional[str] = Field(None, max_length=500, description="Profile avatar image URL")


class UserProfileUpdate(BaseModel):
    """
    Input DTO for updating an existing User Profile.
    """
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=50, description="Gender identity")
    height_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=0.0, le=500.0, description="Weight in kilograms")
    fitness_goal: Optional[str] = Field(None, max_length=100, description="Primary fitness goal")
    activity_level: Optional[str] = Field(None, max_length=100, description="Daily activity level")
    experience_level: Optional[str] = Field(None, max_length=100, description="Workout experience level")
    profile_image_url: Optional[str] = Field(None, max_length=500, description="Profile avatar image URL")


class UserProfileResponse(BaseModel):
    """
    Output DTO for User Profile responses.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: Optional[date]
    gender: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    fitness_goal: Optional[str]
    activity_level: Optional[str]
    experience_level: Optional[str]
    profile_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
