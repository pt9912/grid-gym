"""add replay_of column to runs

Revision ID: 0003_add_replay_of
Revises: 0002_create_telemetry_points
Create Date: 2026-06-17 00:00:00.000000

Slice 039 (ADR 0068) — nullable `replay_of`-Referenz-Spalte fuer die
persistente, auditierbare Replay-Bindung am Lauf. `NULL` = regulaerer
Lauf (kein Replay). Spiegelt `RunMetadata.replay_of` aus
`hexagon/core/domain/run.py`. Additive Migration (kein Backfill noetig —
Bestands-Zeilen sind regulaere Laeufe → `NULL`).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_replay_of"
down_revision: str | None = "0002_create_telemetry_points"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("replay_of", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "replay_of")
