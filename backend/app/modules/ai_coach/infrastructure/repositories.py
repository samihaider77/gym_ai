import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.ai_coach.infrastructure.models import MealLogModel


class MealLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: uuid.UUID, data: dict) -> MealLogModel:
        meal = MealLogModel(user_id=user_id, **data)
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def get(self, meal_id: uuid.UUID) -> Optional[MealLogModel]:
        return self.db.execute(select(MealLogModel).where(MealLogModel.id == meal_id)).scalar_one_or_none()

    def between(self, user_id: uuid.UUID, start: datetime, end: datetime) -> List[MealLogModel]:
        stmt = (
            select(MealLogModel)
            .where(MealLogModel.user_id == user_id, MealLogModel.eaten_at >= start, MealLogModel.eaten_at < end)
            .order_by(MealLogModel.eaten_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, meal: MealLogModel) -> None:
        self.db.delete(meal)
        self.db.commit()
