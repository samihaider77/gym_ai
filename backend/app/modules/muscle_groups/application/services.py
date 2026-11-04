import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.core.utils.slug import generate_slug
from app.modules.muscle_groups.application.dtos import (
    MuscleGroupCreate,
    MuscleGroupUpdate,
    MuscleGroupResponse,
    MuscleGroupListResponse,
)
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel
from app.modules.muscle_groups.infrastructure.repositories import MuscleGroupRepository


class MuscleGroupService:
    """
    Application Service orchestrating Muscle Group use-cases and business rules.
    """
    def __init__(self, repo: MuscleGroupRepository):
        self.repo = repo

    def create_muscle_group(self, muscle_group_in: MuscleGroupCreate) -> MuscleGroupModel:
        """
        Creates a new muscle group.
        Validates name uniqueness and generates URL slug automatically using shared utility.
        """
        # 1. Check duplicate name
        existing = self.repo.get_by_name(muscle_group_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Muscle group with name '{muscle_group_in.name}' already exists.",
            )

        # 2. Generate slug and prepare data
        slug = generate_slug(muscle_group_in.name)
        data = muscle_group_in.model_dump()
        data["slug"] = slug
        data["body_region"] = muscle_group_in.body_region.lower()
        data["is_active"] = True

        return self.repo.create(data)

    def get_muscle_group(self, id: uuid.UUID) -> MuscleGroupModel:
        """
        Retrieves a muscle group by ID.
        Raises HTTP 404 if not found.
        """
        muscle_group = self.repo.get_by_id(id)
        if not muscle_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Muscle group not found.",
            )
        return muscle_group

    def list_muscle_groups(
        self,
        page: int = 1,
        page_size: int = 20,
        body_region: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> MuscleGroupListResponse:
        """
        Retrieves a paginated list of muscle groups with filtering and searching.
        """
        items, total = self.repo.list(
            page=page,
            page_size=page_size,
            body_region=body_region,
            is_active=is_active,
            search=search,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [MuscleGroupResponse.model_validate(item) for item in items]

        return MuscleGroupListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_muscle_group(self, id: uuid.UUID, muscle_group_in: MuscleGroupUpdate) -> MuscleGroupModel:
        """
        Updates an existing muscle group.
        Re-validates name uniqueness and regenerates slug if the name is changed.
        """
        muscle_group = self.get_muscle_group(id)
        update_data = muscle_group_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"].lower() != muscle_group.name.lower():
            existing = self.repo.get_by_name(update_data["name"])
            if existing and existing.id != id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Muscle group with name '{update_data['name']}' already exists.",
                )
            update_data["slug"] = generate_slug(update_data["name"])

        if "body_region" in update_data:
            update_data["body_region"] = update_data["body_region"].lower()

        return self.repo.update(muscle_group, update_data)

    def soft_delete_muscle_group(self, id: uuid.UUID) -> MuscleGroupModel:
        """
        Soft deletes a muscle group by setting is_active = False.
        """
        muscle_group = self.get_muscle_group(id)
        return self.repo.soft_delete(muscle_group)
