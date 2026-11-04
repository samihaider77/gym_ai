import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.modules.progress.infrastructure.models import BodyProgressModel


class BodyProgressRepository:
    """
    SQLAlchemy repository implementation for Body Progress database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_progress_by_id(self, progress_id: uuid.UUID) -> Optional[BodyProgressModel]:
        """
        Retrieves a body progress entry by unique UUID ID.
        """
        stmt = select(BodyProgressModel).where(BodyProgressModel.id == progress_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_latest_progress_by_user(self, user_id: uuid.UUID) -> Optional[BodyProgressModel]:
        """
        Retrieves the most recent body progress record for a user based on recorded_at date.
        """
        stmt = (
            select(BodyProgressModel)
            .where(BodyProgressModel.user_id == user_id)
            .order_by(BodyProgressModel.recorded_at.desc(), BodyProgressModel.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_progress(self, user_id: uuid.UUID, data: dict) -> BodyProgressModel:
        """
        Persists a new body progress entry in the database.
        """
        db_progress = BodyProgressModel(user_id=user_id, **data)
        self.db.add(db_progress)
        self.db.commit()
        self.db.refresh(db_progress)
        return db_progress

    def list_progress_history(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[BodyProgressModel], int]:
        """
        Lists body progress entries for a user with pagination, ordered by recorded_at descending.
        Returns a tuple of (items, total_count).
        """
        query = select(BodyProgressModel).where(BodyProgressModel.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(BodyProgressModel.recorded_at.desc())

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    def update_progress(self, progress: BodyProgressModel, update_data: dict) -> BodyProgressModel:
        """
        Updates an existing body progress entry.
        """
        for key, value in update_data.items():
            setattr(progress, key, value)
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        return progress
