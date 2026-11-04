import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel


class MuscleGroupRepository:
    """
    SQLAlchemy repository implementation for Muscle Group database access.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: uuid.UUID) -> Optional[MuscleGroupModel]:
        """
        Retrieves a muscle group by unique UUID ID.
        """
        stmt = select(MuscleGroupModel).where(MuscleGroupModel.id == id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[MuscleGroupModel]:
        """
        Retrieves a muscle group by URL slug.
        """
        stmt = select(MuscleGroupModel).where(MuscleGroupModel.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[MuscleGroupModel]:
        """
        Retrieves a muscle group by name (case-insensitive).
        """
        stmt = select(MuscleGroupModel).where(func.lower(MuscleGroupModel.name) == name.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, data: dict) -> MuscleGroupModel:
        """
        Persists a new muscle group record in the database.
        """
        db_muscle_group = MuscleGroupModel(**data)
        self.db.add(db_muscle_group)
        self.db.commit()
        self.db.refresh(db_muscle_group)
        return db_muscle_group

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        body_region: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[MuscleGroupModel], int]:
        """
        Lists muscle groups with pagination, filtering by body region or is_active, and searching by name.
        Returns a tuple of (items, total_count).
        """
        query = select(MuscleGroupModel)

        if body_region:
            query = query.where(MuscleGroupModel.body_region == body_region.lower())

        if is_active is not None:
            query = query.where(MuscleGroupModel.is_active == is_active)

        if search:
            query = query.where(MuscleGroupModel.name.ilike(f"%{search.strip()}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(MuscleGroupModel.name.asc())

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    def update(self, muscle_group: MuscleGroupModel, update_data: dict) -> MuscleGroupModel:
        """
        Updates an existing muscle group record.
        """
        for key, value in update_data.items():
            setattr(muscle_group, key, value)
        self.db.add(muscle_group)
        self.db.commit()
        self.db.refresh(muscle_group)
        return muscle_group

    def soft_delete(self, muscle_group: MuscleGroupModel) -> MuscleGroupModel:
        """
        Soft deletes a muscle group record by setting is_active = False.
        """
        muscle_group.is_active = False
        self.db.add(muscle_group)
        self.db.commit()
        self.db.refresh(muscle_group)
        return muscle_group
