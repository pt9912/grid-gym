"""Scenario-Domain-Modelle (`GG-SCN-001..008`).

Frozen-Dataclasses fuer das in `GG-SCN-001` definierte YAML-
Szenarioformat. Welle 5 modelliert das Schema auf Domain-Ebene
als Mapping-input; YAML-File-Parsing ist Adapter-Verantwortung
(spaeterer Slice).

Pflichtfelder per `GG-SCN-001` Akzeptanzkriterium:
`schema_version`, `metadata`, `simulation`, `devices`; optional
`events`, `replay`, `faults`.

Tuple statt list/dict bei Sequenz- und Mapping-Feldern, damit
AC-DOMAIN-FROZEN strukturell erfuellt ist.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    """Szenario-Metadaten (`GG-SCN-001`).

    Welle 5 modelliert `id` und `name` als Pflichtfelder; weitere
    Felder kommen mit M2-Geraetemodellen.
    """

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class ScenarioSimulation:
    """Simulations-Konfiguration (`GG-SCN-002`, `GG-SIM-002`).

    `tick_ms` ist die Schrittweite; `duration_s` die Gesamtlaufzeit;
    `seed` der `RandomPort`-Wurzelseed (`GG-SEED-001`).
    """

    tick_ms: int
    duration_s: int
    seed: int


@dataclass(frozen=True, slots=True)
class ScenarioDevice:
    """Geraete-Definition im Szenario (`GG-SCN-001`).

    Welle-5-Stand: minimaler Strukturvertrag (id + type + params).
    M2-Geraetemodelle schaerfen das per Typ-Mapping.
    """

    id: str
    type: str
    params: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ScenarioEvent:
    """Szenario-Event (`GG-SCN-005`).

    Felder gemaess Akzeptanz: Simulationszeit, Ziel, Typ, Payload.
    `recovery` ist optional (Wiederherstellungsverhalten).
    """

    simulation_time: int
    target: str
    type: str
    payload: Mapping[str, object]
    recovery: str | None


@dataclass(frozen=True, slots=True)
class ScenarioReplayRef:
    """Replay-Verweis im Szenario (`GG-SCN-007`).

    Quelle (`source`), Format (`format`), Zeitabbildung
    (`time_mapping`), Validierungsstatus (`validation_status`).
    """

    source: str
    format: str
    time_mapping: str
    validation_status: str


@dataclass(frozen=True, slots=True)
class ScenarioFault:
    """Fault-Definition im Szenario (`GG-SCN-006`).

    Startzeit, Dauer, Ziel, Fault-Typ, Payload, Recovery-Verhalten.
    Welle-5-Validierung ist strukturell — die Fault-Logik selbst
    folgt in M3+.
    """

    start_simulation_time: int
    duration_ms: int
    target: str
    type: str
    payload: Mapping[str, object]
    recovery: str


@dataclass(frozen=True, slots=True)
class Scenario:
    """Geladenes, kanonisches Szenario (`GG-SCN-001..008`).

    Felder:
    - `schema_version` (`GG-SCN-001`/`003`): z. B.
      `"grid-gym.scenario.v1"`.
    - `metadata`, `simulation`, `devices` (Pflicht per
      `GG-SCN-001`).
    - `events`, `replay`, `faults` (optional; Welle 5 modelliert
      sie als leere Tupel/`None` wenn nicht im Quell-Mapping).

    `scenario_hash` wird vom Loader berechnet (nicht hier) per
    `canonical_json(asdict(scenario))` + SHA-256 — siehe
    `hexagon/core/scenario/loader.py`.
    """

    schema_version: str
    metadata: ScenarioMetadata
    simulation: ScenarioSimulation
    devices: tuple[ScenarioDevice, ...]
    events: tuple[ScenarioEvent, ...]
    replay: ScenarioReplayRef | None
    faults: tuple[ScenarioFault, ...]
