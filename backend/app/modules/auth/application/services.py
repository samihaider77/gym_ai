from fastapi import HTTPException, status
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.modules.auth.application.dtos import LoginRequest, TokenResponse
from app.modules.users.application.dtos import UserResponse
from app.modules.users.infrastructure.repositories import UserRepository


class AuthService:
    """
    Application Service orchestrating User Authentication use-cases.
    Handles credential validation and token issuance.
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def login(self, login_in: LoginRequest) -> TokenResponse:
        """
        Authenticates user credentials and issues JWT access and refresh tokens.
        """
        # 1. Fetch user by email
        user = self.user_repo.get_by_email(login_in.email)
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email address or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Check active account status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive.",
            )

        # 3. Generate access and refresh tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        # 4. Construct response DTO
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
