from datetime import datetime, timezone
import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.modules.progress.application.dtos import (
    BodyProgressCreate,
    BodyProgressUpdate,
    BodyProgressResponse,
    BodyProgressListResponse,
)
from app.modules.progress.infrastructure.models import BodyProgressModel
from app.modules.progress.infrastructure.repositories import BodyProgressRepository
from app.modules.user_profile.infrastructure.repositories import UserProfileRepository


class BodyProgressService:
    """
    Application Service orchestrating Body Progress tracking and BMI calculation.
    """
    def __init__(
        self,
        progress_repo: BodyProgressRepository,
        profile_repo: UserProfileRepository,
    ):
        self.progress_repo = progress_repo
        self.profile_repo = profile_repo

    def _calculate_bmi(self, user_id: uuid.UUID, weight_kg: float) -> Optional[float]:
        """
        Calculates BMI automatically if user profile height_cm exists.
        Formula: weight_kg / (height_m ^ 2)
        """
        profile = self.profile_repo.get_profile_by_user_id(user_id)
        if profile and profile.height_cm and profile.height_cm > 0:
            height_m = profile.height_cm / 100.0
            return round(weight_kg / (height_m ** 2), 2)
        return None

    def create_progress(self, user_id: uuid.UUID, progress_in: BodyProgressCreate) -> BodyProgressModel:
        """
        Creates a new body progress entry.
        Validates recorded_at is not in the future and computes BMI automatically.
        """
        now = datetime.now(timezone.utc)
        recorded_at = progress_in.recorded_at or now

        # Ensure tz-aware comparison
        compare_recorded = recorded_at if recorded_at.tzinfo else recorded_at.replace(tzinfo=timezone.utc)
        if compare_recorded > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Measurement recorded_at date cannot be in the future.",
            )

        data = progress_in.model_dump()
        data["recorded_at"] = compare_recorded

        # Compute BMI automatically
        data["bmi"] = self._calculate_bmi(user_id, progress_in.weight_kg)

        return self.progress_repo.create_progress(user_id, data)

    def get_latest_progress(self, user_id: uuid.UUID) -> BodyProgressModel:
        """
        Retrieves the most recent body progress record for the user.
        Raises HTTP 404 if no progress entries exist.
        """
        progress = self.progress_repo.get_latest_progress_by_user(user_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No body progress records found.",
            )
        return progress

    def list_progress_history(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> BodyProgressListResponse:
        """
        Retrieves a paginated list of body progress entries for the user.
        """
        items, total = self.progress_repo.list_progress_history(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [BodyProgressResponse.model_validate(item) for item in items]

        return BodyProgressListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_progress(
        self,
        progress_id: uuid.UUID,
        user_id: uuid.UUID,
        progress_in: BodyProgressUpdate
    ) -> BodyProgressModel:
        """
        Updates an existing body progress entry owned by the user.
        Re-computes BMI if weight_kg is modified.
        """
        progress = self.progress_repo.get_progress_by_id(progress_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Body progress entry not found.",
            )
        if progress.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this progress entry.",
            )

        update_data = progress_in.model_dump(exclude_unset=True)

        if "recorded_at" in update_data and update_data["recorded_at"]:
            now = datetime.now(timezone.utc)
            rec = update_data["recorded_at"]
            compare_rec = rec if rec.tzinfo else rec.replace(tzinfo=timezone.utc)
            if compare_rec > now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Measurement recorded_at date cannot be in the future.",
                )
            update_data["recorded_at"] = compare_rec

        if "weight_kg" in update_data:
            update_data["bmi"] = self._calculate_bmi(user_id, update_data["weight_kg"])

        return self.progress_repo.update_progress(progress, update_data)
