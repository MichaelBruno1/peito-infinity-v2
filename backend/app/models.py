from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("weight_kg >= 25.0 AND weight_kg <= 300.0", name="ck_profiles_weight_kg"),
        CheckConstraint("height_cm >= 100.0 AND height_cm <= 250.0", name="ck_profiles_height_cm"),
        CheckConstraint(
            "fitness_level IN ('INICIANTE', 'INTERMEDIARIO', 'AVANCADO')",
            name="ck_profiles_fitness_level",
        ),
        CheckConstraint(
            "goal IN ('EMAGRECIMENTO', 'HIPERTROFIA', 'FORCA')",
            name="ck_profiles_goal",
        ),
        CheckConstraint(
            "available_time_minutes >= 20 AND available_time_minutes <= 240",
            name="ck_profiles_available_time_minutes",
        ),
        CheckConstraint(
            "days_per_week >= 1 AND days_per_week <= 7",
            name="ck_profiles_days_per_week",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    fitness_level: Mapped[str] = mapped_column(String(20), nullable=False)
    goal: Mapped[str] = mapped_column(String(20), nullable=False)
    available_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    excluded_links: Mapped[list[ProfileExcludedExercise]] = relationship(
        "ProfileExcludedExercise",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    workout_plans: Mapped[list[WorkoutPlan]] = relationship(
        "WorkoutPlan",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(WorkoutPlan.created_at)",
    )


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("group_order >= 1 AND group_order <= 9", name="ck_exercises_group_order"),
        CheckConstraint("complexity IN ('BAIXA', 'MEDIA', 'ALTA')", name="ck_exercises_complexity"),
        CheckConstraint(
            "efficiency_score >= 0.0 AND efficiency_score <= 10.0",
            name="ck_exercises_efficiency_score",
        ),
        Index("idx_exercises_muscle_group", "muscle_group"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_order: Mapped[int] = mapped_column(Integer, nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(60), nullable=False)
    popular_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    primary_muscle: Mapped[str] = mapped_column(String(150), nullable=False)
    secondary_muscles: Mapped[str] = mapped_column(String(200), nullable=False)
    complexity: Mapped[str] = mapped_column(String(15), nullable=False)
    efficiency_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProfileExcludedExercise(Base):
    __tablename__ = "profile_excluded_exercises"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
    )
    excluded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    profile: Mapped[Profile] = relationship("Profile", back_populates="excluded_links")
    exercise: Mapped[Exercise] = relationship("Exercise")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    split_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialist_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    days_per_week_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    time_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    profile: Mapped[Profile] = relationship("Profile", back_populates="workout_plans")
    days: Mapped[list[WorkoutDay]] = relationship(
        "WorkoutDay",
        back_populates="workout_plan",
        cascade="all, delete-orphan",
        order_by="WorkoutDay.day_number",
    )


class WorkoutDay(Base):
    __tablename__ = "workout_days"
    __table_args__ = (
        CheckConstraint("day_number >= 1 AND day_number <= 7", name="ck_workout_days_day_number"),
        CheckConstraint("estimated_duration_minutes > 0", name="ck_workout_days_estimated_duration"),
        CheckConstraint("cardio_minutes >= 0", name="ck_workout_days_cardio_minutes"),
        UniqueConstraint("workout_plan_id", "day_number", name="uq_workout_days_plan_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_title: Mapped[str] = mapped_column(String(100), nullable=False)
    target_muscles: Mapped[str] = mapped_column(String(150), nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cardio_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cardio_display_text: Mapped[str] = mapped_column(String(60), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    workout_plan: Mapped[WorkoutPlan] = relationship("WorkoutPlan", back_populates="days")
    prescribed_exercises: Mapped[list[WorkoutDayExercise]] = relationship(
        "WorkoutDayExercise",
        back_populates="workout_day",
        cascade="all, delete-orphan",
        order_by="WorkoutDayExercise.execution_order",
    )


class WorkoutDayExercise(Base):
    __tablename__ = "workout_day_exercises"
    __table_args__ = (
        CheckConstraint("execution_order >= 1", name="ck_workout_day_exercises_order"),
        CheckConstraint("sets >= 1 AND sets <= 10", name="ck_workout_day_exercises_sets"),
        CheckConstraint(
            "rest_seconds >= 15 AND rest_seconds <= 300",
            name="ck_workout_day_exercises_rest",
        ),
        UniqueConstraint(
            "workout_day_id",
            "execution_order",
            name="uq_workout_day_exercises_day_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_days.id", ondelete="CASCADE"),
        nullable=False,
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        nullable=False,
    )
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[str] = mapped_column(String(30), nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    workout_day: Mapped[WorkoutDay] = relationship("WorkoutDay", back_populates="prescribed_exercises")
    exercise: Mapped[Exercise] = relationship("Exercise")
