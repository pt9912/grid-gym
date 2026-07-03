"""add GG-TERM full equality-matrix columns to runs

Revision ID: 0004_add_gg_term_full_fields
Revises: 0003_add_replay_of
Create Date: 2026-07-03 00:00:00.000000

Slice 038 (ADR 0073 §2.7) — die vier `GG-TERM-002/003`-Vollfelder
als Spalten der `runs`-Tabelle, gespiegelt aus
`RunMetadata` (`hexagon/core/domain/run.py`). Differenzierter
Backfill per Server-Default:

- `platform_arch`/`enabled_adapters`/`config_hash` = ``''``
  (ehrlich-fehlend: der Wert von Bestandslaeufen ist unbekannt;
  der Replay-Preflight rejected fehlende Werte fail-closed,
  ADR 0073 §2.6).
- `sim_start_time` = ``0`` (fachlich wahr: alle bisherigen Laeufe
  starteten bei Simulationszeit 0, ADR 0073 §2.2).

`enabled_adapters` ist der komma-separierte kanonische String
(ADR 0073 §2.3; Namensraum ``[a-z0-9_]+`` schliesst Kommata aus).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0004_add_gg_term_full_fields"
down_revision: str | None = "0003_add_replay_of"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("platform_arch", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "runs",
        sa.Column("enabled_adapters", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "runs",
        sa.Column("sim_start_time", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "runs",
        sa.Column("config_hash", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("runs", "config_hash")
    op.drop_column("runs", "sim_start_time")
    op.drop_column("runs", "enabled_adapters")
    op.drop_column("runs", "platform_arch")
