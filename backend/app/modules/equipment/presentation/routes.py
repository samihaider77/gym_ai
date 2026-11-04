import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.equipment.application.dtos import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
)
from app.modules.equipment.application.services import EquipmentService
from app.modules.equipment.infrastructure.repositories import EquipmentRepository

router = APIRouter()


@router.post(
    "",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new equipment item",
    description="Registers a new equipment item with an automatically generated URL slug."
)
def create_equipment_endpoint(
    equipment_in: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for creating an equipment item.
    """
    repo = EquipmentRepository(db)
    service = EquipmentService(repo)
    return service.create_equipment(equipment_in)


@router.get(
    "",
    response_model=EquipmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List equipment with pagination, filtering, and search",
    description="Retrieves a paginated list of equipment items. Supports filtering by category, is_active, and name search."
)
def list_equipment_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. barbell, dumbbell, machine, cable, bodyweight)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by equipment name"),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for paginated equipment listing.
    """
    repo = EquipmentRepository(db)
    service = EquipmentService(repo)
    return service.list_equipment(
        page=page,
        page_size=page_size,
        category=category,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/{id}",
    response_model=EquipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get equipment item by ID",
    description="Retrieves details for a specific equipment item by its UUID."
)
def get_equipment_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for retrieving an equipment item by ID.
    """
    repo = EquipmentRepository(db)
    service = EquipmentService(repo)
    return service.get_equipment(id)


@router.put(
    "/{id}",
    response_model=EquipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update equipment item by ID",
    description="Updates equipment attributes. Automatically updates URL slug if the name is changed."
)
def update_equipment_endpoint(
    id: uuid.UUID,
    equipment_in: EquipmentUpdate,
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for equipment modification.
    """
    repo = EquipmentRepository(db)
    service = EquipmentService(repo)
    return service.update_equipment(id, equipment_in)


@router.delete(
    "/{id}",
    response_model=EquipmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete equipment item by ID",
    description="Soft deletes an equipment item by setting is_active = false."
)
def delete_equipment_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP DELETE handler for soft deleting an equipment item.
    """
    repo = EquipmentRepository(db)
    service = EquipmentService(repo)
    return service.soft_delete_equipment(id)
