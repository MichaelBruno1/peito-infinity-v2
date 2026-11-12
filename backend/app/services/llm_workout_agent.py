from __future__ import annotations

import json
import logging
import random
import re
import uuid
from typing import Any, Sequence

import httpx
from openai import OpenAI

import app.config as app_config
from app.models import Exercise, Profile, WorkoutDay
from app.schemas import (
    LLMPrescribedExerciseSchema,
    LLMWorkoutDaySchema,
    LLMWorkoutPlanSchema,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Agente Especialista em Treinamento de Força, Hipertrofia e Condicionamento Físico do sistema Peito Infinity.
Sua função é montar treinos altamente eficientes, seguros e personalizados com base nos dados do perfil do usuário.

REGRAS INEGOCIÁVEIS:
1. FONTE ÚNICA DE EXERCÍCIOS: Escolha apenas exercícios presentes na lista `allowed_exercises` fornecida pelo usuário, referenciando o campo inteiro `code` de cada exercício escolhido.
2. AGRUPAMENTO POR GRUPO MUSCULAR (MAIOR -> MENOR, SEM INTERCALAR):
   - Todos os exercícios de um mesmo grupo muscular devem ficar juntos em sequência contínua (nunca intercale grupos como Peito -> Core -> Peito).
   - Ordem dos blocos musculares na sessão:
     1º Grandes Grupos (1: Peitoral, 2: Costas, 3: Quadríceps, 4: Posterior de Coxa e Glúteos)
     2º Grupos Médios (5: Ombros e Trapézio)
     3º Grupos Menores (6: Bíceps e Antebraço, 7: Tríceps, 8: Panturrilhas e Tibial)
     4º Core / Finalizador (9: Abdômen e Core)
3. ORDEM BIOMECÂNICA DENTRO DE CADA GRUPO MUSCULAR: Dentro do bloco de cada músculo, comece pelos exercícios de complexidade ALTA, depois MEDIA, e finalize aquele músculo com os isoladores de complexidade BAIXA e alta eficiência.
4. ANTI-REDUNDÂNCIA: Não repita o mesmo exercício nem coloque dois exercícios com exatamente o mesmo padrão biomecânico no mesmo dia.
5. REGRA DO CARDIO: Informe apenas o tempo em minutos em `cardio_minutes` (ex: 30 ou 40) e em `cardio_display_text` informe exatamente "{X} min de cardio" (exemplo: "40 min de cardio").
6. LIMITE DE TEMPO: A duração total estimada (`estimated_duration_minutes`) somando musculação e cardio não pode ultrapassar `available_time_minutes` do perfil.
7. FORMATO DE SAÍDA: Responda EXCLUSIVAMENTE com um objeto JSON válido seguindo exatamente o formato solicitado, sem blocos markdown extras.
"""


SPLIT_TEMPLATES: dict[int, tuple[str, list[tuple[str, str, list[int]]]]] = {
    1: (
        "Full Body Completo (1 Dia/Semana)",
        [
            (
                "Dia 1 — Full Body (Corpo Inteiro)",
                "Peitoral, Costas, Quadríceps, Posterior, Ombros e Core",
                [1, 2, 3, 4, 5, 6, 7, 9],
            ),
        ],
    ),
    2: (
        "Full Body A/B (2 Dias/Semana)",
        [
            (
                "Dia 1 — Full Body A (Ênfase Anterior e Empurrar)",
                "Peitoral, Costas, Quadríceps, Ombros, Tríceps e Abdômen",
                [1, 2, 3, 5, 7, 9],
            ),
            (
                "Dia 2 — Full Body B (Ênfase Posterior e Puxar)",
                "Costas, Peitoral, Posterior e Glúteos, Ombros, Bíceps e Panturrilhas",
                [1, 2, 4, 5, 6, 8],
            ),
        ],
    ),
    3: (
        "ABC — Push / Pull / Legs (3 Dias/Semana)",
        [
            (
                "Dia 1 — Treino A: Push (Peito, Ombros e Tríceps)",
                "Peitoral, Deltoides e Tríceps",
                [1, 1, 5, 5, 7, 7, 9],
            ),
            (
                "Dia 2 — Treino B: Pull (Costas, Trapézio e Bíceps)",
                "Dorsais, Parte Superior das Costas, Deltoide Posterior e Bíceps",
                [2, 2, 2, 5, 6, 6, 9],
            ),
            (
                "Dia 3 — Treino C: Legs (Pernas Completas e Panturrilhas)",
                "Quadríceps, Posterior de Coxa, Glúteos e Panturrilhas",
                [3, 3, 3, 4, 4, 8, 8],
            ),
        ],
    ),
    4: (
        "Upper / Lower 2x (4 Dias/Semana)",
        [
            (
                "Dia 1 — Upper A (Superiores: Foco Peitoral e Costas)",
                "Peitoral, Costas, Ombros, Bíceps e Tríceps",
                [1, 1, 2, 2, 5, 6, 7],
            ),
            (
                "Dia 2 — Lower A (Inferiores: Foco Quadríceps e Panturrilhas)",
                "Quadríceps, Glúteos, Posterior de Coxa, Panturrilhas e Core",
                [3, 3, 3, 4, 8, 9],
            ),
            (
                "Dia 3 — Upper B (Superiores: Foco Ombros, Costas e Braços)",
                "Peitoral, Costas, Ombros, Bíceps e Tríceps",
                [1, 2, 2, 5, 5, 6, 7],
            ),
            (
                "Dia 4 — Lower B (Inferiores: Foco Posterior, Glúteos e Abdômen)",
                "Quadríceps, Posterior de Coxa, Glúteos, Panturrilhas e Abdômen",
                [3, 4, 4, 4, 8, 9],
            ),
        ],
    ),
    5: (
        "Upper / Lower + Push / Pull / Legs (5 Dias/Semana)",
        [
            (
                "Dia 1 — Upper (Força e Base de Superiores)",
                "Peitoral, Costas, Ombros, Bíceps e Tríceps",
                [1, 1, 2, 2, 5, 6, 7],
            ),
            (
                "Dia 2 — Lower (Força e Base de Inferiores)",
                "Quadríceps, Posterior de Coxa, Glúteos e Panturrilhas",
                [3, 3, 4, 4, 8, 9],
            ),
            (
                "Dia 3 — Push (Peito, Ombros e Tríceps)",
                "Peitoral, Deltoides e Tríceps",
                [1, 1, 5, 5, 7, 7],
            ),
            (
                "Dia 4 — Pull (Costas, Deltoide Posterior e Bíceps)",
                "Dorsais, Costas Superiores, Trapézio e Bíceps",
                [2, 2, 2, 5, 6, 6],
            ),
            (
                "Dia 5 — Legs (Quadríceps, Posterior, Glúteos e Core)",
                "Quadríceps, Isquiotibiais, Glúteos, Panturrilhas e Abdômen",
                [3, 3, 4, 4, 8, 9],
            ),
        ],
    ),
    6: (
        "ABC 2x — Push / Pull / Legs (6 Dias/Semana)",
        [
            (
                "Dia 1 — Push A (Peito, Ombros e Tríceps)",
                "Peitoral, Deltoide Anterior/Lateral e Tríceps",
                [1, 1, 5, 5, 7, 7],
            ),
            (
                "Dia 2 — Pull A (Costas, Trapézio e Bíceps)",
                "Latíssimo do Dorso, Romboides, Deltoide Posterior e Bíceps",
                [2, 2, 2, 5, 6, 6],
            ),
            (
                "Dia 3 — Legs A (Foco Quadríceps, Glúteos e Panturrilhas)",
                "Quadríceps, Posterior, Glúteos, Panturrilhas e Abdômen",
                [3, 3, 3, 4, 8, 9],
            ),
            (
                "Dia 4 — Push B (Variação de Ângulos: Peito, Ombros e Tríceps)",
                "Peitoral Superior/Inferior, Deltoides e Tríceps",
                [1, 1, 5, 5, 7, 7],
            ),
            (
                "Dia 5 — Pull B (Variação de Densidade: Costas e Bíceps)",
                "Parte Superior das Costas, Dorsal, Bíceps e Antebraço",
                [2, 2, 2, 5, 6, 6],
            ),
            (
                "Dia 6 — Legs B (Foco Cadeia Posterior, Glúteos e Core)",
                "Quadríceps, Isquiotibiais, Glúteos, Panturrilhas e Core",
                [3, 4, 4, 4, 8, 9],
            ),
        ],
    ),
    7: (
        "Push / Pull / Legs 2x + Core & Condicionamento (7 Dias/Semana)",
        [
            (
                "Dia 1 — Push A (Peito, Ombros e Tríceps)",
                "Peitoral, Deltoides e Tríceps",
                [1, 1, 5, 5, 7, 7],
            ),
            (
                "Dia 2 — Pull A (Costas, Trapézio e Bíceps)",
                "Dorsais, Romboides e Bíceps",
                [2, 2, 2, 5, 6, 6],
            ),
            (
                "Dia 3 — Legs A (Foco Quadríceps e Panturrilhas)",
                "Quadríceps, Glúteos, Posterior e Panturrilhas",
                [3, 3, 3, 4, 8, 8],
            ),
            (
                "Dia 4 — Push B (Peito, Ombros e Tríceps)",
                "Peitoral Clavicular, Deltoide Lateral e Tríceps",
                [1, 1, 5, 5, 7, 7],
            ),
            (
                "Dia 5 — Pull B (Costas, Deltoide Posterior e Bíceps)",
                "Costas Completas, Deltoide Posterior, Bíceps e Antebraço",
                [2, 2, 2, 5, 6, 6],
            ),
            (
                "Dia 6 — Legs B (Foco Posterior de Coxa e Glúteos)",
                "Quadríceps, Isquiotibiais, Glúteos e Panturrilhas",
                [3, 4, 4, 4, 8, 8],
            ),
            (
                "Dia 7 — Core, Estabilização Lombar e Condicionamento",
                "Panturrilhas/Tibial, Abdômen Completo, Oblíquos e Lombar",
                [8, 8, 9, 9, 9],
            ),
        ],
    ),
}


EXTERNAL_LLM_PROVIDERS = {
    "lm_studio",
    "lmstudio",
    "local",
    "openai_compatible",
    "openai",
    "gemini",
    "ollama",
}


def _biomechanical_pattern_key(popular_name: str) -> str:
    lower = popular_name.lower()
    patterns = [
        ("supino_reto", ["supino reto", "supino máquina"]),
        ("supino_inclinado", ["supino inclinado"]),
        ("crucifixo_peito", ["crucifixo", "peck deck"]),
        ("puxada_vertical", ["barra fixa", "puxada alta"]),
        (
            "remada_horizontal",
            [
                "remada curvada",
                "remada cavalinho",
                "remada baixa",
                "remada máquina",
                "remada pendlay",
            ],
        ),
        (
            "agachamento_base",
            [
                "agachamento livre",
                "agachamento hack",
                "agachamento no smith",
                "agachamento pendular",
                "agachamento frontal",
            ],
        ),
        (
            "hip_hinge",
            [
                "stiff",
                "levantamento terra romeno",
                "levantamento terra tradicional",
                "bom dia",
            ],
        ),
        ("flexora_joelho", ["cadeira flexora", "mesa flexora", "flexora em pé"]),
        ("desenvolvimento_ombro", ["desenvolvimento"]),
        ("elevacao_lateral", ["elevação lateral"]),
        ("crucifixo_inverso", ["crucifixo inverso", "face pull"]),
        ("rosca_biceps_base", ["rosca direta", "rosca alternada"]),
        ("triceps_polia", ["tríceps pulley", "tríceps corda"]),
        ("panturrilha_pe", ["panturrilha em pé", "panturrilha no leg press"]),
    ]
    for key, keywords in patterns:
        if any(k in lower for k in keywords):
            return key
    return re.sub(r"\s+", "_", lower[:25])


def _calculate_cardio_and_exercise_budget(
    goal: str,
    fitness_level: str,
    available_time_minutes: int,
) -> tuple[int, int, int, str, int]:
    if goal == "EMAGRECIMENTO":
        if available_time_minutes >= 80:
            cardio_minutes = 40
        elif available_time_minutes >= 60:
            cardio_minutes = 30
        elif available_time_minutes >= 45:
            cardio_minutes = 20
        else:
            cardio_minutes = max(10, available_time_minutes // 3)
        reps_range = "12 a 15"
        rest_seconds = 60
        sets_per_exercise = 3 if fitness_level != "INICIANTE" else 2
    elif goal == "FORCA":
        if available_time_minutes >= 75:
            cardio_minutes = 15
        else:
            cardio_minutes = 10
        reps_range = "4 a 6"
        rest_seconds = 150
        sets_per_exercise = 4 if fitness_level != "INICIANTE" else 3
    else:  # HIPERTROFIA
        if available_time_minutes >= 85:
            cardio_minutes = 25
        elif available_time_minutes >= 60:
            cardio_minutes = 15
        else:
            cardio_minutes = 10
        reps_range = "8 a 12"
        rest_seconds = 90
        sets_per_exercise = 3 if fitness_level == "INICIANTE" else 4

    remaining_lifting_minutes = max(15, available_time_minutes - cardio_minutes)
    minutes_per_exercise = sets_per_exercise * (1.2 + (rest_seconds / 60.0))
    target_exercise_count = int(remaining_lifting_minutes // minutes_per_exercise)
    target_exercise_count = max(3, min(8, target_exercise_count))

    return cardio_minutes, target_exercise_count, sets_per_exercise, reps_range, rest_seconds


def _muscle_size_tier(group_order: int) -> int:
    """
    Hierarquia anatômica de tamanho do grupo muscular:
    1º Grandes Grupos: 1 (Peitoral), 2 (Costas), 3 (Quadríceps), 4 (Posterior e Glúteos)
    2º Grupos Médios: 5 (Ombros e Trapézio)
    3º Grupos Menores: 6 (Bíceps e Antebraço), 7 (Tríceps), 8 (Panturrilhas e Tibial)
    4º Core / Estabilizadores: 9 (Abdômen e Core)
    """
    if group_order in (1, 2, 3, 4):
        return 1
    if group_order == 5:
        return 2
    if group_order in (6, 7, 8):
        return 3
    return 4


def _exercise_sort_key_for_session(ex: Exercise) -> tuple[int, int, int, float]:
    """
    Regra de Ordenação por Blocos de Grupo Muscular (Maior -> Menor) e Complexidade Interna:
    1. Tier de tamanho do grupo muscular (Grandes -> Médios -> Menores -> Core).
    2. Código do grupo muscular (`group_order`), mantendo todos os exercícios do mesmo
       músculo juntos em um único bloco contínuo (sem intercalar grupos!).
    3. Complexidade biomecânica dentro daquele grupo muscular: ALTA (0) -> MEDIA (1) -> BAIXA (2).
    4. Maior nota de eficiência primeiro (-efficiency_score).
    """
    tier = _muscle_size_tier(ex.group_order)
    if ex.complexity == "ALTA":
        comp_rank = 0
    elif ex.complexity == "MEDIA":
        comp_rank = 1
    else:
        comp_rank = 2
    return (tier, ex.group_order, comp_rank, -float(ex.efficiency_score))


def _execution_note_for(
    exercise: Exercise,
    goal: str,
    is_last_of_group: bool,
) -> str:
    short_group = exercise.muscle_group.split("(")[0].strip()
    if exercise.complexity == "ALTA":
        return f"Multiarticular prioritário de {short_group}: focar em estabilidade e técnica rigorosa."
    if is_last_of_group and exercise.complexity == "BAIXA":
        return f"Finalizador seguro de {short_group}: levar a última série próxima à falha concêntrica."
    if goal == "FORCA":
        return "Progressão de carga controlada mantendo explosão na fase concêntrica."
    if goal == "EMAGRECIMENTO":
        return "Manter intervalo de descanso rigoroso para preservar alta densidade metabólica."
    return "Controlar a fase excêntrica (2 a 3 segundos) valorizando o alongamento sob tensão."


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extrai o objeto JSON mesmo quando o LLM local envolve a resposta em blocos markdown."""
    cleaned = raw_text.strip()
    # Remove blocos de pensamento <think>...</think> caso presentes no texto
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    return json.loads(cleaned)


class WorkoutLLMAgent:
    """
    Agente Especialista em Montar Treinos do Peito Infinity.
    Suporta provedores LLM locais e em nuvem (LM Studio, Ollama, OpenAI, Gemini)
    e motor especialista biomecânico de fallback.
    """

    def generate_full_plan(
        self,
        profile: Profile,
        allowed_exercises: Sequence[Exercise],
    ) -> LLMWorkoutPlanSchema:
        if not allowed_exercises:
            raise ValueError("Nenhum exercício permitido disponível para montar o treino.")

        cfg = app_config.get_runtime_llm_config()
        provider = cfg["provider"]

        if provider in EXTERNAL_LLM_PROVIDERS:
            try:
                logger.info(
                    "Invoking LLM Agent (provider=%s, model=%s, base_url=%s) for full workout plan...",
                    provider,
                    cfg["model"],
                    cfg["base_url"],
                )
                plan = self._call_external_llm_full_plan(profile, allowed_exercises, cfg)
                validated = self._validate_and_sanitize_plan(plan, profile, allowed_exercises)
                logger.info(
                    "LLM Agent (provider=%s, model=%s) successfully generated full workout plan!",
                    provider,
                    cfg["model"],
                )
                return validated
            except Exception as exc:
                logger.warning(
                    "External/Local LLM call failed (provider=%s, model=%s, error=%s). "
                    "Using built-in Specialist Engine fallback.",
                    provider,
                    cfg["model"],
                    exc,
                )

        plan = self._build_specialist_full_plan(profile, allowed_exercises)
        return self._validate_and_sanitize_plan(plan, profile, allowed_exercises)

    def regenerate_single_day(
        self,
        profile: Profile,
        day_number: int,
        current_day: WorkoutDay | None,
        other_days: Sequence[WorkoutDay],
        allowed_exercises: Sequence[Exercise],
    ) -> LLMWorkoutDaySchema:
        if not allowed_exercises:
            raise ValueError("Nenhum exercício permitido disponível para regenerar o treino do dia.")

        previous_day_exercise_ids: set[uuid.UUID] = set()
        if current_day is not None:
            previous_day_exercise_ids = {
                item.exercise_id for item in current_day.prescribed_exercises
            }

        cfg = app_config.get_runtime_llm_config()
        provider = cfg["provider"]

        if provider in EXTERNAL_LLM_PROVIDERS:
            try:
                logger.info(
                    "Invoking LLM Agent (provider=%s, model=%s, base_url=%s) to regenerate Day %d...",
                    provider,
                    cfg["model"],
                    cfg["base_url"],
                    day_number,
                )
                day_schema = self._call_external_llm_single_day(
                    profile, day_number, current_day, other_days, allowed_exercises, cfg
                )
                validated = self._validate_and_sanitize_day(day_schema, profile, allowed_exercises)
                logger.info(
                    "LLM Agent (provider=%s, model=%s) successfully regenerated Day %d!",
                    provider,
                    cfg["model"],
                    day_number,
                )
                return validated
            except Exception as exc:
                logger.warning(
                    "External/Local LLM single-day call failed (provider=%s, model=%s, error=%s). "
                    "Using built-in Specialist Engine.",
                    provider,
                    cfg["model"],
                    exc,
                )

        day_schema = self._build_specialist_single_day(
            profile=profile,
            day_number=day_number,
            current_day=current_day,
            allowed_exercises=allowed_exercises,
            avoid_exercise_ids=previous_day_exercise_ids,
        )
        return self._validate_and_sanitize_day(day_schema, profile, allowed_exercises)

    def _build_specialist_full_plan(
        self,
        profile: Profile,
        allowed_exercises: Sequence[Exercise],
    ) -> LLMWorkoutPlanSchema:
        days_count = profile.days_per_week
        split_name, day_templates = SPLIT_TEMPLATES[days_count]

        goal_labels = {
            "EMAGRECIMENTO": "Emagrecimento e Densidade Metabólica",
            "HIPERTROFIA": "Hipertrofia Muscular",
            "FORCA": "Treino de Força Pura",
        }
        level_labels = {
            "INICIANTE": "Iniciante",
            "INTERMEDIARIO": "Intermediário",
            "AVANCADO": "Avançado",
        }

        used_recently_across_week: set[uuid.UUID] = set()
        generated_days: list[LLMWorkoutDaySchema] = []

        for idx, (day_title, target_muscles, group_slots) in enumerate(day_templates, start=1):
            day_schema = self._compose_day_from_template(
                profile=profile,
                day_number=idx,
                day_title=day_title,
                target_muscles=target_muscles,
                group_slots=group_slots,
                allowed_exercises=allowed_exercises,
                prefer_avoid_ids=used_recently_across_week,
            )
            for ex in day_schema.exercises:
                used_recently_across_week.add(ex.exercise_id)
            generated_days.append(day_schema)

        specialist_notes = (
            f"Planejamento {split_name} otimizado pelo Agente Especialista para "
            f"{level_labels.get(profile.fitness_level, profile.fitness_level)} com foco em "
            f"{goal_labels.get(profile.goal, profile.goal)}. "
            f"Sessões dimensionadas para até {profile.available_time_minutes} min, "
            f"ordenadas do maior para o menor grupo muscular e por complexidade biomecânica."
        )

        return LLMWorkoutPlanSchema(
            split_name=f"{split_name} — {goal_labels.get(profile.goal, profile.goal)}",
            specialist_notes=specialist_notes,
            days=generated_days,
        )

    def _build_specialist_single_day(
        self,
        profile: Profile,
        day_number: int,
        current_day: WorkoutDay | None,
        allowed_exercises: Sequence[Exercise],
        avoid_exercise_ids: set[uuid.UUID],
    ) -> LLMWorkoutDaySchema:
        days_count = profile.days_per_week
        _, day_templates = SPLIT_TEMPLATES.get(days_count, SPLIT_TEMPLATES[3])
        template_idx = min(max(day_number - 1, 0), len(day_templates) - 1)
        default_title, default_targets, group_slots = day_templates[template_idx]

        day_title = current_day.day_title if current_day else default_title
        target_muscles = current_day.target_muscles if current_day else default_targets

        return self._compose_day_from_template(
            profile=profile,
            day_number=day_number,
            day_title=day_title,
            target_muscles=target_muscles,
            group_slots=group_slots,
            allowed_exercises=allowed_exercises,
            prefer_avoid_ids=avoid_exercise_ids,
        )

    def _compose_day_from_template(
        self,
        profile: Profile,
        day_number: int,
        day_title: str,
        target_muscles: str,
        group_slots: list[int],
        allowed_exercises: Sequence[Exercise],
        prefer_avoid_ids: set[uuid.UUID],
    ) -> LLMWorkoutDaySchema:
        cardio_minutes, target_count, sets_per_ex, reps_range, rest_sec = (
            _calculate_cardio_and_exercise_budget(
                goal=profile.goal,
                fitness_level=profile.fitness_level,
                available_time_minutes=profile.available_time_minutes,
            )
        )

        by_group: dict[int, list[Exercise]] = {}
        for ex in allowed_exercises:
            by_group.setdefault(ex.group_order, []).append(ex)

        effective_slots = list(group_slots[:target_count])
        while len(effective_slots) < target_count:
            effective_slots.append(group_slots[len(effective_slots) % len(group_slots)])

        selected_exercises: list[Exercise] = []
        selected_ids: set[uuid.UUID] = set()
        used_patterns: set[str] = set()
        high_complexity_count = 0
        max_high_complexity = 1 if profile.fitness_level == "INICIANTE" else 3

        for slot_group in effective_slots:
            candidates = list(by_group.get(slot_group, []))
            if not candidates:
                candidates = list(allowed_exercises)

            candidates = [c for c in candidates if c.id not in selected_ids]
            if not candidates:
                continue

            if high_complexity_count >= max_high_complexity:
                non_high = [c for c in candidates if c.complexity != "ALTA"]
                if non_high:
                    candidates = non_high

            non_redundant = [
                c
                for c in candidates
                if _biomechanical_pattern_key(c.popular_name) not in used_patterns
            ]
            if non_redundant:
                candidates = non_redundant

            fresh_candidates = [c for c in candidates if c.id not in prefer_avoid_ids]
            pool = fresh_candidates if fresh_candidates else candidates

            pool.sort(key=lambda x: float(x.efficiency_score), reverse=True)
            top_window = pool[: min(3, len(pool))]
            chosen = random.choice(top_window)

            selected_exercises.append(chosen)
            selected_ids.add(chosen.id)
            used_patterns.add(_biomechanical_pattern_key(chosen.popular_name))
            if chosen.complexity == "ALTA":
                high_complexity_count += 1

        if not selected_exercises and allowed_exercises:
            selected_exercises.append(allowed_exercises[0])

        selected_exercises.sort(key=_exercise_sort_key_for_session)

        prescribed_list: list[LLMPrescribedExerciseSchema] = []
        total_ex = len(selected_exercises)
        for idx, ex in enumerate(selected_exercises):
            order_idx = idx + 1
            is_last_of_group = (
                idx == total_ex - 1
                or selected_exercises[idx + 1].group_order != ex.group_order
            )
            ex_reps = reps_range
            if ex.group_order in (8, 9) and profile.goal == "FORCA":
                ex_reps = "10 a 15"
            prescribed_list.append(
                LLMPrescribedExerciseSchema(
                    execution_order=order_idx,
                    exercise_id=ex.id,
                    sets=sets_per_ex,
                    reps=ex_reps,
                    rest_seconds=rest_sec,
                    execution_notes=_execution_note_for(ex, profile.goal, is_last_of_group),
                )
            )

        lifting_minutes = int(
            round(len(prescribed_list) * sets_per_ex * (1.1 + (rest_sec / 60.0)))
        )
        estimated_total = min(
            profile.available_time_minutes,
            max(15, lifting_minutes + cardio_minutes),
        )

        return LLMWorkoutDaySchema(
            day_number=day_number,
            day_title=day_title,
            target_muscles=target_muscles,
            estimated_duration_minutes=estimated_total,
            cardio_minutes=cardio_minutes,
            cardio_display_text=f"{cardio_minutes} min de cardio",
            exercises=prescribed_list,
        )

    def _build_compact_catalog(
        self, allowed_exercises: Sequence[Exercise]
    ) -> tuple[str, dict[int, Exercise], dict[str, Exercise]]:
        lines: list[str] = ["code|grupo|nome|complexidade|eficiencia"]
        code_to_ex: dict[int, Exercise] = {}
        lookup_by_str: dict[str, Exercise] = {}

        for idx, ex in enumerate(allowed_exercises, start=1):
            code_to_ex[idx] = ex
            lookup_by_str[str(ex.id).lower()] = ex
            lookup_by_str[ex.popular_name.strip().lower()] = ex
            short_group = ex.muscle_group.split("(")[0].strip()
            lines.append(
                f"{idx}|{ex.group_order}:{short_group}|{ex.popular_name}|{ex.complexity}|{float(ex.efficiency_score)}"
            )
        return "\n".join(lines), code_to_ex, lookup_by_str

    def _resolve_exercise_from_llm_item(
        self,
        raw_item: dict[str, Any],
        code_to_ex: dict[int, Exercise],
        lookup_by_str: dict[str, Exercise],
    ) -> Exercise | None:
        code_val = raw_item.get("code") or raw_item.get("exercise_code")
        if code_val is not None:
            try:
                ex = code_to_ex.get(int(code_val))
                if ex is not None:
                    return ex
            except (ValueError, TypeError):
                pass

        for key in ("exercise_id", "id", "popular_name", "name"):
            val = raw_item.get(key)
            if isinstance(val, int) and val in code_to_ex:
                return code_to_ex[val]
            if isinstance(val, str) and val.strip():
                cleaned = val.strip().lower()
                if cleaned in lookup_by_str:
                    return lookup_by_str[cleaned]
                if cleaned.isdigit() and int(cleaned) in code_to_ex:
                    return code_to_ex[int(cleaned)]
        return None

    def _parse_llm_day_dict(
        self,
        raw_day: dict[str, Any],
        fallback_day_number: int,
        profile: Profile,
        code_to_ex: dict[int, Exercise],
        lookup_by_str: dict[str, Exercise],
    ) -> LLMWorkoutDaySchema:
        cardio_default, _, sets_default, reps_default, rest_default = (
            _calculate_cardio_and_exercise_budget(
                goal=profile.goal,
                fitness_level=profile.fitness_level,
                available_time_minutes=profile.available_time_minutes,
            )
        )
        day_number = int(raw_day.get("day_number") or fallback_day_number)
        day_title = str(raw_day.get("day_title") or f"Dia {day_number}").strip()[:100]
        target_muscles = str(raw_day.get("target_muscles") or "Musculação Geral").strip()[:150]
        cardio_minutes = int(raw_day.get("cardio_minutes", cardio_default))
        cardio_minutes = max(0, min(180, cardio_minutes))
        est_duration = int(
            raw_day.get("estimated_duration_minutes") or profile.available_time_minutes
        )
        est_duration = max(15, min(profile.available_time_minutes, est_duration))

        raw_exercises = raw_day.get("exercises") or []
        prescribed: list[LLMPrescribedExerciseSchema] = []
        for idx, raw_ex in enumerate(raw_exercises, start=1):
            if not isinstance(raw_ex, dict):
                continue
            resolved_ex = self._resolve_exercise_from_llm_item(
                raw_ex, code_to_ex, lookup_by_str
            )
            if resolved_ex is None:
                continue
            sets_val = max(1, min(10, int(raw_ex.get("sets") or sets_default)))
            reps_val = str(raw_ex.get("reps") or reps_default).strip()[:30]
            rest_val = max(15, min(300, int(raw_ex.get("rest_seconds") or rest_default)))
            notes_val = str(
                raw_ex.get("execution_notes")
                or _execution_note_for(resolved_ex, profile.goal, False)
            ).strip()[:255]

            prescribed.append(
                LLMPrescribedExerciseSchema(
                    execution_order=idx,
                    exercise_id=resolved_ex.id,
                    sets=sets_val,
                    reps=reps_val,
                    rest_seconds=rest_val,
                    execution_notes=notes_val,
                )
            )

        return LLMWorkoutDaySchema(
            day_number=day_number,
            day_title=day_title,
            target_muscles=target_muscles,
            estimated_duration_minutes=est_duration,
            cardio_minutes=cardio_minutes,
            cardio_display_text=f"{cardio_minutes} min de cardio",
            exercises=prescribed,
        )

    def _call_external_llm_full_plan(
        self,
        profile: Profile,
        allowed_exercises: Sequence[Exercise],
        cfg: dict[str, str],
    ) -> LLMWorkoutPlanSchema:
        compact_catalog, code_to_ex, lookup_by_str = self._build_compact_catalog(
            allowed_exercises
        )
        cardio_rec, ex_count_rec, sets_rec, reps_rec, rest_rec = (
            _calculate_cardio_and_exercise_budget(
                profile.goal, profile.fitness_level, profile.available_time_minutes
            )
        )
        split_suggestion, _ = SPLIT_TEMPLATES[profile.days_per_week]

        user_prompt = (
            f"Monte um plano de treino semanal completo ({profile.days_per_week} dias) em JSON.\n"
            f"Perfil: Nome={profile.name}, Peso={profile.weight_kg}kg, Altura={profile.height_cm}cm, "
            f"Nível={profile.fitness_level}, Objetivo={profile.goal}, "
            f"Tempo disponível por dia={profile.available_time_minutes} min, "
            f"Dias na semana={profile.days_per_week} (Sugestão de divisão: {split_suggestion}).\n"
            f"Recomendação por dia: cerca de {ex_count_rec} exercícios ({sets_rec} séries de '{reps_rec}', "
            f"descanso {rest_rec}s) + {cardio_rec} min de cardio ('{cardio_rec} min de cardio').\n\n"
            f"Catálogo permitido (`allowed_exercises`):\n"
            f"{compact_catalog}\n\n"
            "Retorne APENAS um JSON válido com a estrutura exata abaixo:\n"
            "{\n"
            '  "split_name": "Nome da Divisão",\n'
            '  "specialist_notes": "Explicação técnica resumida",\n'
            '  "days": [\n'
            "    {\n"
            '      "day_number": 1,\n'
            '      "day_title": "Dia 1 — Título",\n'
            '      "target_muscles": "Músculos do dia",\n'
            f'      "estimated_duration_minutes": {profile.available_time_minutes},\n'
            f'      "cardio_minutes": {cardio_rec},\n'
            f'      "cardio_display_text": "{cardio_rec} min de cardio",\n'
            '      "exercises": [\n'
            f'        {{"code": 1, "sets": {sets_rec}, "reps": "{reps_rec}", "rest_seconds": {rest_rec}, "execution_notes": "Dica curta"}}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        raw_json = self._invoke_llm_json(user_prompt, cfg)
        raw_days = raw_json.get("days") or []
        parsed_days = [
            self._parse_llm_day_dict(d, idx, profile, code_to_ex, lookup_by_str)
            for idx, d in enumerate(raw_days, start=1)
            if isinstance(d, dict)
        ]

        return LLMWorkoutPlanSchema(
            split_name=str(raw_json.get("split_name") or split_suggestion).strip()[:100],
            specialist_notes=str(
                raw_json.get("specialist_notes")
                or f"Treino personalizado gerado pelo modelo LLM ({cfg['model']})."
            ).strip(),
            days=parsed_days,
        )

    def _call_external_llm_single_day(
        self,
        profile: Profile,
        day_number: int,
        current_day: WorkoutDay | None,
        other_days: Sequence[WorkoutDay],
        allowed_exercises: Sequence[Exercise],
        cfg: dict[str, str],
    ) -> LLMWorkoutDaySchema:
        compact_catalog, code_to_ex, lookup_by_str = self._build_compact_catalog(
            allowed_exercises
        )
        cardio_rec, ex_count_rec, sets_rec, reps_rec, rest_rec = (
            _calculate_cardio_and_exercise_budget(
                profile.goal, profile.fitness_level, profile.available_time_minutes
            )
        )

        prev_names = [
            item.exercise.popular_name
            for item in (current_day.prescribed_exercises if current_day else [])
            if item.exercise is not None
        ]
        other_summary = [
            f"Dia {d.day_number}: {d.day_title} ({d.target_muscles})" for d in other_days
        ]

        user_prompt = (
            f"Gere um NOVO treino APENAS para o Dia {day_number} em JSON.\n"
            f"Perfil: Nome={profile.name}, Nível={profile.fitness_level}, Objetivo={profile.goal}, "
            f"Tempo disponível={profile.available_time_minutes} min.\n"
            f"Título atual do Dia {day_number}: '{current_day.day_title if current_day else f'Dia {day_number}'}'.\n"
            f"Músculos foco do Dia {day_number}: '{current_day.target_muscles if current_day else 'Geral'}'.\n"
            f"Exercícios anteriores deste dia (procure variar os exercícios mantendo os mesmos grupos musculares): {prev_names}.\n"
            f"Outros dias da semana: {other_summary}.\n"
            f"Recomendação: cerca de {ex_count_rec} exercícios ({sets_rec} séries de '{reps_rec}', "
            f"descanso {rest_rec}s) + {cardio_rec} min de cardio ('{cardio_rec} min de cardio').\n\n"
            f"Catálogo permitido (`allowed_exercises`):\n"
            f"{compact_catalog}\n\n"
            "Retorne APENAS um JSON válido com a estrutura exata abaixo:\n"
            "{\n"
            f'  "day_number": {day_number},\n'
            f'  "day_title": "{current_day.day_title if current_day else f"Dia {day_number}"}",\n'
            f'  "target_muscles": "{current_day.target_muscles if current_day else "Músculos do dia"}",\n'
            f'  "estimated_duration_minutes": {profile.available_time_minutes},\n'
            f'  "cardio_minutes": {cardio_rec},\n'
            f'  "cardio_display_text": "{cardio_rec} min de cardio",\n'
            '  "exercises": [\n'
            f'    {{"code": 1, "sets": {sets_rec}, "reps": "{reps_rec}", "rest_seconds": {rest_rec}, "execution_notes": "Dica curta"}}\n'
            "  ]\n"
            "}"
        )

        raw_json = self._invoke_llm_json(user_prompt, cfg)
        if "days" in raw_json and isinstance(raw_json["days"], list) and raw_json["days"]:
            raw_json = raw_json["days"][0]

        return self._parse_llm_day_dict(
            raw_json, day_number, profile, code_to_ex, lookup_by_str
        )

    def _invoke_llm_json(self, user_prompt: str, cfg: dict[str, str]) -> dict[str, Any]:
        provider = cfg["provider"]
        model = cfg["model"]
        api_key = cfg["api_key"] or "local"
        base_url = cfg["base_url"].rstrip("/")

        if provider == "ollama":
            url = f"{base_url}/api/chat"
            resp = httpx.post(
                url,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": "json",
                    "think": False,
                    "stream": False,
                },
                timeout=180.0,
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            return _extract_json_object(content)

        if provider in ("lm_studio", "lmstudio", "local", "openai_compatible"):
            v1_base = base_url if base_url.endswith("/v1") else f"{base_url}/v1"
            url = f"{v1_base}/chat/completions"
            resp = httpx.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "reasoning_effort": "none",
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                },
                timeout=180.0,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return _extract_json_object(content)

        # Provedores OpenAI / Gemini
        openai_base_url = None
        if provider == "gemini":
            openai_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif base_url and "11434" not in base_url:
            openai_base_url = base_url if base_url.endswith("/v1") else f"{base_url}/v1"

        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=180.0)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        content = completion.choices[0].message.content or ""
        return _extract_json_object(content)

    def _validate_and_sanitize_plan(
        self,
        plan: LLMWorkoutPlanSchema,
        profile: Profile,
        allowed_exercises: Sequence[Exercise],
    ) -> LLMWorkoutPlanSchema:
        if len(plan.days) != profile.days_per_week:
            raise ValueError(
                f"Número de dias gerados ({len(plan.days)}) difere de days_per_week ({profile.days_per_week})."
            )
        sanitized_days = [
            self._validate_and_sanitize_day(day, profile, allowed_exercises)
            for day in plan.days
        ]
        plan.days = sanitized_days
        return plan

    def _validate_and_sanitize_day(
        self,
        day: LLMWorkoutDaySchema,
        profile: Profile,
        allowed_exercises: Sequence[Exercise],
    ) -> LLMWorkoutDaySchema:
        allowed_map = {ex.id: ex for ex in allowed_exercises}
        valid_exercises: list[LLMPrescribedExerciseSchema] = []
        seen_ids: set[uuid.UUID] = set()

        for item in day.exercises:
            if item.exercise_id in allowed_map and item.exercise_id not in seen_ids:
                seen_ids.add(item.exercise_id)
                valid_exercises.append(item)

        if not valid_exercises:
            raise ValueError("Dia gerado não contém exercícios válidos da lista permitida.")

        # Garante determinismo de ordenação: Grupo Muscular (Maior -> Menor, sem intercalar)
        # e Complexidade Interna (ALTA -> MEDIA -> BAIXA) dentro de cada grupo muscular.
        valid_exercises.sort(
            key=lambda item: _exercise_sort_key_for_session(allowed_map[item.exercise_id])
        )

        for idx, item in enumerate(valid_exercises, start=1):
            item.execution_order = idx

        day.exercises = valid_exercises
        day.estimated_duration_minutes = min(
            profile.available_time_minutes,
            max(15, day.estimated_duration_minutes),
        )
        day.cardio_display_text = f"{day.cardio_minutes} min de cardio"
        return day


workout_llm_agent = WorkoutLLMAgent()
