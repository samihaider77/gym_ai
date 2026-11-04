import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.modules.equipment.infrastructure.models import EquipmentModel


class EquipmentRepository:
    """
    SQLAlchemy repository implementation for Equipment database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: uuid.UUID) -> Optional[EquipmentModel]:
        """
        Retrieves equipment by unique UUID ID.
        """
        stmt = select(EquipmentModel).where(EquipmentModel.id == id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[EquipmentModel]:
        """
        Retrieves equipment by URL slug.
        """
        stmt = select(EquipmentModel).where(EquipmentModel.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[EquipmentModel]:
        """
        Retrieves equipment by name (case-insensitive).
        """
        stmt = select(EquipmentModel).where(func.lower(EquipmentModel.name) == name.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, data: dict) -> EquipmentModel:
        """
        Persists a new equipment record in the database.
        """
        db_equipment = EquipmentModel(**data)
        self.db.add(db_equipment)
        self.db.commit()
        self.db.refresh(db_equipment)
        return db_equipment

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[EquipmentModel], int]:
        """
        Lists equipment items with pagination, filtering by category or is_active, and searching by name.
        Returns a tuple of (items, total_count).
        """
        query = select(EquipmentModel)

        if category:
            query = query.where(EquipmentModel.category == category.lower())

        if is_active is not None:
            query = query.where(EquipmentModel.is_active == is_active)

        if search:
            query = query.where(EquipmentModel.name.ilike(f"%{search.strip()}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(EquipmentModel.name.asc())

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    def update(self, equipment: EquipmentModel, update_data: dict) -> EquipmentModel:
        """
        Updates an existing equipment record.
        """
        for key, value in update_data.items():
            setattr(equipment, key, value)
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def soft_delete(self, equipment: EquipmentModel) -> EquipmentModel:
        """
        Soft deletes an equipment record by setting is_active = False.
        """
        equipment.is_active = False
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment
