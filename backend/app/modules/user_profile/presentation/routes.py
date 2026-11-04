from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.user_profile.application.dtos import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)
from app.modules.user_profile.application.services import UserProfileService
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository

router = APIRouter()


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create profile for authenticated user",
    description="Creates a fitness and demographic profile for the currently authenticated user."
)
def create_profile_endpoint(
    profile_in: UserProfileCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for user profile creation.
    """
    repo = UserProfileRepository(db)
    service = UserProfileService(repo)
    return service.create_profile(current_user.id, profile_in)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile of authenticated user",
    description="Retrieves the fitness profile of the currently authenticated user."
)
def get_my_profile_endpoint(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for fetching current user's profile.
    """
    repo = UserProfileRepository(db)
    service = UserProfileService(repo)
    return service.get_profile(current_user.id)


@router.put(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update profile for authenticated user",
    description="Updates existing profile attributes for the currently authenticated user."
)
def update_profile_endpoint(
    profile_in: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for profile modification.
    """
    repo = UserProfileRepository(db)
    service = UserProfileService(repo)
    return service.update_profile(current_user.id, profile_in)
