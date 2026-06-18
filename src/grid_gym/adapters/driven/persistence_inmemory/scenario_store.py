"""In-Memory-`ScenarioStorePort`-Implementation (Multi-Run-Execution S1,
ADR 0069 §2.1).

Haelt kanonisierte `Scenario`-Objekte in einem dict, keyed by
`scenario_hash`. Der State ueberlebt den Prozess nicht — Demo-/Test-
Sessions legen ihre Szenarien per `POST /scenarios` neu ab. Pattern
parallel zu `InMemoryRunRepository` (M5 Welle 5); InMemory ist die heute
einzige nicht-Stub-Implementation dieses Ports (Postgres-Paritaet ist ein
Folge-Schritt des Multi-Run-Plans).
"""

from __future__ import annotations

from grid_gym.hexagon.core.domain.scenario import Scenario


class InMemoryScenarioStore:
    """`ScenarioStorePort`-Implementation mit dict-basiertem Store.

    `put` ist idempotent (der Hash determiniert den Content); ein erneutes
    `put` ueberschreibt mit strukturell identischem `Scenario`.
    """

    def __init__(self) -> None:
        self._store: dict[str, Scenario] = {}

    def put(self, scenario_hash: str, scenario: Scenario) -> None:
        self._store[scenario_hash] = scenario

    def get(self, scenario_hash: str) -> Scenario | None:
        return self._store.get(scenario_hash)

    def exists(self, scenario_hash: str) -> bool:
        return scenario_hash in self._store
