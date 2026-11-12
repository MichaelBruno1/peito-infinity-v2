from __future__ import annotations

import logging
import re
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DEFAULT_SEED_FILE, settings
from app.models import Exercise

logger = logging.getLogger(__name__)

GROUP_HEADER_PATTERN = re.compile(r"^##\s+(\d+)\.\s+(.+)$")
EFFICIENCY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*/\s*10")


def _parse_complexity(raw_complexity: str) -> str:
    text = raw_complexity.upper()
    if "BAIXA" in text:
        return "BAIXA"
    if "MÉDIA" in text or "MEDIA" in text:
        return "MEDIA"
    if "ALTA" in text:
        return "ALTA"
    raise ValueError(f"Complexidade desconhecida no seed: {raw_complexity!r}")


def _parse_efficiency(raw_efficiency: str) -> Decimal:
    match = EFFICIENCY_PATTERN.search(raw_efficiency)
    if not match:
        raise ValueError(f"Nota de eficiência inválida no seed: {raw_efficiency!r}")
    return Decimal(match.group(1))


def parse_exercises_from_markdown(markdown_content: str) -> list[dict]:
    """Faz o parse determinístico do arquivo Markdown de exercícios conforme spec 03."""
    parsed_exercises: list[dict] = []
    current_group_order: int | None = None
    current_muscle_group: str | None = None

    for raw_line in markdown_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        header_match = GROUP_HEADER_PATTERN.match(line)
        if header_match:
            current_group_order = int(header_match.group(1))
            current_muscle_group = header_match.group(2).strip()
            continue

        if current_group_order is None or current_muscle_group is None:
            continue

        if not line.startswith("|"):
            continue

        columns = [col.strip() for col in line.strip("|").split("|")]
        if len(columns) < 5:
            continue

        # Ignora cabeçalho e separador da tabela Markdown
        first_col_lower = columns[0].lower()
        if "nome popular" in first_col_lower or set(columns[0]).issubset({":", "-", " "}):
            continue

        popular_name = columns[0].replace("**", "").strip()
        primary_muscle = columns[1].replace("**", "").strip()
        secondary_muscles = columns[2].replace("*", "").strip()
        complexity = _parse_complexity(columns[3])
        efficiency_score = _parse_efficiency(columns[4])

        parsed_exercises.append(
            {
                "group_order": current_group_order,
                "muscle_group": current_muscle_group,
                "popular_name": popular_name,
                "primary_muscle": primary_muscle,
                "secondary_muscles": secondary_muscles,
                "complexity": complexity,
                "efficiency_score": efficiency_score,
            }
        )

    return parsed_exercises


def resolve_seed_file_path(custom_path: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if custom_path:
        candidates.append(Path(custom_path))
    if settings.seed_file_path:
        candidates.append(Path(settings.seed_file_path))
    candidates.append(DEFAULT_SEED_FILE)
    candidates.append(Path("/app/specs/data/guia-exercicios-seed.md"))

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        f"Arquivo de seed Markdown não encontrado. Caminhos verificados: {[str(p) for p in candidates]}"
    )


def seed_exercises_if_empty(db: Session, seed_file_path: str | Path | None = None) -> int:
    """
    Importa os dados do arquivo Markdown para a tabela `exercises` APENAS na primeira execução
    (quando a tabela está vazia). O banco passa a ser a única fonte de dados para os treinos.
    """
    existing_count = db.scalar(select(func.count()).select_from(Exercise)) or 0
    if existing_count > 0:
        logger.info(
            "Database already seeded with %d exercises. Skipping Markdown import.",
            existing_count,
        )
        return 0

    path = resolve_seed_file_path(seed_file_path)
    markdown_content = path.read_text(encoding="utf-8")
    parsed_items = parse_exercises_from_markdown(markdown_content)

    if not parsed_items:
        raise RuntimeError("Nenhum exercício extraído do arquivo Markdown de seed.")

    for item in parsed_items:
        db.add(Exercise(**item))

    db.commit()
    logger.info("Successfully seeded %d exercises from %s into database.", len(parsed_items), path)
    return len(parsed_items)
