import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.modules.workout_sessions.infrastructure.models import WorkoutSessionModel
from app.modules.workout_sessions.domain.entities import STATUS_IN_PROGRESS


class WorkoutSessionRepository:
    """
    SQLAlchemy repository implementation for Workout Session database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_session_by_id(self, session_id: uuid.UUID) -> Optional[WorkoutSessionModel]:
        """
        Retrieves a workout session by unique UUID ID.
        """
        stmt = select(WorkoutSessionModel).where(WorkoutSessionModel.id == session_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_session_by_user(self, user_id: uuid.UUID) -> Optional[WorkoutSessionModel]:
        """
        Retrieves an active (IN_PROGRESS) workout session for a given user.
        """
        stmt = select(WorkoutSessionModel).where(
            and_(
                WorkoutSessionModel.user_id == user_id,
                WorkoutSessionModel.status == STATUS_IN_PROGRESS
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_session(self, user_id: uuid.UUID, data: dict) -> WorkoutSessionModel:
        """
        Persists a new workout session record in the database.
        """
        db_session = WorkoutSessionModel(user_id=user_id, **data)
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def list_user_sessions(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[WorkoutSessionModel], int]:
        """
        Lists workout sessions owned by a specific user with pagination and optional status filter.
        Returns a tuple of (items, total_count).
        """
        query = select(WorkoutSessionModel).where(WorkoutSessionModel.user_id == user_id)

        if status_filter:
            query = query.where(WorkoutSessionModel.status == status_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(WorkoutSessionModel.started_at.desc())

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    def update_session(self, session: WorkoutSessionModel, update_data: dict) -> WorkoutSessionModel:
        """
        Updates an existing workout session.
        """
        for key, value in update_data.items():
            setattr(session, key, value)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
