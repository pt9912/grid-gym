"""create runs table

Revision ID: 0001_create_runs
Revises:
Create Date: 2026-05-17 00:00:00.000000

Welle 6c — `runs`-Tabelle fuer `PostgresRunRepository`. Felder
spiegeln `RunMetadata` aus `hexagon/core/domain/run.py`
(`GG-DATA-001`/`GG-SIM-003`/`GG-TERM-003`).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_runs"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("run_id", sa.Text(), primary_key=True),
        sa.Column("scenario_hash", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("tick_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.Text(), nullable=False),
        sa.Column("ended_at", sa.Text(), nullable=False),
        sa.Column("tool_version", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runs")
