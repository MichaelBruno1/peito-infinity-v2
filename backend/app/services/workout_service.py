from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Exercise,
    Profile,
    ProfileExcludedExercise,
    WorkoutDay,
    WorkoutDayExercise,
    WorkoutPlan,
)
from app.schemas import (
    PrescribedExerciseResponse,
    ProfileResponse,
    WorkoutDayResponse,
    WorkoutPlanResponse,
)
from app.services.llm_workout_agent import workout_llm_agent
from app.services.seed_service import seed_exercises_if_empty


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m * height_m), 2)


def serialize_workout_plan(plan: WorkoutPlan) -> WorkoutPlanResponse:
    days_resp: list[WorkoutDayResponse] = []
    sorted_days = sorted(plan.days, key=lambda d: d.day_number)

    for day in sorted_days:
        sorted_items = sorted(day.prescribed_exercises, key=lambda item: item.execution_order)
        exercises_resp: list[PrescribedExerciseResponse] = []
        for item in sorted_items:
            ex = item.exercise
            exercises_resp.append(
                PrescribedExerciseResponse(
                    execution_order=item.execution_order,
                    exercise_id=item.exercise_id,
                    popular_name=ex.popular_name,
                    muscle_group=ex.muscle_group,
                    primary_muscle=ex.primary_muscle,
                    secondary_muscles=ex.secondary_muscles,
                    complexity=ex.complexity,  # type: ignore[arg-type]
                    efficiency_score=float(ex.efficiency_score),
                    sets=item.sets,
                    reps=item.reps,
                    rest_seconds=item.rest_seconds,
                    execution_notes=item.execution_notes,
                )
            )

        days_resp.append(
            WorkoutDayResponse(
                id=day.id,
                day_number=day.day_number,
                day_title=day.day_title,
                target_muscles=day.target_muscles,
                estimated_duration_minutes=day.estimated_duration_minutes,
                cardio_minutes=day.cardio_minutes,
                cardio_display_text=day.cardio_display_text,
                updated_at=day.updated_at,
                exercises=exercises_resp,
            )
        )

    return WorkoutPlanResponse(
        id=plan.id,
        profile_id=plan.profile_id,
        split_name=plan.split_name,
        specialist_notes=plan.specialist_notes,
        days_per_week_snapshot=plan.days_per_week_snapshot,
        time_minutes_snapshot=plan.time_minutes_snapshot,
        goal_snapshot=plan.goal_snapshot,  # type: ignore[arg-type]
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        days=days_resp,
    )


def get_active_plan_for_profile(db: Session, profile_id: uuid.UUID) -> WorkoutPlan | None:
    stmt = (
        select(WorkoutPlan)
        .where(WorkoutPlan.profile_id == profile_id, WorkoutPlan.is_active.is_(True))
        .options(
            selectinload(WorkoutPlan.days)
            .selectinload(WorkoutDay.prescribed_exercises)
            .selectinload(WorkoutDayExercise.exercise)
        )
        .order_by(WorkoutPlan.created_at.desc())
    )
    return db.scalars(stmt).first()


def serialize_profile(db: Session, profile: Profile, include_workout: bool = True) -> ProfileResponse:
    excluded_ids = [link.exercise_id for link in profile.excluded_links]
    active_plan = get_active_plan_for_profile(db, profile.id)
    weight = float(profile.weight_kg)
    height = float(profile.height_cm)

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        gender=getattr(profile, "gender", None) or "MASCULINO",  # type: ignore[arg-type]
        weight_kg=weight,
        height_cm=height,
        bmi=compute_bmi(weight, height),
        fitness_level=profile.fitness_level,  # type: ignore[arg-type]
        goal=profile.goal,  # type: ignore[arg-type]
        available_time_minutes=profile.available_time_minutes,
        days_per_week=profile.days_per_week,
        excluded_exercise_ids=excluded_ids,
        has_active_workout=active_plan is not None,
        active_workout=serialize_workout_plan(active_plan) if (active_plan and include_workout) else None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def update_profile_excluded_exercises(
    db: Session,
    profile: Profile,
    excluded_exercise_ids: list[uuid.UUID],
) -> list[uuid.UUID]:
    unique_ids = list(dict.fromkeys(excluded_exercise_ids))

    if unique_ids:
        valid_ids = set(
            db.scalars(select(Exercise.id).where(Exercise.id.in_(unique_ids))).all()
        )
    else:
        valid_ids = set()

    db.execute(
        delete(ProfileExcludedExercise).where(
            ProfileExcludedExercise.profile_id == profile.id
        )
    )
    for ex_id in unique_ids:
        if ex_id in valid_ids:
            db.add(ProfileExcludedExercise(profile_id=profile.id, exercise_id=ex_id))

    db.flush()
    db.refresh(profile)
    return [link.exercise_id for link in profile.excluded_links]


