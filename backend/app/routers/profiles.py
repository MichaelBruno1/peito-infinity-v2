from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Profile
from app.schemas import (
    ProfileCreateUpdateRequest,
    ProfileResponse,
    UpdateExcludedExercisesRequest,
)
from app.services.workout_service import (
    serialize_profile,
    update_profile_excluded_exercises,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def get_profile_or_404(db: Session, profile_id: uuid.UUID) -> Profile:
    stmt = (
        select(Profile)
        .where(Profile.id == profile_id)
        .options(selectinload(Profile.excluded_links))
    )
    profile = db.scalars(stmt).first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PROFILE_NOT_FOUND",
                "message": "Perfil de usuário não encontrado.",
            },
        )
    return profile


@router.get("", response_model=list[ProfileResponse])
def list_profiles(db: Session = Depends(get_db)) -> list[ProfileResponse]:
    stmt = (
        select(Profile)
        .options(selectinload(Profile.excluded_links))
        .order_by(Profile.created_at.desc())
    )
    profiles = list(db.scalars(stmt).all())
    return [serialize_profile(db, p, include_workout=False) for p in profiles]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreateUpdateRequest,
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = Profile(
        name=payload.name,
        weight_kg=Decimal(str(payload.weight_kg)),
        height_cm=Decimal(str(payload.height_cm)),
        fitness_level=payload.fitness_level,
        goal=payload.goal,
        available_time_minutes=payload.available_time_minutes,
        days_per_week=payload.days_per_week,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return serialize_profile(db, profile, include_workout=True)


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = get_profile_or_404(db, profile_id)
    return serialize_profile(db, profile, include_workout=True)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: uuid.UUID,
    payload: ProfileCreateUpdateRequest,
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = get_profile_or_404(db, profile_id)
    profile.name = payload.name
    profile.weight_kg = Decimal(str(payload.weight_kg))
    profile.height_cm = Decimal(str(payload.height_cm))
    profile.fitness_level = payload.fitness_level
    profile.goal = payload.goal
    profile.available_time_minutes = payload.available_time_minutes
    profile.days_per_week = payload.days_per_week
    profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(profile)
    return serialize_profile(db, profile, include_workout=True)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    profile = get_profile_or_404(db, profile_id)
    db.delete(profile)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{profile_id}/excluded-exercises", response_model=ProfileResponse)
def put_excluded_exercises(
    profile_id: uuid.UUID,
    payload: UpdateExcludedExercisesRequest,
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = get_profile_or_404(db, profile_id)
    update_profile_excluded_exercises(db, profile, payload.excluded_exercise_ids)
    db.commit()
    db.refresh(profile)
    return serialize_profile(db, profile, include_workout=True)
