import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.exercises.application.dtos import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseListResponse,
    ExerciseFacetsResponse,
)
from app.modules.exercises.application.services import ExerciseService
from app.modules.exercises.infrastructure.repositories import ExerciseRepository

router = APIRouter()


@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exercise",
    description="Registers a new exercise in the library with an automatically generated URL slug."
)
def create_exercise_endpoint(
    exercise_in: ExerciseCreate,
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler for exercise creation.
    """
    repo = ExerciseRepository(db)
    service = ExerciseService(repo)
    return service.create_exercise(exercise_in)


@router.get(
    "",
    response_model=ExerciseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List exercises with pagination, filtering, and search",
    description="Retrieves a paginated list of exercises. Supports filtering by type, difficulty, active status, and name search."
)
def list_exercises_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    exercise_type: Optional[str] = Query(None, description="Filter by exercise type (e.g. strength, cardio)"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty (beginner, intermediate, advanced)"),
    equipment_id: Optional[uuid.UUID] = Query(None, description="Filter by equipment ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by exercise name"),
    muscle_group_id: Optional[uuid.UUID] = Query(None, description="Filter by associated muscle group"),
    is_compound: Optional[bool] = Query(None, description="Filter by compound or isolation movement"),
    has_media: Optional[bool] = Query(None, description="Only exercises with (true) or without (false) a ready demo"),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for paginated exercise catalog listing.
    """
    repo = ExerciseRepository(db)
    service = ExerciseService(repo)
    return service.list_exercises(
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


@router.get(
    "/facets",
    response_model=ExerciseFacetsResponse,
    status_code=status.HTTP_200_OK,
    summary="Filter options that return exercises",
    description="For each filter (muscle, equipment, type, level), the values that still match exercises under the other filters, with counts."
)
def list_exercise_facets_endpoint(
    exercise_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    equipment_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    muscle_group_id: Optional[uuid.UUID] = Query(None),
    has_media: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for the exercise library filter options.
    """
    service = ExerciseService(ExerciseRepository(db))
    return service.list_facets(
        exercise_type=exercise_type,
        difficulty_level=difficulty_level,
        equipment_id=equipment_id,
        is_active=is_active,
        search=search,
        muscle_group_id=muscle_group_id,
        has_media=has_media,
    )


@router.get(
    "/{id}",
    response_model=ExerciseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exercise details by ID",
    description="Retrieves details for a specific exercise by its UUID."
)
def get_exercise_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler for retrieving an exercise by ID.
    """
    repo = ExerciseRepository(db)
    service = ExerciseService(repo)
    return service.get_exercise_by_id(id)


@router.put(
    "/{id}",
    response_model=ExerciseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update exercise by ID",
    description="Updates exercise details. Automatically updates URL slug if the name is changed."
)
def update_exercise_endpoint(
    id: uuid.UUID,
    exercise_in: ExerciseUpdate,
    db: Session = Depends(get_db)
):
    """
    HTTP PUT handler for exercise modification.
    """
    repo = ExerciseRepository(db)
    service = ExerciseService(repo)
    return service.update_exercise(id, exercise_in)


@router.delete(
    "/{id}",
    response_model=ExerciseResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete exercise by ID",
    description="Soft deletes an exercise from the library by setting is_active = false."
)
def delete_exercise_endpoint(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    HTTP DELETE handler for soft deleting an exercise.
    """
    repo = ExerciseRepository(db)
    service = ExerciseService(repo)
    return service.delete_exercise(id)
