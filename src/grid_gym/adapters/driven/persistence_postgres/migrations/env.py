"""Alembic environment fuer den Postgres-Adapter (M1 Welle 6c).

Welle 6c liefert manuelle SQL-Migrationen ohne SQLAlchemy-Models —
`target_metadata = None`, `--autogenerate` ist daher nicht
verfuegbar. Migrationen werden bewusst handgeschrieben in
`versions/`.

Die `sqlalchemy.url`-Konfiguration kommt aus `alembic.ini` ODER aus
einer Override (Integration-Tests setzen das per
`config.set_main_option`). Wenn weder Env-Var noch Override
gesetzt sind, faellt das mit `psycopg.OperationalError` — der
Integration-Test darf das nicht zulassen.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

target_metadata = None
"""Keine SQLAlchemy-Models — Migrationen sind handgeschrieben."""


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (`alembic upgrade --sql`).

    Erzeugt SQL-Skripte, ohne eine Engine zu attachen. Wird nicht
    von den Welle-6c-Integration-Tests genutzt, aber von alembic
    selbst beim `--sql`-Mode benoetigt.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode mit aktiver Engine.

    Der Integration-Test-Runner ruft typischerweise
    `alembic.command.upgrade(...)`-Programmatic; diese Funktion
    ist der entsprechende Online-Entry.
    """
    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
