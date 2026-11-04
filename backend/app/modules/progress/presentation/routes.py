import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.progress.application.dtos import (
    BodyProgressCreate,
    BodyProgressUpdate,
    BodyProgressResponse,
    BodyProgressListResponse,
)
from app.modules.progress.application.services import BodyProgressService
from app.modules.progress.infrastructure.repositories import BodyProgressRepository
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> BodyProgressService:
    progress_repo = BodyProgressRepository(db)
    profile_repo = UserProfileRepository(db)
    return BodyProgressService(progress_repo, profile_repo)


@router.post(
    "",
    response_model=BodyProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a body progress measurement entry",
    description="Logs body weight, body fat percentage, and body circumferences for the authenticated user. Automatically computes BMI if user profile height exists."
)
def create_progress_endpoint(
    progress_in: BodyProgressCreate,
    current_user: UserModel = Depends(get_current_user),
    service: BodyProgressService = Depends(get_service)
):
    """
    HTTP POST handler for body progress entry creation.
    """
    return service.create_progress(current_user.id, progress_in)


@router.get(
    "",
    response_model=BodyProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest body progress measurement entry",
    description="Retrieves the most recent body progress record for the authenticated user."
)
def get_latest_progress_endpoint(
    current_user: UserModel = Depends(get_current_user),
    service: BodyProgressService = Depends(get_service)
):
    """
    HTTP GET handler for fetching the latest body progress entry.
    """
    return service.get_latest_progress(current_user.id)


@router.get(
    "/history",
    response_model=BodyProgressListResponse,
    status_code=status.HTTP_200_OK,
    summary="List body progress measurement history",
    description="Retrieves a paginated list of historical body progress entries for the authenticated user."
)
def list_progress_history_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserModel = Depends(get_current_user),
    service: BodyProgressService = Depends(get_service)
):
    """
    HTTP GET handler for body progress history listing.
    """
    return service.list_progress_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/{id}",
    response_model=BodyProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Update body progress entry by ID",
    description="Updates measurements in an existing body progress entry owned by the authenticated user."
)
def update_progress_endpoint(
    id: uuid.UUID,
    progress_in: BodyProgressUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: BodyProgressService = Depends(get_service)
):
    """
    HTTP PUT handler for modifying a body progress entry.
    """
    return service.update_progress(id, current_user.id, progress_in)
