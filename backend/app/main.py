from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine, ensure_database_exists
from app.routers import exercises, health, profiles, workouts
from app.services.seed_service import seed_exercises_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seeded = seed_exercises_if_empty(db)
        if seeded > 0:
            logger.info("Peito Infinity startup seeded %d exercises.", seeded)
    yield


app = FastAPI(
    title="Peito Infinity API",
    description=(
        "API de montagem e gerenciamento inteligente de treinos de academia com Agente LLM "
        "Especialista, executada em rede doméstica e privada sem autenticação."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(exercises.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")
app.include_router(workouts.router, prefix="/api/v1")
