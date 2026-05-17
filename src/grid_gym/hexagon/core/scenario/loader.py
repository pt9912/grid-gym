"""Scenario-Loader (`GG-SCN-003`/`004`).

Nimmt ein vorvalidiertes (oder zu validierendes) `Mapping[str,
object]` entgegen und liefert ein kanonisches `Scenario`-Objekt
plus den `scenario_hash` (SHA-256 ueber `canonical_json` der
kanonisierten Domain-Form).

Trennung: YAML-File-Parsing lebt in einem zukuenftigen Adapter
(`adapters/driven/scenario_yaml/`), nicht hier. Der Loader hier
bleibt I/O-frei und Format-agnostisch.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import cast

from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioDevice,
    ScenarioEvent,
    ScenarioFault,
    ScenarioMetadata,
    ScenarioReplayRef,
    ScenarioSimulation,
)
from grid_gym.hexagon.core.scenario.validator import validate_scenario_mapping
from grid_gym.hexagon.core.serialization.canonical import canonical_json


@dataclass(frozen=True, slots=True)
class LoadedScenario:
    """Loader-Resultat (`GG-SCN-003`/`004`).

    Liegt ausserhalb `hexagon/core/domain/` — ist Loader-Compound,
    keine Domain-Entitaet (`scenario_hash` ist eine berechnete
    Sicht, kein Datenfeld). `frozen=True, slots=True` aus
    Konsistenz.
    """

    scenario: Scenario
    scenario_hash: str


def load_scenario(raw: Mapping[str, object]) -> LoadedScenario:
    """Validiert + kanonisiert + hasht ein Szenario-Mapping.

    Wirft Subklassen von `ScenarioError`, wenn das Mapping das
    `GG-SCN-001`-Schema verletzt. Bei erfolgreicher Validierung
    wird ein `Scenario` mit Tuple-Sequenzen konstruiert; der
    `scenario_hash` ist
    `sha256(canonical_json(asdict(scenario))).hexdigest()`.
    """
    validate_scenario_mapping(raw)
    scenario = _build_scenario(raw)
    digest = hashlib.sha256(canonical_json(asdict(scenario))).hexdigest()
    return LoadedScenario(scenario=scenario, scenario_hash=digest)


def _build_scenario(raw: Mapping[str, object]) -> Scenario:
    """Setzt die Domain-Form aus einem validierten Mapping zusammen.

    `validate_scenario_mapping` hat alle `isinstance`-Pruefungen
    bereits durchgefuehrt; hier nutzen wir `cast` zur Typ-Aufloesung
    fuer mypy. Bei Falschnutzung (Loader-Aufruf ohne vorhergehende
    Validierung) wuerde die `dataclass`-Konstruktion mit
    `TypeError` brechen — Aufrufer rufen `load_scenario` und nicht
    `_build_scenario` direkt.
    """
    metadata_raw = cast(Mapping[str, object], raw["metadata"])
    simulation_raw = cast(Mapping[str, object], raw["simulation"])
    devices_raw = cast(list[object], raw["devices"])
    return Scenario(
        schema_version=cast(str, raw["schema_version"]),
        metadata=ScenarioMetadata(
            id=cast(str, metadata_raw["id"]),
            name=cast(str, metadata_raw["name"]),
        ),
        simulation=ScenarioSimulation(
            tick_ms=cast(int, simulation_raw["tick_ms"]),
            duration_s=cast(int, simulation_raw["duration_s"]),
            seed=cast(int, simulation_raw["seed"]),
        ),
        devices=tuple(_build_device(entry) for entry in devices_raw),
        events=_build_events(raw),
        replay=_build_replay(raw),
        faults=_build_faults(raw),
    )


def _build_device(entry: object) -> ScenarioDevice:
    mapping = cast(Mapping[str, object], entry)
    return ScenarioDevice(
        id=cast(str, mapping["id"]),
        type=cast(str, mapping["type"]),
        params=cast(Mapping[str, object], mapping["params"]),
    )


def _build_events(raw: Mapping[str, object]) -> tuple[ScenarioEvent, ...]:
    if "events" not in raw:
        return ()
    events = cast(list[object], raw["events"])
    return tuple(_build_event(entry) for entry in events)


def _build_event(entry: object) -> ScenarioEvent:
    mapping = cast(Mapping[str, object], entry)
    recovery_raw = mapping.get("recovery")
    recovery = recovery_raw if isinstance(recovery_raw, str) else None
    return ScenarioEvent(
        simulation_time=cast(int, mapping["simulation_time"]),
        target=cast(str, mapping["target"]),
        type=cast(str, mapping["type"]),
        payload=cast(Mapping[str, object], mapping["payload"]),
        recovery=recovery,
    )


def _build_replay(raw: Mapping[str, object]) -> ScenarioReplayRef | None:
    if "replay" not in raw:
        return None
    replay = cast(Mapping[str, object], raw["replay"])
    return ScenarioReplayRef(
        source=cast(str, replay["source"]),
        format=cast(str, replay["format"]),
        time_mapping=cast(str, replay["time_mapping"]),
        validation_status=cast(str, replay["validation_status"]),
    )


def _build_faults(raw: Mapping[str, object]) -> tuple[ScenarioFault, ...]:
    if "faults" not in raw:
        return ()
    faults = cast(list[object], raw["faults"])
    return tuple(_build_fault(entry) for entry in faults)


def _build_fault(entry: object) -> ScenarioFault:
    mapping = cast(Mapping[str, object], entry)
    return ScenarioFault(
        start_simulation_time=cast(int, mapping["start_simulation_time"]),
        duration_ms=cast(int, mapping["duration_ms"]),
        target=cast(str, mapping["target"]),
        type=cast(str, mapping["type"]),
        payload=cast(Mapping[str, object], mapping["payload"]),
        recovery=cast(str, mapping["recovery"]),
    )