def fetch_allowed_exercises(
    db: Session,
    excluded_exercise_ids: list[uuid.UUID],
) -> list[Exercise]:
    seed_exercises_if_empty(db)
    stmt = select(Exercise).order_by(Exercise.group_order, Exercise.efficiency_score.desc())
    if excluded_exercise_ids:
        stmt = stmt.where(Exercise.id.notin_(excluded_exercise_ids))

    allowed = list(db.scalars(stmt).all())
    if len(allowed) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INSUFFICIENT_ALLOWED_EXERCISES",
                "message": (
                    "Você excluiu exercícios demais. Mantenha ao menos 6 exercícios "
                    "permitidos na base para que o Agente Especialista possa montar o treino."
                ),
                "details": {"allowed_count": len(allowed)},
            },
        )
    return allowed


def generate_full_workout_for_profile(
    db: Session,
    profile: Profile,
    excluded_exercise_ids: list[uuid.UUID],
) -> WorkoutPlanResponse:
    persisted_excluded_ids = update_profile_excluded_exercises(
        db, profile, excluded_exercise_ids
    )
    allowed_exercises = fetch_allowed_exercises(db, persisted_excluded_ids)

    llm_plan = workout_llm_agent.generate_full_plan(
        profile=profile,
        allowed_exercises=allowed_exercises,
    )

    # Desativa planos ativos anteriores do perfil
    db.execute(
        update(WorkoutPlan)
        .where(WorkoutPlan.profile_id == profile.id, WorkoutPlan.is_active.is_(True))
        .values(is_active=False)
    )

    new_plan = WorkoutPlan(
        profile_id=profile.id,
        split_name=llm_plan.split_name,
        specialist_notes=llm_plan.specialist_notes,
        is_active=True,
        days_per_week_snapshot=profile.days_per_week,
        time_minutes_snapshot=profile.available_time_minutes,
        goal_snapshot=profile.goal,
    )
    db.add(new_plan)
    db.flush()

    for day_schema in llm_plan.days:
        day_model = WorkoutDay(
            workout_plan_id=new_plan.id,
            day_number=day_schema.day_number,
            day_title=day_schema.day_title,
            target_muscles=day_schema.target_muscles,
            estimated_duration_minutes=day_schema.estimated_duration_minutes,
            cardio_minutes=day_schema.cardio_minutes,
            cardio_display_text=day_schema.cardio_display_text,
        )
        db.add(day_model)
        db.flush()

        for ex_schema in day_schema.exercises:
            db.add(
                WorkoutDayExercise(
                    workout_day_id=day_model.id,
                    exercise_id=ex_schema.exercise_id,
                    execution_order=ex_schema.execution_order,
                    sets=ex_schema.sets,
                    reps=ex_schema.reps,
                    rest_seconds=ex_schema.rest_seconds,
                    execution_notes=ex_schema.execution_notes,
                )
            )

    db.commit()
    reloaded = get_active_plan_for_profile(db, profile.id)
    assert reloaded is not None
    return serialize_workout_plan(reloaded)


def regenerate_single_workout_day_for_profile(
    db: Session,
    profile: Profile,
    day_number: int,
    excluded_exercise_ids: list[uuid.UUID],
) -> WorkoutPlanResponse:
    active_plan = get_active_plan_for_profile(db, profile.id)
    if active_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "WORKOUT_PLAN_NOT_FOUND",
                "message": "Nenhum plano de treino ativo encontrado para este perfil. Gere um treino completo primeiro.",
            },
        )

    target_day = next((d for d in active_plan.days if d.day_number == day_number), None)
    if target_day is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "WORKOUT_DAY_NOT_FOUND",
                "message": f"Dia {day_number} não encontrado no plano de treino atual.",
            },
        )

    other_days = [d for d in active_plan.days if d.day_number != day_number]
    persisted_excluded_ids = update_profile_excluded_exercises(
        db, profile, excluded_exercise_ids
    )
    allowed_exercises = fetch_allowed_exercises(db, persisted_excluded_ids)

    new_day_schema = workout_llm_agent.regenerate_single_day(
        profile=profile,
        day_number=day_number,
        current_day=target_day,
        other_days=other_days,
        allowed_exercises=allowed_exercises,
    )

    now = datetime.now(timezone.utc)
    target_day.day_title = new_day_schema.day_title
    target_day.target_muscles = new_day_schema.target_muscles
    target_day.estimated_duration_minutes = new_day_schema.estimated_duration_minutes
    target_day.cardio_minutes = new_day_schema.cardio_minutes
    target_day.cardio_display_text = new_day_schema.cardio_display_text
    target_day.updated_at = now
    active_plan.updated_at = now

    # Remove apenas os exercícios prescritos do dia regenerado, mantendo os demais dias intactos
    db.execute(
        delete(WorkoutDayExercise).where(
            WorkoutDayExercise.workout_day_id == target_day.id
        )
    )
    db.flush()

    for ex_schema in new_day_schema.exercises:
        db.add(
            WorkoutDayExercise(
                workout_day_id=target_day.id,
                exercise_id=ex_schema.exercise_id,
                execution_order=ex_schema.execution_order,
                sets=ex_schema.sets,
                reps=ex_schema.reps,
                rest_seconds=ex_schema.rest_seconds,
                execution_notes=ex_schema.execution_notes,
            )
        )

    db.commit()
    db.expire_all()
    reloaded = get_active_plan_for_profile(db, profile.id)
    assert reloaded is not None
    return serialize_workout_plan(reloaded)
