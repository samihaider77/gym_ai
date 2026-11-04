from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.users.application.dtos import UserCreate, UserResponse
from app.modules.users.application.services import UserService
from app.modules.users.infrastructure.repositories import UserRepository

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Validates user input, checks email uniqueness, hashes password, and creates a new user profile."
)
def create_user_endpoint(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for user creation.
    """
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    return user_service.create_user(user_in)
