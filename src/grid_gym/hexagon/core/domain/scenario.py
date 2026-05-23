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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Welle-6b (ADR 0021 §2.3): Imports fuer optionale
    # Scenario-Erweiterungen. TYPE_CHECKING-Guard, weil
    # `grid_model`/`loads.py` selbst keine Scenario-Importe
    # haben (kein Cycle), aber wir den runtime-Import vermeiden
    # wollen — Welle-1-Pattern fuer Domain-Cross-Imports.
    from grid_gym.hexagon.core.grid_model.config import GridModelConfig
    from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile


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
class ScenarioAgent:
    """Agent-Definition im Szenario (M3 Welle 4b, ADR 0027 §2.2).

    Welle-4b-Stand: minimaler Strukturvertrag (id + type + params)
    analog `ScenarioDevice`. Konkrete `params`-Schemas sind pro
    `type` festgelegt (RuleBasedAgent: `target_device_id` +
    `rules` ODER `plugin` + `plugin_params`).

    `id` ist die `agent_id`-Pflicht aus dem nested `agents`-
    Top-Level-Block (ADR 0027 §2.1). Der Validator extrahiert
    `id` aus dem Dict-Key, nicht aus `agent_def`.
    """

    id: str
    type: str
    params: Mapping[str, object]


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
    - `grid_model_config`, `load_events`, `load_profiles`
      (M2-Welle-6b, ADR 0021 §2.3): optionale Welle-6b-
      Erweiterungen fuer das Netzbilanzmodell und Lastenheft-
      `GG-GRID-003`/`004`-Pfade.
    - `agents` (M3-Welle-4b, ADR 0027 §2.1): optionaler nested
      `agents`-Block; Default leer fuer Welle-1..6-Szenarien
      ohne Agenten.

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
    # Welle-6b (ADR 0021 §2.3): optionale Erweiterungen.
    grid_model_config: "GridModelConfig | None" = None
    load_events: "tuple[LoadEvent, ...]" = ()
    load_profiles: "tuple[LoadProfile, ...]" = ()
    # M3-Welle-4b (ADR 0027 §2.1): optionaler nested agents-Block.
    agents: tuple[ScenarioAgent, ...] = ()
