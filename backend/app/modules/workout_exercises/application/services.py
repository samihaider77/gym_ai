import uuid
from typing import List
from fastapi import HTTPException, status
from app.modules.workout_exercises.application.dtos import (
    WorkoutExerciseCreate,
    WorkoutExerciseUpdate,
    ReorderExercisesRequest,
    WorkoutExerciseResponse,
    WorkoutExerciseListResponse,
)
from app.modules.workout_exercises.infrastructure.models import WorkoutExerciseModel
from app.modules.workout_exercises.infrastructure.repositories import WorkoutExerciseRepository
from app.modules.workout_days.infrastructure.repositories import WorkoutDayRepository
from app.modules.workout_plans.infrastructure.repositories import WorkoutPlanRepository
from app.modules.exercises.infrastructure.repositories import ExerciseRepository


class WorkoutExerciseService:
    """
    Application Service orchestrating Workout Exercise configurations and validations.
    """
    def __init__(
        self,
        we_repo: WorkoutExerciseRepository,
        day_repo: WorkoutDayRepository,
        plan_repo: WorkoutPlanRepository,
        exercise_repo: ExerciseRepository,
    ):
        self.we_repo = we_repo
        self.day_repo = day_repo
        self.plan_repo = plan_repo
        self.exercise_repo = exercise_repo

    def _verify_day_ownership(self, workout_day_id: uuid.UUID, user_id: uuid.UUID):
        """
        Helper method verifying parent day and plan existence and user ownership.
        """
        day = self.day_repo.get_day_by_id(workout_day_id)
        if not day:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout day not found.",
            )
        plan = self.plan_repo.get_plan_by_id(day.workout_plan_id)
        if not plan or plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this workout plan.",
            )
        return day

    def create_workout_exercise(
        self,
        workout_day_id: uuid.UUID,
        user_id: uuid.UUID,
        exercise_in: WorkoutExerciseCreate
    ) -> WorkoutExerciseModel:
        """
        Adds an exercise configuration to a workout day.
        Validates day user ownership, exercise existence, sets/reps > 0, and unique order position.
        """
        self._verify_day_ownership(workout_day_id, user_id)

        # 1. Verify exercise existence in catalog
        ex = self.exercise_repo.get_exercise_by_id(exercise_in.exercise_id)
        if not ex:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found in library.",
            )

        # 2. Verify sets & reps > 0
        if exercise_in.sets <= 0 or exercise_in.reps <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sets and reps must be greater than zero.",
            )

        # 3. Check order index uniqueness in day
        existing_order = self.we_repo.get_by_day_and_order(workout_day_id, exercise_in.order_index)
        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise position {exercise_in.order_index} is already occupied in this workout day.",
            )

        data = exercise_in.model_dump()
        return self.we_repo.create(workout_day_id, data)

    def list_by_day(self, workout_day_id: uuid.UUID, user_id: uuid.UUID) -> WorkoutExerciseListResponse:
        """
        Lists all exercises in a workout day ordered by order_index.
        """
        self._verify_day_ownership(workout_day_id, user_id)
        items = self.we_repo.list_by_day(workout_day_id)
        responses = [WorkoutExerciseResponse.model_validate(item) for item in items]
        return WorkoutExerciseListResponse(items=responses, total=len(responses))

    def update_workout_exercise(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        exercise_in: WorkoutExerciseUpdate
    ) -> WorkoutExerciseModel:
        """
        Updates an existing workout exercise configuration.
        """
        we = self.we_repo.get_by_id(id)
        if not we:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout exercise configuration not found.",
            )

        self._verify_day_ownership(we.workout_day_id, user_id)
        update_data = exercise_in.model_dump(exclude_unset=True)

        if "exercise_id" in update_data:
            ex = self.exercise_repo.get_exercise_by_id(update_data["exercise_id"])
            if not ex:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found in library.",
                )

        if ("sets" in update_data and update_data["sets"] <= 0) or ("reps" in update_data and update_data["reps"] <= 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sets and reps must be greater than zero.",
            )

        if "order_index" in update_data and update_data["order_index"] != we.order_index:
            existing = self.we_repo.get_by_day_and_order(we.workout_day_id, update_data["order_index"])
            if existing and existing.id != id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise position {update_data['order_index']} is already occupied.",
                )

        return self.we_repo.update(we, update_data)

    def delete_workout_exercise(self, id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Deletes a workout exercise from a day.
        """
        we = self.we_repo.get_by_id(id)
        if not we:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout exercise configuration not found.",
            )

        self._verify_day_ownership(we.workout_day_id, user_id)
        self.we_repo.delete(we)

    def reorder_workout_exercises(self, user_id: uuid.UUID, reorder_in: ReorderExercisesRequest) -> None:
        """
        Reorders a batch of workout exercises within a day.
        """
        if not reorder_in.items:
            return

        # Verify ownership of first item
        first_we = self.we_repo.get_by_id(reorder_in.items[0].id)
        if not first_we:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout exercise configuration not found.",
            )
        self._verify_day_ownership(first_we.workout_day_id, user_id)

        items_dict = [{"id": item.id, "order_index": item.order_index} for item in reorder_in.items]
        self.we_repo.reorder(items_dict)
