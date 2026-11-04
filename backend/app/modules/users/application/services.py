import bcrypt
from fastapi import HTTPException, status
from app.modules.users.application.dtos import UserCreate
from app.modules.users.infrastructure.models import UserModel
from app.modules.users.infrastructure.repositories import UserRepository


class UserService:
    """
    Application Service orchestrating User use-cases.
    Encapsulates business workflow logic (email check, bcrypt password hashing).
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, user_in: UserCreate) -> UserModel:
        """
        Creates a new user in the system.
        Validates email uniqueness and hashes raw password before persistence.
        """
        # 1. Check if email is already registered
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email address already exists.",
            )

        # 2. Hash raw password securely using bcrypt
        salt = bcrypt.gensalt()
        password_bytes = user_in.password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # 3. Construct user persistence dictionary
        user_data = {
            "first_name": user_in.first_name,
            "last_name": user_in.last_name,
            "email": user_in.email.lower(),
            "password_hash": hashed_password,
            "is_active": True,
            "is_verified": False,
        }

        # 4. Save user record via repository
        return self.user_repo.create(user_data)
