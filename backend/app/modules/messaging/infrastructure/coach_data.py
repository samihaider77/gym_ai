"""Reads and writes the member's own workout data for the chat bot, using the app's existing tables."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.exercises.infrastructure.models import ExerciseModel
from app.modules.progress.infrastructure.models import BodyProgressModel
from app.modules.workout_days.infrastructure.models import WorkoutDayModel
from app.modules.workout_exercises.infrastructure.models import WorkoutExerciseModel
from app.modules.workout_plans.infrastructure.models import WorkoutPlanModel
from app.modules.workout_sessions.domain.entities import STATUS_COMPLETED
from app.modules.workout_sessions.infrastructure.models import WorkoutSessionModel


@dataclass(frozen=True)
class ExerciseLine:
    name: str
    name_ur: Optional[str]
    sets: int
    reps: int
    weight_kg: Optional[float]
    duration_seconds: Optional[int]


@dataclass(frozen=True)
class Day:
    id: uuid.UUID
    number: int
    title: str
    minutes: Optional[int]
    exercises: List[ExerciseLine]


@dataclass(frozen=True)
class Plan:
    id: uuid.UUID
    name: str
    days: List[Day]  # sorted by day number; may be empty


class CoachData:
    def __init__(self, db: Session):
        self.db = db

    def active_plan(self, user_id: uuid.UUID) -> Optional[Plan]:
        """The member's most recently updated active plan, with its days and exercises."""
        plan = self.db.execute(
            select(WorkoutPlanModel)
            .where(WorkoutPlanModel.user_id == user_id, WorkoutPlanModel.is_active.is_(True))
            .order_by(WorkoutPlanModel.updated_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not plan:
            return None
        days = self.db.execute(
            select(WorkoutDayModel).where(WorkoutDayModel.workout_plan_id == plan.id).order_by(WorkoutDayModel.day_number)
        ).scalars().all()
        rows = self.db.execute(
            select(WorkoutExerciseModel, ExerciseModel)
            .join(ExerciseModel, ExerciseModel.id == WorkoutExerciseModel.exercise_id)
            .where(WorkoutExerciseModel.workout_day_id.in_([d.id for d in days] or [uuid.uuid4()]))
            .order_by(WorkoutExerciseModel.order_index)
        ).all()
        by_day = {}
        for item, exercise in rows:
            by_day.setdefault(item.workout_day_id, []).append(ExerciseLine(
                name=exercise.name, name_ur=exercise.name_ur, sets=item.sets, reps=item.reps,
                weight_kg=item.target_weight or None, duration_seconds=item.duration_seconds))
        return Plan(id=plan.id, name=plan.name, days=[
            Day(id=d.id, number=d.day_number, title=d.title, minutes=d.estimated_duration_minutes,
                exercises=by_day.get(d.id, [])) for d in days])

    def last_completed(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> Optional[WorkoutSessionModel]:
        return self.db.execute(
            select(WorkoutSessionModel)
            .where(WorkoutSessionModel.user_id == user_id, WorkoutSessionModel.workout_plan_id == plan_id,
                   WorkoutSessionModel.status == STATUS_COMPLETED)
            .order_by(WorkoutSessionModel.completed_at.desc().nulls_last(), WorkoutSessionModel.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    def complete_day(self, user_id: uuid.UUID, plan_id: uuid.UUID, day: Day, now: datetime) -> WorkoutSessionModel:
        session = WorkoutSessionModel(
            user_id=user_id, workout_plan_id=plan_id, workout_day_id=day.id, started_at=now, completed_at=now,
            duration_minutes=day.minutes or 0, status=STATUS_COMPLETED, notes="Logged from WhatsApp",
        )
        self.db.add(session)
        self.db.commit()
        return session

    def log_weight(self, user_id: uuid.UUID, weight_kg: float, now: datetime) -> None:
        self.db.add(BodyProgressModel(user_id=user_id, weight_kg=weight_kg, recorded_at=now,
                                      notes="Logged from WhatsApp"))
        self.db.commit()
