import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.user_profile.infrastructure.models import UserProfileModel


class UserProfileRepository:
    """
    SQLAlchemy repository implementation for User Profile data access.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_profile_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfileModel]:
        """
        Retrieves a user profile by associated user_id.
        """
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_profile(self, user_id: uuid.UUID, profile_data: dict) -> UserProfileModel:
        """
        Persists a new user profile record in the database.
        """
        db_profile = UserProfileModel(user_id=user_id, **profile_data)
        self.db.add(db_profile)
        self.db.commit()
        self.db.refresh(db_profile)
        return db_profile

    def update_profile(self, profile: UserProfileModel, update_data: dict) -> UserProfileModel:
        """
        Updates an existing user profile record.
        """
        for key, value in update_data.items():
            setattr(profile, key, value)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
