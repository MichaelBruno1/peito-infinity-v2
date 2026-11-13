from __future__ import annotations

import os
import re
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.config as app_config
from app.database import Base, get_db
from app.main import app
from app.models import Exercise
from app.services.seed_service import seed_exercises_if_empty


def create_test_client():
    app_config.get_runtime_llm_config = lambda: {
        "provider": "specialist_engine",
        "model": "specialist",
        "api_key": "",
        "base_url": "",
    }
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        seed_exercises_if_empty(db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def test_seed_service_imports_94_exercises_across_9_groups_and_is_idempotent():
    _, SessionMaker = create_test_client()
    with SessionMaker() as db:
        total = db.scalar(select(func.count()).select_from(Exercise))
        assert total == 94

        distinct_groups = db.scalar(select(func.count(func.distinct(Exercise.group_order))))
        assert distinct_groups == 9

        # Segunda execução deve ser idempotente (retornar 0 e manter 94)
        second_run = seed_exercises_if_empty(db)
        assert second_run == 0
        assert db.scalar(select(func.count()).select_from(Exercise)) == 94


def test_exercises_catalog_endpoint_and_filters():
    client, _ = create_test_client()

    resp = client.get("/api/v1/exercises")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 94
    assert len(data["groups"]) == 9

    # Filtro por complexidade
    resp_low = client.get("/api/v1/exercises", params={"complexity": "BAIXA"})
    assert resp_low.status_code == 200
    for grp in resp_low.json()["groups"]:
        for ex in grp["exercises"]:
            assert ex["complexity"] == "BAIXA"

    # Filtro por busca
    resp_search = client.get("/api/v1/exercises", params={"search": "Supino"})
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] >= 5


def test_profile_crud_and_editability_without_authentication():
    client, _ = create_test_client()

    create_payload = {
        "name": "Carlos Silva",
        "gender": "MASCULINO",
        "weight_kg": 88.0,
        "height_cm": 180.0,
        "fitness_level": "INTERMEDIARIO",
        "goal": "EMAGRECIMENTO",
        "available_time_minutes": 90,
        "days_per_week": 4,
    }
    resp = client.post("/api/v1/profiles", json=create_payload)
    assert resp.status_code == 201
    profile = resp.json()
    profile_id = profile["id"]
    assert profile["name"] == "Carlos Silva"
    assert profile["gender"] == "MASCULINO"
    assert profile["goal"] == "EMAGRECIMENTO"
    assert profile["available_time_minutes"] == 90
    assert profile["days_per_week"] == 4

    # Edição de perfil
    update_payload = {
        "name": "Carlos Silva Editado",
        "gender": "FEMININO",
        "weight_kg": 84.0,
        "height_cm": 180.0,
        "fitness_level": "AVANCADO",
        "goal": "HIPERTROFIA",
        "available_time_minutes": 60,
        "days_per_week": 5,
    }
    upd_resp = client.put(f"/api/v1/profiles/{profile_id}", json=update_payload)
    assert upd_resp.status_code == 200
    updated = upd_resp.json()
    assert updated["name"] == "Carlos Silva Editado"
    assert updated["gender"] == "FEMININO"
    assert updated["weight_kg"] == 84.0
    assert updated["fitness_level"] == "AVANCADO"
    assert updated["goal"] == "HIPERTROFIA"
    assert updated["available_time_minutes"] == 60
    assert updated["days_per_week"] == 5


