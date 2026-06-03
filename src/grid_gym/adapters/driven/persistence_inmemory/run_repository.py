"""In-Memory-`RunRepositoryPort`-Implementation (M5 Welle 5).

Produktiver Demo-Pfad-Adapter fuer den Lifespan-env-var-Pfad
(`GRID_GYM_DEMO_SCENARIO_PATH`). Haelt `RunMetadata` und den
orthogonalen `RunStatus`-Lifecycle-State in zwei Dicts; der State
ueberlebt den Prozess nicht — Demo-Sessions starten frische
Runs aus dem Scenario-YAML.

Welle-4a hatte den Status-Lifecycle (ADR 0039 Decision 12) am
`InMemoryRunRepository`-Test-Helper unter
``tests/unit/hexagon/ports/driven/_fakes.py`` etabliert; Welle 5
hebt die Substanz nach ``adapters/driven/persistence_inmemory/``,
damit die produktive Demo-Pipeline (Lifespan +
`make demo`-Container) den Welle-4a/4b-`update_status`/
`get_status`-Pfad ohne `NotImplementedError` ausueben kann.

Welle-6c-Aussicht (`GG-PERSIST-001`/`004`): Postgres-Status-Spalte
+ alembic-Revision; bestehende Tests dieses Adapters bleiben
gruen, bestehende `PostgresRunRepository.update_status`-Stub-
Aufrufer wechseln auf den Postgres-Pfad.
"""

from __future__ import annotations

from grid_gym.hexagon.core.domain.run import RunMetadata, RunStatus
from grid_gym.hexagon.core.errors import RunAlreadyExistsError, RunNotFoundError


class InMemoryRunRepository:
    """`RunRepositoryPort`-Implementation mit dict-basiertem Store.

    Welle-5-Produktiv-Adapter (M5 Welle 5). Substanz identisch
    zum Test-Fake ``tests/unit/hexagon/ports/driven/_fakes.
    InMemoryRunRepository`` (Welle-4a-Extension um den Status-
    Lifecycle); der Test-Fake bleibt fuer Unit-Tests bestehen.

    `_status_store` haelt den Lifecycle-State neben den Metadaten;
    `save` initialisiert auf ``"pending"`` per Port-Vertrag
    (ADR 0039 Decision 12). Invalid-Transitions sind Aufrufer-
    Verantwortung (`TickLoop.request_*` wirft
    `TickLoopInvalidTransitionError` vor dem `update_status`-Call).
    """

    def __init__(self) -> None:
        self._store: dict[str, RunMetadata] = {}
        self._status_store: dict[str, RunStatus] = {}

    def save(self, metadata: RunMetadata) -> None:
        if metadata.run_id in self._store:
            raise RunAlreadyExistsError(metadata.run_id)
        self._store[metadata.run_id] = metadata
        self._status_store[metadata.run_id] = "pending"

    def get_by_id(self, run_id: str) -> RunMetadata:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        return self._store[run_id]

    def exists(self, run_id: str) -> bool:
        return run_id in self._store

    def update_status(self, run_id: str, status: RunStatus) -> None:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        self._status_store[run_id] = status

    def get_status(self, run_id: str) -> RunStatus:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        return self._status_store[run_id]
