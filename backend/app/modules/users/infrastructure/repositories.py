from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.users.infrastructure.models import UserModel


class UserRepository:
    """
    SQLAlchemy repository implementation for User database operations.
    Handles data access logic for the 'users' table.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Fetches a user record by email address.
        """
        stmt = select(UserModel).where(UserModel.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user_data: dict) -> UserModel:
        """
        Persists a new user record into the database.
        """
        db_user = UserModel(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
