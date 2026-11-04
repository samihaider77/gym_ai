from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """
    Input Data Transfer Object (DTO) for user creation / registration.
    """
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: EmailStr = Field(..., description="User's unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's raw password")


class UserResponse(BaseModel):
    """
    Output Data Transfer Object (DTO) for user responses.
    Excludes sensitive fields like password_hash.
    """
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
