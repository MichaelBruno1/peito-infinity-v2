"""Add gender column to profiles

Revision ID: 0002_add_profile_gender
Revises: 0001_initial_schema
Create Date: 2026-11-12 23:47:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_profile_gender"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "profiles" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("profiles")}
        if "gender" not in columns:
            op.add_column(
                "profiles",
                sa.Column(
                    "gender",
                    sa.String(length=15),
                    server_default="MASCULINO",
                    nullable=False,
                ),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "profiles" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("profiles")}
        if "gender" in columns:
            op.drop_column("profiles", "gender")
