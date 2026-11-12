from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exercise, Profile

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    exercises_count = db.scalar(select(func.count()).select_from(Exercise)) or 0
    profiles_count = db.scalar(select(func.count()).select_from(Profile)) or 0
    return {
        "status": "ok",
        "service": "Peito Infinity API",
        "database_connected": True,
        "exercises_count": exercises_count,
        "profiles_count": profiles_count,
    }
