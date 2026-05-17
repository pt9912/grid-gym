"""RunRepositoryPort — Persistenz fuer Laufmetadaten
(`GG-AR-PORT-DRN-003`, `GG-PERSIST-003`/`009`).

Driven-Port-Vertrag fuer das Persistieren und Lesen von
`RunMetadata`-Eintraegen. Welle 6b liefert das Protocol und einen
`InMemoryRunRepository`-Test-Helper (`tests/`); Welle 6c bringt
die produktive Postgres-Implementation in
`adapters/driven/persistence_postgres/`.

Vertrag:
- `save(metadata)` legt einen neuen Lauf an. `RunAlreadyExistsError`
  bei doppeltem `run_id` — Aufrufer (FastAPI-Adapter) muss
  `uuid4` als Quelle nutzen.
- `get_by_id(run_id) -> RunMetadata` wirft `RunNotFoundError`,
  wenn der Lauf nicht persistiert ist.
- `exists(run_id) -> bool` als non-error Lookup-API.
"""

from __future__ import annotations

from typing import Protocol

from grid_gym.hexagon.core.domain.run import RunMetadata


class RunRepositoryPort(Protocol):
    """Driven-Port fuer Laufmetadaten-Persistenz (`GG-AR-PORT-DRN-003`).

    Implementationen MUESSEN deterministisch sein: ein nach `save`
    gespeichertes `RunMetadata` MUSS strukturell gleich aus
    `get_by_id` zurueckkommen (Frozen-Dataclass-Roundtrip).
    """

    def save(self, metadata: RunMetadata) -> None:
        """Persistiert einen Lauf.

        Wirft `RunAlreadyExistsError`, wenn `metadata.run_id`
        bereits vorhanden ist — Doppel-Inserts sind ein
        Programmierfehler (`run_id` ist UUID4-eindeutig).
        """
        ...  # pragma: no cover — Protocol-Stub

    def get_by_id(self, run_id: str) -> RunMetadata:
        """Liest die Laufmetadaten zu einem `run_id`.

        Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert
        ist.
        """
        ...  # pragma: no cover — Protocol-Stub

    def exists(self, run_id: str) -> bool:
        """Non-error-Lookup: gibt `True` zurueck, wenn der Lauf
        persistiert ist."""
        ...  # pragma: no cover — Protocol-Stub
