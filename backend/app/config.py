from pathlib import Path
from dotenv import dotenv_values
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_FILE = DEFAULT_REPO_ROOT / "specs" / "data" / "guia-exercicios-seed.md"


class Settings(BaseSettings):
    db_host: str = "postgres"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "peito_infinity"
    db_port: int = 5432
    database_url: str = ""

    seed_file_path: str = str(DEFAULT_SEED_FILE)
    llm_provider: str = "specialist_engine"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    ollama_base_url: str = "http://host.docker.internal:11434"
    llm_base_url: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "/app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return self


settings = Settings()


def get_runtime_llm_config() -> dict[str, str]:
    """
    Lê dinamicamente as configurações de LLM do arquivo .env (se existir)
    combinadas com as variáveis de ambiente atuais, permitindo alterar o .env
    sem precisar reconstruir a imagem.
    """
    current = Settings()
    file_vals: dict[str, str] = {}
    for candidate in (Path("/app/.env"), Path(".env"), DEFAULT_REPO_ROOT / ".env"):
        if candidate.is_file():
            raw = dotenv_values(candidate)
            for k, v in raw.items():
                if v is not None:
                    file_vals[k.upper()] = v.strip()
            break

    provider = file_vals.get("LLM_PROVIDER", current.llm_provider).strip().lower()
    model = file_vals.get("LLM_MODEL", current.llm_model).strip()
    api_key = file_vals.get("LLM_API_KEY", current.llm_api_key).strip()
    base_url = (
        file_vals.get("LLM_BASE_URL")
        or file_vals.get("OLLAMA_BASE_URL")
        or current.llm_base_url
        or current.ollama_base_url
    ).strip()

    if Path("/.dockerenv").exists() and base_url:
        base_url = base_url.replace("://127.0.0.1", "://host.docker.internal").replace(
            "://localhost", "://host.docker.internal"
        )

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
    }
