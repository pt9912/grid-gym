"""Scenario-Loader (`GG-SCN-003`/`004`).

Nimmt ein vorvalidiertes (oder zu validierendes) `Mapping[str,
object]` entgegen und liefert ein kanonisches `Scenario`-Objekt
plus den `scenario_hash` (SHA-256 ueber `canonical_json` der
kanonisierten Domain-Form).

Trennung: YAML-File-Parsing lebt in einem zukuenftigen Adapter
(`adapters/driven/scenario_yaml/`), nicht hier. Der Loader hier
bleibt I/O-frei und Format-agnostisch.

Welle 6b (ADR 0021) ergaenzt zwei Welle-6b-Schritte:

- `build_devices(scenario_devices, random_root)`: Factory-
  Dispatch ueber `ScenarioDevice.type` zu konkreten
  `DeviceModel`-Implementierungen + `attach_sources(...)` fuer
  SmartMeter.
- `build_tick_loop(scenario, clock, random_root)`: produktiver
  Aufruf-Pfad, der Devices, GridModel und TickLoop verdrahtet.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Final, cast

from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioDevice,
    ScenarioEvent,
    ScenarioFault,
    ScenarioMetadata,
    ScenarioReplayRef,
    ScenarioSimulation,
)
from grid_gym.hexagon.core.errors import (
    ScenarioInvalidLoadTargetError,
    ScenarioMissingSourceDeviceError,
    ScenarioUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.scenario.validator import validate_scenario_mapping
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.random import RandomPort

_DEVICE_FACTORIES: Final[Mapping[str, Callable[[], DeviceModel]]] = {
    "battery": BatteryDevice,
    "pv": PvDevice,
    "load": LoadDevice,
    "grid_connection": GridConnectionDevice,
    "smart_meter": SmartMeterDevice,
}
"""Welle-6b (ADR 0021 §2.2): Hartzweig-Factory-Map fuer Device-
Dispatch nach `ScenarioDevice.type`. Pflegegleichheit mit
`TickLoop._DEVICE_TYPE_BY_CLASS_NAME` ist Welle-6c+/M3-Pflicht
(siehe ADR 0021 §6 Konsequenzen)."""


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
        # Welle-6b (ADR 0021 §2.3): optionale Top-Level-Sektionen.
        grid_model_config=_parse_grid_model_config(raw),
        load_events=parse_load_events(raw),
        load_profiles=parse_load_profiles(raw),
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


# ---------------------------------------------------------------------------
# Welle 6b — Device-Factory + TickLoop-Builder (ADR 0021 §2.2 + §2.4)
# ---------------------------------------------------------------------------


def build_devices(
    scenario_devices: tuple[ScenarioDevice, ...],
    random_root: RandomPort,
) -> tuple[DeviceModel, ...]:
    """Welle-6b (ADR 0021 §2.2): Factory-Dispatch nach
    `ScenarioDevice.type` zu konkreten `DeviceModel`-Implementierungen.

    **Resume-Vertrag** (Welle-6b-Review M-3): `build_devices`
    konstruiert ausschliesslich **frische** Devices ueber
    `factory().initialize(...)`. Welle 6b unterstuetzt **keinen**
    Resume-Pfad ueber den Loader — `from_snapshot`-restored Devices
    muessen vom Aufrufer separat instantiiert und ueber den
    `TickLoop`-Konstruktor verdrahtet werden (siehe
    ADR 0015 §4: Welle 6a-from_snapshot rekonstruiert Devices/
    grid_model nicht; Welle 6b's Loader-Pfad ist nur fuer den
    Fresh-Start gedacht). `attach_random(...)` (ADR 0018 §2.3)
    muessen Resume-Aufrufer selbst aufrufen.

    Pro `ScenarioDevice`:
    1. Factory aus `_DEVICE_FACTORIES[type]` (Unknown →
       `ScenarioUnknownDeviceTypeError`).
    2. `device = factory()`.
    3. `random_sub = random_root.sub_port(scenario_device.id)`
       (ADR 0007 §5).
    4. `device.initialize(scenario_device, random_sub)`.

    Nach der ersten Iteration verdrahtet die Funktion alle
    `SmartMeterDevice`-Instanzen ueber `attach_sources(...)` mit
    einem Mapping aller bekannten Devices nach `device_id` (ADR
    0018 §2.3 + ADR 0021 §2.2 SmartMeter-Sonderbehandlung).

    `aggregate_device_ids` werden vor dem `attach_sources(...)`-
    Aufruf gegen das Devices-Mapping verifiziert. Fehlende Quelle
    → `ScenarioMissingSourceDeviceError` (Fail-fast).
    """
    devices: list[DeviceModel] = []
    for scenario_device in scenario_devices:
        factory = _DEVICE_FACTORIES.get(scenario_device.type)
        if factory is None:
            raise ScenarioUnknownDeviceTypeError(
                scenario_device.type,
                tuple(_DEVICE_FACTORIES),
            )
        device = factory()
        random_sub = random_root.sub_port(scenario_device.id)
        device.initialize(scenario_device, random_sub)
        devices.append(device)

    devices_by_id: dict[str, DeviceModel] = {d.device_id: d for d in devices}
    for scenario_device, device in zip(scenario_devices, devices, strict=True):
        if not isinstance(device, SmartMeterDevice):
            continue
        aggregate_ids = _smart_meter_aggregate_ids(scenario_device)
        for source_id in aggregate_ids:
            if source_id not in devices_by_id:
                raise ScenarioMissingSourceDeviceError(scenario_device.id, source_id)
        device.attach_sources(devices_by_id)

    return tuple(devices)


def _smart_meter_aggregate_ids(scenario_device: ScenarioDevice) -> tuple[str, ...]:
    """Welle-6b (ADR 0021 §2.2): Liest `aggregate_device_ids`
    aus den `ScenarioDevice.params` der SmartMeter-Definition.

    Welle-6b-Review L-2: Die starke Typvalidierung lebt im
    `SmartMeterConfig._config_from_params` und ist beim
    `device.initialize(scenario_device, random_sub)`-Aufruf in
    `build_devices` BEREITS gelaufen (vor diesem Helfer). Hier
    bleibt nur das Mapping `tuple|list -> tuple[str, ...]`.
    Falsch-Typen koennen den Helfer nicht erreichen (initialize
    haette zuvor `WrongTypeError(subsystem='smart_meter',
    key='params.aggregate_device_ids', ...)` geworfen).
    """
    if "aggregate_device_ids" not in scenario_device.params:
        return ()
    raw = scenario_device.params["aggregate_device_ids"]
    if isinstance(raw, tuple):
        return cast(tuple[str, ...], raw)
    if isinstance(raw, list):
        return tuple(cast(list[str], raw))
    return ()  # pragma: no cover — vorgelagert von initialize geblockt


def _parse_grid_model_config(raw: Mapping[str, object]) -> GridModelConfig | None:
    """Welle-6b (ADR 0021 §2.3): liest die optionale `grid_model`-
    Sektion aus dem validierten Mapping in einen `GridModelConfig`.
    Validator hat alle Pflicht-Decimal-Felder bereits geprueft."""
    if "grid_model" not in raw:
        return None
    block = cast(Mapping[str, object], raw["grid_model"])
    return GridModelConfig(
        nominal_frequency_hz=cast(Decimal, block["nominal_frequency_hz"]),
        frequency_sensitivity_hz_per_kw=cast("Decimal", block["frequency_sensitivity_hz_per_kw"]),
        frequency_clamp_min_hz=cast(Decimal, block["frequency_clamp_min_hz"]),
        frequency_clamp_max_hz=cast(Decimal, block["frequency_clamp_max_hz"]),
        nominal_voltage_v=cast(Decimal, block["nominal_voltage_v"]),
        voltage_sensitivity_v_per_kw=cast("Decimal", block["voltage_sensitivity_v_per_kw"]),
        voltage_clamp_min_v=cast(Decimal, block["voltage_clamp_min_v"]),
        voltage_clamp_max_v=cast(Decimal, block["voltage_clamp_max_v"]),
    )


def parse_load_events(raw: Mapping[str, object]) -> tuple[LoadEvent, ...]:
    """Welle-6b (ADR 0021 §2.3 + ADR 0020 §2.2): liest `load_events`
    aus dem validierten Scenario-Mapping. Validator hat alle
    Pflicht-Decimal-/`target_device_id`-Felder bereits geprueft."""
    if "load_events" not in raw:
        return ()
    entries = cast(list[object], raw["load_events"])
    return tuple(_build_load_event(entry) for entry in entries)


def _build_load_event(entry: object) -> LoadEvent:
    mapping = cast(Mapping[str, object], entry)
    return LoadEvent(
        start_s=cast(Decimal, mapping["start_s"]),
        duration_s=cast(Decimal, mapping["duration_s"]),
        target_device_id=cast(str, mapping["target_device_id"]),
        power_kw=cast(Decimal, mapping["power_kw"]),
    )


def parse_load_profiles(raw: Mapping[str, object]) -> tuple[LoadProfile, ...]:
    """Welle-6b (ADR 0021 §2.3 + ADR 0020 §2.3): liest `load_profiles`
    aus dem validierten Scenario-Mapping."""
    if "load_profiles" not in raw:
        return ()
    entries = cast(list[object], raw["load_profiles"])
    return tuple(_build_load_profile(entry) for entry in entries)


def _build_load_profile(entry: object) -> LoadProfile:
    mapping = cast(Mapping[str, object], entry)
    tick_values = tuple(cast(list[Decimal], mapping["tick_values"]))
    return LoadProfile(
        target_device_id=cast(str, mapping["target_device_id"]),
        tick_values=tick_values,
        tick_ms=cast(int, mapping["tick_ms"]),
    )


def build_tick_loop(
    scenario: Scenario,
    *,
    run_id: str,
    clock: ClockPort,
    random_root: RandomPort,
) -> TickLoop:
    """Welle-6b (ADR 0021 §2.4): produktiver TickLoop-Builder.

    Verdrahtet Devices, optionalen `GridModelBilanz`, M1-
    Scheduler-Events (unveraendertes M1-Surface) sowie
    LoadEvent/LoadProfile-Tupel aus dem Scenario zu einem
    fertig-konfigurierten `TickLoop`. Aufrufer-Pflicht: clock
    und `random_root` sind bereits konstruiert (`random_root`
    typisch der `RandomPort` ueber `scenario.simulation.seed`).
    """
    devices = build_devices(scenario.devices, random_root)
    # Welle-6b-Review M-6: Validierung, dass LoadEvent/LoadProfile-
    # Ziele auf legitime Overlay-Geraete (LoadDevice oder
    # GridConnectionDevice) zeigen.
    _assert_overlay_targets(devices, scenario.load_events, scenario.load_profiles)
    grid_model = (
        GridModelBilanz(scenario.grid_model_config)
        if scenario.grid_model_config is not None
        else None
    )
    # Welle-6b (ADR 0021 §7): ScenarioEvent→Event-Bridge ist
    # explizit out-of-scope. Der Scheduler wird leer initialisiert;
    # M1-Scheduler-Events bleiben in `scenario.events` und werden
    # in Welle 6c / M3 in das Event-Surface uebersetzt.
    scheduler = Scheduler()
    return TickLoop(
        run_id=run_id,
        tick_ms=scenario.simulation.tick_ms,
        clock=clock,
        random=random_root,
        scheduler=scheduler,
        devices=devices,
        grid_model=grid_model,
        active_load_events=scenario.load_events,
        active_load_profiles=scenario.load_profiles,
    )


def _assert_overlay_targets(
    devices: tuple[DeviceModel, ...],
    load_events: tuple[LoadEvent, ...],
    load_profiles: tuple[LoadProfile, ...],
) -> None:
    """Welle-6b-Review M-6 (ADR 0021 §2.5 + §2.7): Validiert, dass
    jeder LoadEvent-/LoadProfile-Target auf ein LoadDevice oder
    GridConnectionDevice zeigt. Unbekannte Targets werden zur
    Laufzeit von TickLoop silent-skipped — diese Pre-Check-
    Validierung fluegt nur Wrong-Type ab; unbekannte IDs bleiben
    die Verantwortung des Validators (`ScenarioUnknownEventTargetError`).
    """
    device_by_id = {device.device_id: device for device in devices}
    for event in load_events:
        target = device_by_id.get(event.target_device_id)
        if target is None:
            continue
        if not isinstance(target, LoadDevice | GridConnectionDevice):
            raise ScenarioInvalidLoadTargetError(
                "LoadEvent", event.target_device_id, type(target).__name__
            )
    for profile in load_profiles:
        target = device_by_id.get(profile.target_device_id)
        if target is None:
            continue
        if not isinstance(target, LoadDevice | GridConnectionDevice):
            raise ScenarioInvalidLoadTargetError(
                "LoadProfile", profile.target_device_id, type(target).__name__
            )
