"""Postgres-Driven-Adapter (`GG-PERSIST-001`/`003`/`009`, M1 Welle 6c).

Liefert die produktive `RunRepositoryPort`-Implementation auf
`psycopg`-Basis. Welle 6b hatte den Port + InMemory-Fake; Welle 6c
bringt die Postgres-Persistenz und das alembic-Schema.

Modul-Re-Export: `PostgresRunRepository` ist die einzige
oeffentliche API dieses Pakets.
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_postgres.run_repository import (
    PostgresRunRepository,
)

__all__ = ["PostgresRunRepository"]
