import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.core.utils.slug import generate_slug
from app.modules.exercises.application.dtos import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseListResponse,
    ExerciseFacetsResponse,
    FacetCount,
)
from app.modules.exercises.domain.entities import (
    VALID_DIFFICULTY_LEVELS,
    VALID_EXERCISE_TYPES,
)
from app.modules.exercises.infrastructure.media_models import VISIBLE_MEDIA_STATUSES
from app.modules.exercises.infrastructure.models import ExerciseModel
from app.modules.exercises.infrastructure.repositories import ExerciseRepository


class ExerciseService:
    """
    Application Service orchestrating Exercise use-cases and business rules.
    """
    def __init__(self, exercise_repo: ExerciseRepository):
        self.exercise_repo = exercise_repo

    def _validate_enums(self, difficulty_level: str, exercise_type: str):
        """
        Validates difficulty_level and exercise_type against domain rules.
        """
        if difficulty_level.lower() not in VALID_DIFFICULTY_LEVELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty_level. Must be one of: {', '.join(sorted(VALID_DIFFICULTY_LEVELS))}",
            )
        if exercise_type.lower() not in VALID_EXERCISE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid exercise_type. Must be one of: {', '.join(sorted(VALID_EXERCISE_TYPES))}",
            )

    def create_exercise(self, exercise_in: ExerciseCreate) -> ExerciseModel:
        """
        Creates a new exercise.
        Validates name uniqueness, generates URL slug automatically, and checks enum attributes.
        """
        # 1. Check duplicate exercise name
        existing_exercise = self.exercise_repo.get_exercise_by_name(exercise_in.name)
        if existing_exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise with name '{exercise_in.name}' already exists.",
            )

        # 2. Validate domain enums
        self._validate_enums(exercise_in.difficulty_level, exercise_in.exercise_type)
        if exercise_in.equipment_id and not self.exercise_repo.equipment_exists(exercise_in.equipment_id):
            raise HTTPException(status_code=400, detail="Invalid equipment_id.")
        muscle_ids = exercise_in.primary_muscle_ids + exercise_in.secondary_muscle_ids
        if not self.exercise_repo.muscle_ids_exist(muscle_ids):
            raise HTTPException(status_code=400, detail="One or more muscle group IDs are invalid.")

        # 3. Generate URL slug automatically using shared utility
        slug = generate_slug(exercise_in.name)

        # 4. Construct exercise persistence data
        exercise_data = exercise_in.model_dump(exclude={"primary_muscle_ids", "secondary_muscle_ids"})
        exercise_data["slug"] = slug
        exercise_data["difficulty_level"] = exercise_in.difficulty_level.lower()
        exercise_data["exercise_type"] = exercise_in.exercise_type.lower()
        exercise_data["is_active"] = True

        exercise = self.exercise_repo.create_exercise(exercise_data)
        self.exercise_repo.set_muscles(exercise, exercise_in.primary_muscle_ids, exercise_in.secondary_muscle_ids)
        return exercise

    def get_exercise_by_id(self, exercise_id: uuid.UUID) -> ExerciseModel:
        """
        Retrieves an exercise by ID.
        Raises HTTP 404 if not found.
        """
        exercise = self.exercise_repo.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found.",
            )
        return exercise

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
    ) -> ExerciseListResponse:
        """
        Retrieves a paginated list of exercises with optional filters and name search.
        """
        items, total = self.exercise_repo.list_exercises(
            page=page,
            page_size=page_size,
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
            equipment_id=equipment_id,
            is_active=is_active,
            search=search,
            muscle_group_id=muscle_group_id,
            is_compound=is_compound,
            has_media=has_media,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        exercise_responses = [self.to_response(item) for item in items]

        return ExerciseListResponse(
            items=exercise_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def list_facets(self, **filters) -> ExerciseFacetsResponse:
        """
        Returns the filter options that still match exercises, with counts, largest first.
        """
        facets = self.exercise_repo.facets(**filters)
        return ExerciseFacetsResponse(**{
            name: [FacetCount(value=str(value), count=count) for value, count in sorted(rows, key=lambda r: -r[1])]
            for name, rows in facets.items()
        })

    def update_exercise(self, exercise_id: uuid.UUID, exercise_in: ExerciseUpdate) -> ExerciseModel:
        """
        Updates an existing exercise.
        Re-validates name uniqueness and regenerates slug if the exercise name changes.
        """
        exercise = self.get_exercise_by_id(exercise_id)

        update_data = exercise_in.model_dump(exclude_unset=True)

        # Re-validate name uniqueness & slug if name is updated
        if "name" in update_data and update_data["name"].lower() != exercise.name.lower():
            existing = self.exercise_repo.get_exercise_by_name(update_data["name"])
            if existing and existing.id != exercise_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise with name '{update_data['name']}' already exists.",
                )
            update_data["slug"] = generate_slug(update_data["name"])

        # Re-validate enums if provided
        diff_level = update_data.get("difficulty_level", exercise.difficulty_level)
        ex_type = update_data.get("exercise_type", exercise.exercise_type)
        self._validate_enums(diff_level, ex_type)
        if update_data.get("equipment_id") and not self.exercise_repo.equipment_exists(update_data["equipment_id"]):
            raise HTTPException(status_code=400, detail="Invalid equipment_id.")
        muscle_ids = (update_data.get("primary_muscle_ids") or []) + (update_data.get("secondary_muscle_ids") or [])
        if not self.exercise_repo.muscle_ids_exist(muscle_ids):
            raise HTTPException(status_code=400, detail="One or more muscle group IDs are invalid.")

        if "difficulty_level" in update_data:
            update_data["difficulty_level"] = update_data["difficulty_level"].lower()
        if "exercise_type" in update_data:
            update_data["exercise_type"] = update_data["exercise_type"].lower()

        primary = update_data.pop("primary_muscle_ids", None)
        secondary = update_data.pop("secondary_muscle_ids", None)
        updated = self.exercise_repo.update_exercise(exercise, update_data)
        if primary is not None or secondary is not None:
            self.exercise_repo.set_muscles(updated, primary or [], secondary or [])
        return updated

    def delete_exercise(self, exercise_id: uuid.UUID) -> ExerciseModel:
        """
        Soft deletes an exercise by setting is_active = False.
        """
        exercise = self.get_exercise_by_id(exercise_id)
        return self.exercise_repo.delete_exercise(exercise)

    @staticmethod
    def to_response(item: ExerciseModel) -> ExerciseResponse:
        return ExerciseResponse(
            **{field: getattr(item, field) for field in ("id", "name", "slug", "description", "instructions", "name_ur", "instructions_ur", "difficulty_level", "exercise_type", "force_type", "mechanic_type", "equipment_id", "is_compound", "is_active", "created_at", "updated_at")},
            equipment=item.equipment,
            primary_muscles=item.primary_muscles,
            secondary_muscles=item.secondary_muscles,
            media=[m for m in item.media if m.status in VISIBLE_MEDIA_STATUSES],
        )
