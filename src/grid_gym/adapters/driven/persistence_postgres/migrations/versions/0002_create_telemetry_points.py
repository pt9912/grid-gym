"""create telemetry_points table

Revision ID: 0002_create_telemetry_points
Revises: 0001_create_runs
Create Date: 2026-06-08 00:00:00.000000

M7 Welle 1a (ADR 0047) — `telemetry_points`-Tabelle fuer
`PostgresTelemetrySinkAdapter` (`GG-PERSIST-001`). Spalten
spiegeln `TelemetryPoint` aus `hexagon/core/domain/telemetry.py`
(`GG-DATA-001`).

Append-only: ein Surrogat-`id` (Identity) ist Primary Key —
`(run_id, simulation_time, sequence)` ist NICHT eindeutig, weil
`sequence` per-device-per-tick vergeben wird (zwei Geraete teilen
`sequence` bei gleicher `simulation_time`). Die deterministische
`emitted_telemetry`-Reihenfolge (Device-Major x Per-Device-
`sequence`) wird ueber die Insertion-Reihenfolge (= aufsteigender
`id`) reproduziert; `read_ordered` sortiert daher `ORDER BY id`.
`value` ist `TEXT` (kanonische `str(Decimal)`-Serialisierung,
byte-stabil; NICHT `NUMERIC` wegen Scale-Normalisierung —
ADR 0047 §2.2/§2.4).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_telemetry_points"
down_revision: str | None = "0001_create_runs"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "telemetry_points",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("run_id", sa.Text(), nullable=False),
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("simulation_time", sa.BigInteger(), nullable=False),
        sa.Column("device_id", sa.Text(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        # `value` als TEXT (kanonisches `str(Decimal)`), NICHT NUMERIC
        # — Byte-Stabilitaet fuer den Welle-1b-Replay-Diff (ADR 0047 §2.4).
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("quality", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
    )
    # Lese-Index fuer `read_ordered(run_id)` (`WHERE run_id ORDER BY id`).
    op.create_index(
        "ix_telemetry_points_run_id_id",
        "telemetry_points",
        ["run_id", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_telemetry_points_run_id_id", table_name="telemetry_points")
    op.drop_table("telemetry_points")
