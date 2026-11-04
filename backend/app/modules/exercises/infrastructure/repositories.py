import uuid
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import ColumnElement, select, func, delete, exists
from app.modules.exercises.infrastructure.models import ExerciseModel
from app.modules.exercises.infrastructure.models import exercise_muscle_association
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel, VISIBLE_MEDIA_STATUSES
from app.modules.equipment.infrastructure.models import EquipmentModel
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel


class ExerciseRepository:
    """
    SQLAlchemy repository implementation for Exercise database operations.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_exercise_by_id(self, exercise_id: uuid.UUID) -> Optional[ExerciseModel]:
        """
        Retrieves an exercise by its unique UUID ID.
        """
        stmt = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_exercise_by_slug(self, slug: str) -> Optional[ExerciseModel]:
        """
        Retrieves an exercise by its unique URL slug.
        """
        stmt = select(ExerciseModel).where(ExerciseModel.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_exercise_by_name(self, name: str) -> Optional[ExerciseModel]:
        """
        Retrieves an exercise by name (case-insensitive).
        """
        stmt = select(ExerciseModel).where(func.lower(ExerciseModel.name) == name.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create_exercise(self, exercise_data: dict) -> ExerciseModel:
        """
        Persists a new exercise record in the database.
        """
        db_exercise = ExerciseModel(**exercise_data)
        self.db.add(db_exercise)
        self.db.commit()
        self.db.refresh(db_exercise)
        return db_exercise

    def list_exercises(
        self,
        page: int = 1,
        page_size: int = 20,
        exercise_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        equipment_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        muscle_group_id: Optional[uuid.UUID] = None,
        is_compound: Optional[bool] = None,
        has_media: Optional[bool] = None,
    ) -> Tuple[List[ExerciseModel], int]:
        """
        Lists exercises with optional pagination, filtering, and search options.
        Returns a tuple of (items, total_count).
        """
        query = select(ExerciseModel).where(*self._conditions(
            exercise_type=exercise_type, difficulty_level=difficulty_level, equipment_id=equipment_id,
            is_active=is_active, search=search, muscle_group_id=muscle_group_id, is_compound=is_compound,
            has_media=has_media,
        ).values())

        # Calculate total matching records count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.execute(count_query).scalar_one()

        # Apply ordering and pagination
        offset = (page - 1) * page_size
        query = query.order_by(ExerciseModel.name.asc()).offset(offset).limit(page_size)

        items = list(self.db.execute(query).scalars().all())
        return items, total_count

    @staticmethod
    def _conditions(
        exercise_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        equipment_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        muscle_group_id: Optional[uuid.UUID] = None,
        is_compound: Optional[bool] = None,
        has_media: Optional[bool] = None,
    ) -> Dict[str, ColumnElement]:
        """
        Builds the WHERE clauses for the given filters, keyed by filter name so facet counts can leave one out.
        """
        conditions: Dict[str, ColumnElement] = {}
        if exercise_type:
            conditions["exercise_type"] = ExerciseModel.exercise_type == exercise_type.lower()
        if difficulty_level:
            conditions["difficulty_level"] = ExerciseModel.difficulty_level == difficulty_level.lower()
        if equipment_id:
            conditions["equipment_id"] = ExerciseModel.equipment_id == equipment_id
        if is_active is not None:
            conditions["is_active"] = ExerciseModel.is_active == is_active
        if search:
            term = f"%{search.strip()}%"
            conditions["search"] = ExerciseModel.name.ilike(term) | ExerciseModel.name_ur.ilike(term) | ExerciseModel.description.ilike(term)
        if muscle_group_id:
            # Primary muscle only: a shoulder press that also works the chest is not a chest exercise.
            conditions["muscle_group_id"] = exists(select(1).where(
                exercise_muscle_association.c.exercise_id == ExerciseModel.id,
                exercise_muscle_association.c.muscle_group_id == muscle_group_id,
                exercise_muscle_association.c.role == "primary",
            ))
        if is_compound is not None:
            conditions["is_compound"] = ExerciseModel.is_compound == is_compound
        if has_media is not None:
            media_exists = exists(select(1).where(
                ExerciseMediaModel.exercise_id == ExerciseModel.id,
                ExerciseMediaModel.status.in_(VISIBLE_MEDIA_STATUSES),
            ))
            conditions["has_media"] = media_exists if has_media else ~media_exists
        return conditions

    def facets(self, **filters) -> Dict[str, List[Tuple[object, int]]]:
        """
        For each filter dropdown, the values that still return exercises and how many.
        Each facet applies every other filter but not its own, so the current choice can still be changed.
        """
        conditions = self._conditions(**filters)

        def others(name: str) -> list:
            return [clause for key, clause in conditions.items() if key != name]

        muscles = self.db.execute(
            select(exercise_muscle_association.c.muscle_group_id, func.count(func.distinct(ExerciseModel.id)))
            .join(ExerciseModel, ExerciseModel.id == exercise_muscle_association.c.exercise_id)
            .where(exercise_muscle_association.c.role == "primary", *others("muscle_group_id"))
            .group_by(exercise_muscle_association.c.muscle_group_id)
        ).all()
        equipment = self.db.execute(
            select(ExerciseModel.equipment_id, func.count()).where(ExerciseModel.equipment_id.is_not(None), *others("equipment_id"))
            .group_by(ExerciseModel.equipment_id)
        ).all()
        types = self.db.execute(
            select(ExerciseModel.exercise_type, func.count()).where(*others("exercise_type")).group_by(ExerciseModel.exercise_type)
        ).all()
        levels = self.db.execute(
            select(ExerciseModel.difficulty_level, func.count()).where(*others("difficulty_level")).group_by(ExerciseModel.difficulty_level)
        ).all()
        return {"muscles": muscles, "equipment": equipment, "types": types, "levels": levels}

    def set_muscles(self, exercise: ExerciseModel, primary_ids: List[uuid.UUID], secondary_ids: List[uuid.UUID]) -> None:
        all_ids = list(dict.fromkeys(primary_ids + secondary_ids))
        found = self.db.execute(select(MuscleGroupModel.id).where(MuscleGroupModel.id.in_(all_ids))).scalars().all() if all_ids else []
        if set(found) != set(all_ids):
            raise ValueError("One or more muscle group IDs are invalid.")
        self.db.execute(delete(exercise_muscle_association).where(exercise_muscle_association.c.exercise_id == exercise.id))
        rows = [{"exercise_id": exercise.id, "muscle_group_id": muscle_id, "role": "primary" if muscle_id in primary_ids else "secondary"} for muscle_id in all_ids]
        if rows: self.db.execute(exercise_muscle_association.insert(), rows)
        self.db.commit()

    def equipment_exists(self, equipment_id: uuid.UUID) -> bool:
        return self.db.execute(select(EquipmentModel.id).where(EquipmentModel.id == equipment_id)).scalar_one_or_none() is not None

    def muscle_ids_exist(self, muscle_ids: List[uuid.UUID]) -> bool:
        if not muscle_ids:
            return True
        found = self.db.execute(select(MuscleGroupModel.id).where(MuscleGroupModel.id.in_(set(muscle_ids)))).scalars().all()
        return set(found) == set(muscle_ids)

    def update_exercise(self, exercise: ExerciseModel, update_data: dict) -> ExerciseModel:
        """
        Updates an existing exercise record.
        """
        for key, value in update_data.items():
            setattr(exercise, key, value)
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def delete_exercise(self, exercise: ExerciseModel) -> ExerciseModel:
        """
        Soft deletes an exercise record by setting is_active = False.
        """
        exercise.is_active = False
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise
