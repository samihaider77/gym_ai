import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.muscle_groups.application.dtos import (
    MuscleGroupCreate,
    MuscleGroupUpdate,
    MuscleGroupResponse,
    MuscleGroupListResponse,
)
from app.modules.muscle_groups.application.services import MuscleGroupService
from app.modules.muscle_groups.infrastructure.repositories import MuscleGroupRepository

router = APIRouter()


@router.post(
    "",
    response_model=MuscleGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new muscle group",
    description="Registers a new muscle group with an automatically generated URL slug."
)
def create_muscle_group_endpoint(
    muscle_group_in: MuscleGroupCreate,
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for creating a muscle group.
    """
    repo = MuscleGroupRepository(db)
    service = MuscleGroupService(repo)
    return service.create_muscle_group(muscle_group_in)


@router.get(
    "",
    response_model=MuscleGroupListResponse,
    status_code=status.HTTP_200_OK,
    summary="List muscle groups with pagination, filtering, and search",
    description="Retrieves a paginated list of muscle groups. Supports filtering by body_region, is_active, and name search."
)
def list_muscle_groups_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    body_region: Optional[str] = Query(None, description="Filter by body region (e.g. chest, back, legs, arms, shoulders, core)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by muscle group name"),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for paginated muscle groups listing.
    """
    repo = MuscleGroupRepository(db)
    service = MuscleGroupService(repo)
    return service.list_muscle_groups(
        page=page,
        page_size=page_size,
        body_region=body_region,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/{id}",
    response_model=MuscleGroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get muscle group by ID",
    description="Retrieves details for a specific muscle group by its UUID."
)
def get_muscle_group_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for retrieving a muscle group by ID.
    """
    repo = MuscleGroupRepository(db)
    service = MuscleGroupService(repo)
    return service.get_muscle_group(id)


@router.put(
    "/{id}",
    response_model=MuscleGroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Update muscle group by ID",
    description="Updates muscle group attributes. Automatically updates URL slug if the name is changed."
)
def update_muscle_group_endpoint(
    id: uuid.UUID,
    muscle_group_in: MuscleGroupUpdate,
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for muscle group modification.
    """
    repo = MuscleGroupRepository(db)
    service = MuscleGroupService(repo)
    return service.update_muscle_group(id, muscle_group_in)


@router.delete(
    "/{id}",
    response_model=MuscleGroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete muscle group by ID",
    description="Soft deletes a muscle group by setting is_active = false."
)
def delete_muscle_group_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP DELETE handler for soft deleting a muscle group.
    """
    repo = MuscleGroupRepository(db)
    service = MuscleGroupService(repo)
    return service.soft_delete_muscle_group(id)
