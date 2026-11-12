from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.profiles import get_profile_or_404
from app.schemas import GenerateWorkoutRequest, WorkoutPlanResponse
from app.services.workout_service import (
    generate_full_workout_for_profile,
    regenerate_single_workout_day_for_profile,
)

router = APIRouter(prefix="/profiles/{profile_id}/workouts", tags=["Workouts"])


@router.post(
    "/generate-full",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_full_workout(
    profile_id: uuid.UUID,
    payload: GenerateWorkoutRequest,
    db: Session = Depends(get_db),
) -> WorkoutPlanResponse:
    profile = get_profile_or_404(db, profile_id)
    return generate_full_workout_for_profile(
        db=db,
        profile=profile,
        excluded_exercise_ids=payload.excluded_exercise_ids,
    )


@router.post(
    "/days/{day_number}/regenerate",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
)
def regenerate_workout_day(
    profile_id: uuid.UUID,
    payload: GenerateWorkoutRequest,
    day_number: int = Path(..., ge=1, le=7),
    db: Session = Depends(get_db),
) -> WorkoutPlanResponse:
    profile = get_profile_or_404(db, profile_id)
    return regenerate_single_workout_day_for_profile(
        db=db,
        profile=profile,
        day_number=day_number,
        excluded_exercise_ids=payload.excluded_exercise_ids,
    )
