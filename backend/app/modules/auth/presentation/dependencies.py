import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.core.security import decode_token
from app.modules.users.infrastructure.models import UserModel
from app.modules.users.infrastructure.repositories import UserRepository

# Configure HTTP Bearer security scheme for OpenAPI and token extraction
http_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Reusable FastAPI dependency that decodes the Bearer JWT token,
    validates token type and expiry, and fetches the currently authenticated active user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decode token from HTTPBearer credentials
    token = credentials.credentials
    payload = decode_token(token)

    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # 2. Fetch user record from database
    user_repo = UserRepository(db)
    user = user_repo.db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user

