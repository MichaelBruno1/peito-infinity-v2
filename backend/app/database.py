from collections.abc import Generator
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_database_exists() -> None:
    """
    Garante que o banco de dados (`DB_NAME`, ex: `peito_infinity`) exista na instância
    PostgreSQL compartilhada antes de executar as migrações e o seed inicial.
    """
    if settings.database_url.startswith("sqlite"):
        return

    try:
        url = make_url(settings.database_url)
        target_db = url.database
        if not target_db:
            return

        admin_url = url.set(database="postgres")
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": target_db},
            ).scalar()
            if not exists:
                logger.info("Creating database '%s' on external PostgreSQL server...", target_db)
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
        admin_engine.dispose()
    except Exception as exc:
        logger.warning("Could not verify/auto-create database '%s': %s", settings.db_name, exc)


def ensure_schema_columns() -> None:
    """
    Garante que novas colunas adicionadas ao modelo (como `profiles.gender`)
    existam em bancos PostgreSQL/SQLite já criados anteriormente.
    """
    try:
        inspector = inspect(engine)
        if "profiles" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("profiles")}
            if "gender" not in existing_cols:
                logger.info("Adding missing column 'gender' to 'profiles' table...")
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE profiles "
                            "ADD COLUMN gender VARCHAR(15) NOT NULL DEFAULT 'MASCULINO'"
                        )
                    )
    except Exception as exc:
        logger.warning("Could not verify/update schema columns: %s", exc)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
