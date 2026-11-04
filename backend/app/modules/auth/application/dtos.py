from pydantic import BaseModel, EmailStr, Field
from app.modules.users.application.dtos import UserResponse


class LoginRequest(BaseModel):
    """
    Input Data Transfer Object (DTO) for login requests.
    """
    email: EmailStr = Field(..., description="User's registered email address")
    password: str = Field(..., min_length=1, description="User's raw password")


class TokenResponse(BaseModel):
    """
    Output Data Transfer Object (DTO) returned upon successful authentication.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
