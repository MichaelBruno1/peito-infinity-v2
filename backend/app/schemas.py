from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


GenderLiteral = Literal["MASCULINO", "FEMININO"]
FitnessLevelLiteral = Literal["INICIANTE", "INTERMEDIARIO", "AVANCADO"]
GoalLiteral = Literal["EMAGRECIMENTO", "HIPERTROFIA", "FORCA"]
ComplexityLiteral = Literal["BAIXA", "MEDIA", "ALTA"]


class ExerciseResponse(BaseModel):
    id: uuid.UUID
    group_order: int
    muscle_group: str
    popular_name: str
    primary_muscle: str
    secondary_muscles: str
    complexity: ComplexityLiteral
    efficiency_score: float

    model_config = ConfigDict(from_attributes=True)


class ExerciseGroupResponse(BaseModel):
    group_order: int
    muscle_group: str
    exercises: list[ExerciseResponse]


class ExerciseCatalogResponse(BaseModel):
    total: int
    groups: list[ExerciseGroupResponse]


class ProfileCreateUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    gender: GenderLiteral = "MASCULINO"
    weight_kg: float = Field(..., ge=25.0, le=300.0)
    height_cm: float = Field(..., ge=100.0, le=250.0)
    fitness_level: FitnessLevelLiteral
    goal: GoalLiteral
    available_time_minutes: int = Field(..., ge=20, le=240)
    days_per_week: int = Field(..., ge=1, le=7)

    @field_validator("name")
    @classmethod
    def validate_trimmed_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")
        return cleaned


class UpdateExcludedExercisesRequest(BaseModel):
    excluded_exercise_ids: list[uuid.UUID] = Field(default_factory=list)


class GenerateWorkoutRequest(BaseModel):
    excluded_exercise_ids: list[uuid.UUID] = Field(default_factory=list)


class PrescribedExerciseResponse(BaseModel):
    execution_order: int
    exercise_id: uuid.UUID
    popular_name: str
    muscle_group: str
    primary_muscle: str
    secondary_muscles: str
    complexity: ComplexityLiteral
    efficiency_score: float
    sets: int
    reps: str
    rest_seconds: int
    execution_notes: str | None = None


class WorkoutDayResponse(BaseModel):
    id: uuid.UUID
    day_number: int
    day_title: str
    target_muscles: str
    estimated_duration_minutes: int
    cardio_minutes: int
    cardio_display_text: str
    updated_at: datetime
    exercises: list[PrescribedExerciseResponse]


class WorkoutPlanResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    split_name: str
    specialist_notes: str | None = None
    days_per_week_snapshot: int
    time_minutes_snapshot: int
    goal_snapshot: GoalLiteral
    created_at: datetime
    updated_at: datetime
    days: list[WorkoutDayResponse]


class ProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    gender: GenderLiteral = "MASCULINO"
    weight_kg: float
    height_cm: float
    bmi: float
    fitness_level: FitnessLevelLiteral
    goal: GoalLiteral
    available_time_minutes: int
    days_per_week: int
    excluded_exercise_ids: list[uuid.UUID]
    has_active_workout: bool
    active_workout: WorkoutPlanResponse | None = None
    created_at: datetime
    updated_at: datetime


# Structured Output Schemas for LLM Specialist Agent
class LLMPrescribedExerciseSchema(BaseModel):
    execution_order: int = Field(..., ge=1)
    exercise_id: uuid.UUID
    sets: int = Field(..., ge=1, le=10)
    reps: str = Field(..., min_length=1, max_length=30)
    rest_seconds: int = Field(..., ge=15, le=300)
    execution_notes: str = Field(default="Manter controle técnico durante toda a amplitude.")


class LLMWorkoutDaySchema(BaseModel):
    day_number: int = Field(..., ge=1, le=7)
    day_title: str = Field(..., min_length=3, max_length=100)
    target_muscles: str = Field(..., min_length=3, max_length=150)
    estimated_duration_minutes: int = Field(..., ge=15, le=240)
    cardio_minutes: int = Field(..., ge=0, le=180)
    cardio_display_text: str = Field(..., max_length=60)
    exercises: list[LLMPrescribedExerciseSchema] = Field(..., min_length=1)

    @model_validator(mode="after")
    def enforce_cardio_display_format(self) -> LLMWorkoutDaySchema:
        # Regra Constitucional 4 / RF-11: Exibir apenas o tempo, ex: "40 min de cardio"
        self.cardio_display_text = f"{self.cardio_minutes} min de cardio"
        return self


class LLMWorkoutPlanSchema(BaseModel):
    split_name: str = Field(..., min_length=3, max_length=100)
    specialist_notes: str = Field(...)
    days: list[LLMWorkoutDaySchema] = Field(..., min_length=1, max_length=7)
