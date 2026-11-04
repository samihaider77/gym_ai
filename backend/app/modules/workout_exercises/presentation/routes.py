import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.modules.auth.presentation.dependencies import get_current_user
from app.modules.users.infrastructure.models import UserModel
from app.modules.workout_exercises.application.dtos import (
    WorkoutExerciseCreate,
    WorkoutExerciseUpdate,
    ReorderExercisesRequest,
    WorkoutExerciseResponse,
    WorkoutExerciseListResponse,
)
from app.modules.workout_exercises.application.services import WorkoutExerciseService
from app.modules.workout_exercises.infrastructure.repositories import WorkoutExerciseRepository
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository
from app.modules.exercises.infrastructure.repositories import ExerciseRepository

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> WorkoutExerciseService:
    we_repo = WorkoutExerciseRepository(db)
    day_repo = WorkoutDayRepository(db)
    plan_repo = WorkoutPlanRepository(db)
    exercise_repo = ExerciseRepository(db)
    return WorkoutExerciseService(we_repo, day_repo, plan_repo, exercise_repo)


@router.post(
    "/workout-days/{day_id}/exercises",
    response_model=WorkoutExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an exercise to a workout day",
    description="Adds an exercise configuration (sets, reps, target weight, order) to a workout day."
)
def create_workout_exercise_endpoint(
    day_id: uuid.UUID,
    exercise_in: WorkoutExerciseCreate,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutExerciseService = Depends(get_service)
):
    """
    HTTP POST handler for adding an exercise to a workout day.
    """
    return service.create_workout_exercise(day_id, current_user.id, exercise_in)


@router.get(
    "/workout-days/{day_id}/exercises",
    response_model=WorkoutExerciseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List exercises in a workout day",
    description="Retrieves all exercises configured in a workout day ordered by order_index."
)
def list_workout_exercises_endpoint(
    day_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutExerciseService = Depends(get_service)
):
    """
    HTTP GET handler for listing exercises in a workout day.
    """
    return service.list_by_day(day_id, current_user.id)


@router.patch(
    "/workout-exercises/reorder",
    status_code=status.HTTP_200_OK,
    summary="Reorder exercises in a workout day",
    description="Batch updates the order_index positions of workout exercises."
)
def reorder_workout_exercises_endpoint(
    reorder_in: ReorderExercisesRequest,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutExerciseService = Depends(get_service)
):
    """
    HTTP PATCH handler for exercise position reordering.
    """
    service.reorder_workout_exercises(current_user.id, reorder_in)
    return {"status": "success", "message": "Exercises reordered successfully."}


@router.put(
    "/workout-exercises/{id}",
    response_model=WorkoutExerciseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workout exercise configuration by ID",
    description="Updates sets, reps, weight, rest time, or order index of a workout exercise."
)
def update_workout_exercise_endpoint(
    id: uuid.UUID,
    exercise_in: WorkoutExerciseUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutExerciseService = Depends(get_service)
):
    """
    HTTP PUT handler for modifying a workout exercise configuration.
    """
    return service.update_workout_exercise(id, current_user.id, exercise_in)


@router.delete(
    "/workout-exercises/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workout exercise by ID",
    description="Removes an exercise configuration from a workout day."
)
def delete_workout_exercise_endpoint(
    id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: WorkoutExerciseService = Depends(get_service)
):
    """
    HTTP DELETE handler for removing a workout exercise configuration.
    """
    service.delete_workout_exercise(id, current_user.id)
    return None
