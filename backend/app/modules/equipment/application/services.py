import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.core.utils.slug import generate_slug
from app.modules.equipment.application.dtos import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
)
from app.modules.equipment.infrastructure.models import EquipmentModel
from app.modules.equipment.infrastructure.repositories import EquipmentRepository


class EquipmentService:
    """
    Application Service orchestrating Equipment use-cases and business rules.
    """
    def __init__(self, repo: EquipmentRepository):
        self.repo = repo

    def create_equipment(self, equipment_in: EquipmentCreate) -> EquipmentModel:
        """
        Creates a new equipment item.
        Validates name uniqueness and generates URL slug automatically using shared utility.
        """
        # 1. Check duplicate name
        existing = self.repo.get_by_name(equipment_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment with name '{equipment_in.name}' already exists.",
            )

        # 2. Generate slug and prepare data
        slug = generate_slug(equipment_in.name)
        data = equipment_in.model_dump()
        data["slug"] = slug
        data["category"] = equipment_in.category.lower()
        data["is_active"] = True

        return self.repo.create(data)

    def get_equipment(self, id: uuid.UUID) -> EquipmentModel:
        """
        Retrieves an equipment item by ID.
        Raises HTTP 404 if not found.
        """
        equipment = self.repo.get_by_id(id)
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipment item not found.",
            )
        return equipment

    def list_equipment(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> EquipmentListResponse:
        """
        Retrieves a paginated list of equipment items with filtering and searching.
        """
        items, total = self.repo.list(
            page=page,
            page_size=page_size,
            category=category,
            is_active=is_active,
            search=search,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [EquipmentResponse.model_validate(item) for item in items]

        return EquipmentListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_equipment(self, id: uuid.UUID, equipment_in: EquipmentUpdate) -> EquipmentModel:
        """
        Updates an existing equipment item.
        Re-validates name uniqueness and regenerates slug if the name is changed.
        """
        equipment = self.get_equipment(id)
        update_data = equipment_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"].lower() != equipment.name.lower():
            existing = self.repo.get_by_name(update_data["name"])
            if existing and existing.id != id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Equipment with name '{update_data['name']}' already exists.",
                )
            update_data["slug"] = generate_slug(update_data["name"])

        if "category" in update_data:
            update_data["category"] = update_data["category"].lower()

        return self.repo.update(equipment, update_data)

    def soft_delete_equipment(self, id: uuid.UUID) -> EquipmentModel:
        """
        Soft deletes an equipment item by setting is_active = False.
        """
        equipment = self.get_equipment(id)
        return self.repo.soft_delete(equipment)