def test_workout_generation_respects_exclusions_cardio_format_and_single_day_regeneration():
    client, _ = create_test_client()

    # Cria perfil com objetivo EMAGRECIMENTO e 90 min (espera-se "40 min de cardio")
    profile_resp = client.post(
        "/api/v1/profiles",
        json={
            "name": "Marina Costa",
            "gender": "FEMININO",
            "weight_kg": 68.5,
            "height_cm": 165.0,
            "fitness_level": "INTERMEDIARIO",
            "goal": "EMAGRECIMENTO",
            "available_time_minutes": 90,
            "days_per_week": 4,
        },
    )
    profile_id = profile_resp.json()["id"]
    assert profile_resp.json()["gender"] == "FEMININO"

    # Obtém catálogo de exercícios e seleciona 10 exercícios para EXCLUIR
    catalog = client.get("/api/v1/exercises").json()
    excluded_ids = [
        ex["id"]
        for grp in catalog["groups"][:3]
        for ex in grp["exercises"][:3]
    ]
    assert len(excluded_ids) == 9

    # Gera treino completo do zero
    gen_resp = client.post(
        f"/api/v1/profiles/{profile_id}/workouts/generate-full",
        json={"excluded_exercise_ids": excluded_ids},
    )
    assert gen_resp.status_code == 201
    plan = gen_resp.json()
    assert len(plan["days"]) == 4

    cardio_regex = re.compile(r"^\d+ min de cardio$")
    complexity_rank = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
    group_tier_by_name = {
        "Peitoral (Peito)": 1,
        "Costas (Dorsais e Parte Superior das Costas)": 1,
        "Quadríceps (Parte Anterior da Coxa)": 1,
        "Posterior de Coxa (Isquiotibiais) e Glúteos": 1,
        "Ombros (Deltoides) e Trapézio": 2,
        "Bíceps e Antebraço": 3,
        "Tríceps": 3,
        "Panturrilhas e Tibial": 3,
        "Abdômen e Core": 4,
    }

    for day in plan["days"]:
        assert cardio_regex.match(day["cardio_display_text"]), day["cardio_display_text"]
        assert day["cardio_display_text"] == "40 min de cardio"
        assert day["estimated_duration_minutes"] <= 90

        seen_finished_groups: set[str] = set()
        prev_group: str | None = None
        prev_tier: int = 0
        prev_comp_rank_in_group: int = -1

        for ex in day["exercises"]:
            assert ex["exercise_id"] not in excluded_ids
            mg = ex["muscle_group"]
            tier = group_tier_by_name[mg]
            comp = complexity_rank[ex["complexity"]]

            if mg != prev_group:
                # Garante que os grupos musculares não se intercalam (ex: Peito -> Core -> Peito)
                assert mg not in seen_finished_groups, (
                    f"Grupo muscular {mg} foi intercalado indevidamente no dia {day['day_number']}"
                )
                if prev_group is not None:
                    seen_finished_groups.add(prev_group)
                # Garante que grupos maiores vêm antes de grupos menores
                assert tier >= prev_tier, (
                    f"Grupo de tier {tier} ({mg}) veio após tier {prev_tier} ({prev_group})"
                )
                prev_group = mg
                prev_tier = tier
                prev_comp_rank_in_group = comp
            else:
                # Dentro do mesmo grupo muscular, garante ALTA -> MEDIA -> BAIXA
                assert comp >= prev_comp_rank_in_group, (
                    f"Complexidade fora de ordem dentro do grupo {mg}"
                )
                prev_comp_rank_in_group = comp

    # Captura snapshot dos dias 1, 3 e 4 antes de regenerar apenas o Dia 2
    day_1_before = plan["days"][0]["exercises"]
    day_2_before = plan["days"][1]["exercises"]
    day_3_before = plan["days"][2]["exercises"]
    day_4_before = plan["days"][3]["exercises"]

    # Adiciona os exercícios atuais do Dia 2 na lista de exclusão e regenera APENAS o Dia 2
    extra_excluded = excluded_ids + [day_2_before[0]["exercise_id"]]
    regen_resp = client.post(
        f"/api/v1/profiles/{profile_id}/workouts/days/2/regenerate",
        json={"excluded_exercise_ids": extra_excluded},
    )
    assert regen_resp.status_code == 200
    updated_plan = regen_resp.json()
    assert len(updated_plan["days"]) == 4

    # Verifica que Dias 1, 3 e 4 permaneceram 100% intactos
    assert updated_plan["days"][0]["exercises"] == day_1_before
    assert updated_plan["days"][2]["exercises"] == day_3_before
    assert updated_plan["days"][3]["exercises"] == day_4_before

    # Verifica que o Dia 2 foi atualizado e não contém o exercício recém-excluído
    day_2_after_ids = [e["exercise_id"] for e in updated_plan["days"][1]["exercises"]]
    assert day_2_before[0]["exercise_id"] not in day_2_after_ids
    assert cardio_regex.match(updated_plan["days"][1]["cardio_display_text"])
