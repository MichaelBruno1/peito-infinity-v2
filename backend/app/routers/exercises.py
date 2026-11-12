from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exercise
from app.schemas import (
    ComplexityLiteral,
    ExerciseCatalogResponse,
    ExerciseGroupResponse,
    ExerciseResponse,
)

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get("", response_model=ExerciseCatalogResponse)
def list_exercises(
    muscle_group: str | None = Query(default=None),
    complexity: ComplexityLiteral | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ExerciseCatalogResponse:
    stmt = select(Exercise).order_by(Exercise.group_order, Exercise.efficiency_score.desc(), Exercise.popular_name)

    if muscle_group:
        stmt = stmt.where(Exercise.muscle_group.ilike(f"%{muscle_group.strip()}%"))
    if complexity:
        stmt = stmt.where(Exercise.complexity == complexity)
    if search and search.strip():
        q = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Exercise.popular_name.ilike(q),
                Exercise.primary_muscle.ilike(q),
                Exercise.secondary_muscles.ilike(q),
                Exercise.muscle_group.ilike(q),
            )
        )

    exercises = list(db.scalars(stmt).all())

    groups_map: dict[int, ExerciseGroupResponse] = {}
    for ex in exercises:
        if ex.group_order not in groups_map:
            groups_map[ex.group_order] = ExerciseGroupResponse(
                group_order=ex.group_order,
                muscle_group=ex.muscle_group,
                exercises=[],
            )
        groups_map[ex.group_order].exercises.append(
            ExerciseResponse(
                id=ex.id,
                group_order=ex.group_order,
                muscle_group=ex.muscle_group,
                popular_name=ex.popular_name,
                primary_muscle=ex.primary_muscle,
                secondary_muscles=ex.secondary_muscles,
                complexity=ex.complexity,  # type: ignore[arg-type]
                efficiency_score=float(ex.efficiency_score),
            )
        )

    sorted_groups = [groups_map[k] for k in sorted(groups_map.keys())]
    return ExerciseCatalogResponse(total=len(exercises), groups=sorted_groups)
