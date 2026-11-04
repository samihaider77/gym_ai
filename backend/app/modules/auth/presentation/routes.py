from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.application.dtos import LoginRequest, TokenResponse
from app.modules.auth.application.services import AuthService
from app.modules.users.infrastructure.repositories import UserRepository

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT tokens",
    description="Validates email and password, returning JWT access & refresh tokens along with user profile info."
)
def login_endpoint(
    login_in: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for user login.
    """
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    return auth_service.login(login_in)
