import uuid
from fastapi import HTTPException, status
from app.modules.user_profile.application.dtos import UserProfileCreate, UserProfileUpdate
from app.modules.user_profile.infrastructure.models import UserProfileModel
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository


class UserProfileService:
    """
    Application Service orchestrating User Profile use-cases and business rules.
    """
    def __init__(self, profile_repo: UserProfileRepository):
        self.profile_repo = profile_repo

    def create_profile(self, user_id: uuid.UUID, profile_in: UserProfileCreate) -> UserProfileModel:
        """
        Creates a profile for the specified user.
        Enforces rule: A user can only have one profile (prevents duplicate creation).
        """
        existing_profile = self.profile_repo.get_profile_by_user_id(user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User profile already exists for this account.",
            )

        profile_data = profile_in.model_dump(exclude_unset=True)
        return self.profile_repo.create_profile(user_id, profile_data)

    def get_profile(self, user_id: uuid.UUID) -> UserProfileModel:
        """
        Retrieves the profile of the specified user.
        Raises HTTP 404 if profile does not exist yet.
        """
        profile = self.profile_repo.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )
        return profile

    def update_profile(self, user_id: uuid.UUID, profile_in: UserProfileUpdate) -> UserProfileModel:
        """
        Updates the profile of the specified user.
        Raises HTTP 404 if profile does not exist.
        """
        profile = self.profile_repo.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Create a profile first.",
            )

        update_data = profile_in.model_dump(exclude_unset=True)
        return self.profile_repo.update_profile(profile, update_data)
