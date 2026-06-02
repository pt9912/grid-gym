"""RunRepositoryPort — Persistenz fuer Laufmetadaten + Lifecycle-Status
(`GG-AR-PORT-DRN-003`, `GG-PERSIST-003`/`009`).

Driven-Port-Vertrag fuer das Persistieren und Lesen von
`RunMetadata`-Eintraegen + dem orthogonalen `RunStatus`-Lifecycle-
State (M5 Welle 4a, ADR 0039 Decision 12). Welle 6b liefert das
Protocol und einen `InMemoryRunRepository`-Test-Helper (`tests/`);
Welle 6c bringt die produktive Postgres-Implementation in
`adapters/driven/persistence_postgres/`; M5 Welle 4a erweitert
beide Implementationen um `update_status`/`get_status` (Postgres-
Status-Spalte wartet auf M3-Welle-6c).

Vertrag (Welle-1):

- `save(metadata)` legt einen neuen Lauf an. `RunAlreadyExistsError`
  bei doppeltem `run_id` — Aufrufer (FastAPI-Adapter) muss
  `uuid4` als Quelle nutzen. Implementationen MUESSEN den Run mit
  Initial-Status ``"pending"`` versehen (Default-Lifecycle-Start
  per ADR 0039 §2.1).
- `get_by_id(run_id) -> RunMetadata` wirft `RunNotFoundError`,
  wenn der Lauf nicht persistiert ist.
- `exists(run_id) -> bool` als non-error Lookup-API.

Vertrag (Welle-4a-Extension):

- `update_status(run_id, status)` setzt den Lifecycle-Status.
  Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert ist
  (konsistent mit `get_by_id`).
- `get_status(run_id) -> RunStatus` liest den Lifecycle-Status.
  Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert ist.
"""

from __future__ import annotations

from typing import Protocol

from grid_gym.hexagon.core.domain.run import RunMetadata, RunStatus


class RunRepositoryPort(Protocol):
    """Driven-Port fuer Laufmetadaten-Persistenz (`GG-AR-PORT-DRN-003`).

    Implementationen MUESSEN deterministisch sein: ein nach `save`
    gespeichertes `RunMetadata` MUSS strukturell gleich aus
    `get_by_id` zurueckkommen (Frozen-Dataclass-Roundtrip). Der
    `RunStatus`-Lifecycle-State lebt orthogonal — ein `save`
    setzt ihn auf ``"pending"``; nachfolgende ``update_status``-
    Aufrufe persistieren die State-Transitions aus ADR 0039
    Decision 13 (TickLoop-Control-Surface).
    """

    def save(self, metadata: RunMetadata) -> None:
        """Persistiert einen Lauf mit Initial-Status ``"pending"``.

        Wirft `RunAlreadyExistsError`, wenn `metadata.run_id`
        bereits vorhanden ist — Doppel-Inserts sind ein
        Programmierfehler (`run_id` ist UUID4-eindeutig).
        """
        ...

    def get_by_id(self, run_id: str) -> RunMetadata:
        """Liest die Laufmetadaten zu einem `run_id`.

        Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert
        ist.
        """
        ...

    def exists(self, run_id: str) -> bool:
        """Non-error-Lookup: gibt `True` zurueck, wenn der Lauf
        persistiert ist."""
        ...

    def update_status(self, run_id: str, status: RunStatus) -> None:
        """Setzt den `RunStatus`-Lifecycle-State (M5 Welle 4a, ADR 0039
        Decision 12).

        Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert
        ist. Symmetrisch zu `get_by_id` — keine Auto-Create-
        Semantik. Idempotente Wiederholung mit demselben Status
        ist ein No-op; Invalid-Transitions sind Aufrufer-
        Verantwortung (TickLoop wirft `TickLoopInvalidTransition
        Error` BEVOR diese Methode gerufen wird).
        """
        ...

    def get_status(self, run_id: str) -> RunStatus:
        """Liest den `RunStatus`-Lifecycle-State (M5 Welle 4a, ADR 0039
        Decision 12).

        Wirft `RunNotFoundError`, wenn der Lauf nicht persistiert
        ist. Default nach `save` ist ``"pending"`` — die
        ``update_status``-Aufrufe aus TickLoop-`request_*`-Methoden
        propagieren die State-Transitions.
        """
        ...
