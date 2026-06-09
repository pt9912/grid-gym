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

from grid_gym.hexagon.core.agents import (
    Agent,
    AgentMessageBus,
    AgentPlugin,
    RuleBasedAgent,
    RuleBasedAgentConfig,
)
from grid_gym.hexagon.core.agents.rule_based import (
    Rule,
    RuleAction,
    RuleCondition,
)
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioAgent,
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
    ScenarioUnknownAgentPluginError,
    ScenarioUnknownAgentTypeError,
    ScenarioUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.scenario.validator import validate_scenario_mapping
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.device_protocol import DeviceProtocolPort
from grid_gym.hexagon.ports.driven.fault import FaultPort
from grid_gym.hexagon.ports.driven.observability import LogPort, MetricsPort, TracePort
from grid_gym.hexagon.ports.driven.random import RandomPort
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driven.replay_snapshot import ReplaySnapshotPort
from grid_gym.hexagon.ports.driven.telemetry_sink import TelemetrySinkPort


AlarmIdSource = Callable[[], str]
"""Welle-4b-Review-Fix #11: signature-alias fuer den
``alarm_id_source``-Kwarg (Production-Default ``uuid.uuid4``;
Tests injizieren einen monoton zaehlenden Stub fuer
deterministische Alarm-IDs)."""


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
        # M3-Welle-4b (ADR 0027 §2.1): optionaler nested agents-Block.
        agents=_parse_agents(raw),
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
    # `device.initialize(...)` validiert vorgelagert via
    # `SmartMeterConfig._config_from_params`, dass `raw` entweder
    # `tuple` oder `list` ist — der `list`-Branch ist daher der einzige
    # noch erreichbare Pfad.
    return tuple(cast(list[str], raw))


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


@dataclass(frozen=True, slots=True)
class TickLoopWiring:
    """Optionale Verdrahtungs-Envelope fuer `build_tick_loop`
    (Slice 027 Paket C).

    Buendelt alle optionalen Cross-Cutting-Ports zu einem
    Value-Object, damit `build_tick_loop` kein 10-Parameter-Aufruf
    mehr ist. Default `None` heisst „kein Port" (analog zu den
    bisherigen `None`-Defaults der einzelnen Kwargs).

    Felder spiegeln den TickLoop-Konstruktor-Vertrag aus
    `ADR 0022 §2.5`, `ADR 0023 §2.5`, `ADR 0024 §2.6`, `ADR 0026
    §2.2`, `ADR 0030 §4` (M4-Welle-1 `protocol_ports`). Eine
    Aenderung dieser Liste braucht eine Folge-ADR (Builder-
    Symmetrie).
    """

    fault_port: FaultPort | None = None
    agent_bus: AgentMessageBus | None = None
    agents: tuple[Agent, ...] | None = None
    log_port: LogPort | None = None
    metrics_port: MetricsPort | None = None
    trace_port: TracePort | None = None
    protocol_ports: tuple[DeviceProtocolPort, ...] | None = None
    run_repository: RunRepositoryPort | None = None
    telemetry_sink: TelemetrySinkPort | None = None
    replay_snapshot: ReplaySnapshotPort | None = None
    replay_reference_run_id: str | None = None
    alarm_id_source: AlarmIdSource | None = None


def build_tick_loop(
    scenario: Scenario,
    *,
    run_id: str,
    clock: ClockPort,
    random_root: RandomPort,
    wiring: TickLoopWiring | None = None,
) -> TickLoop:
    """Welle-6b (ADR 0021 §2.4): produktiver TickLoop-Builder.

    Verdrahtet Devices, optionalen `GridModelBilanz`, M1-
    Scheduler-Events (unveraendertes M1-Surface) sowie
    LoadEvent/LoadProfile-Tupel aus dem Scenario zu einem
    fertig-konfigurierten `TickLoop`. Aufrufer-Pflicht: clock
    und `random_root` sind bereits konstruiert (`random_root`
    typisch der `RandomPort` ueber `scenario.simulation.seed`).

    M3-Welle-2 (ADR 0022 §2.5): optionaler `fault_port`-Kwarg
    fuer Fault-Injection. `None`-Default skippt den TickLoop-
    Vor-Tick-Block-Schritt-A2-Hook; Welle-2-Aufrufer mit
    `scenario.faults`-Inhalt konstruieren typischerweise
    `BatteryFaultAdapter` + `GridFaultAdapter` aus
    `scenario.faults` und komponieren sie in einen produktiven
    FaultPort (Composition-Pattern ist M3-Welle-3-Material;
    Welle-2-Integrationstests komponieren test-side).

    M3-Welle-3 (ADR 0023 §2.5): optionaler `agent_bus`-Kwarg
    fuer Multi-Agent-Bus. `None`-Default skippt den TickLoop-
    Schritt-D2-Hook.

    M3-Welle-4a (ADR 0026 §2.2): produktiver `agents`-Kwarg
    fuer Multi-Agent-Registry. `()`-Default behaelt agentenlose
    Runs unveraendert. Bei nicht-leeren `agents` aktiviert die
    Auto-Bus-Regel im TickLoop-Konstruktor automatisch einen
    `AgentMessageBus`, falls keiner explizit injiziert ist.

    M3-Welle-4a (ADR 0026 §2.2 + §2.6): bei vorhandenem
    `grid_model_config` reicht der Builder die Scenario-
    LoadOverlay-Tupel an den `GridModelBilanz`-Konstruktor
    durch, damit der GridModel-v2-Overlay-Snapshot
    (ADR 0020) die Single Source of Truth fuer die
    Welle-4a-Resume-LoadOverlay-Match-Checks ist.

    M3-Welle-4b (ADR 0027 §2.2): `agents=None`-Default
    (Sentinel) signalisiert „Builder leitet Tuple aus
    `scenario.agents` via Factory-Map ab". Explizite Tupel
    werden vom Aufrufer durchgereicht — auch das leere
    Tupel `()` (= „agentenloser Run trotz Scenario-Block").
    Welle-4b-Review-Folge F-1 (2026-05-22): vorher hatte
    `agents=()`-Default die Scenario-Defaultierung
    ausgeloest, was den expliziten agentenlosen Override
    silent ueberschrieb.
    """
    devices = build_devices(scenario.devices, random_root)
    w = wiring if wiring is not None else TickLoopWiring()
    # M3-Welle-4b (ADR 0027 §2.2 + Review-Folge F-1):
    # `wiring.agents=None`-Sentinel triggert Scenario-Defaultierung.
    # Expliziter `()`-Override wird respektiert.
    resolved_agents: tuple[Agent, ...] | None = w.agents
    if resolved_agents is None:
        resolved_agents = _build_agents(scenario.agents) if scenario.agents else ()
    # Welle-6b-Review M-6: Validierung, dass LoadEvent/LoadProfile-
    # Ziele auf legitime Overlay-Geraete (LoadDevice oder
    # GridConnectionDevice) zeigen.
    _assert_overlay_targets(devices, scenario.load_events, scenario.load_profiles)
    # M3-Welle-4a (ADR 0026 §2.2): wenn `grid_model_config`
    # vorhanden, baut der Builder das GridModel mit den
    # Overlay-Tupeln, damit `grid_model.snapshot()` sie
    # persistiert (Resume-Match-Check-Vorbereitung).
    grid_model = (
        GridModelBilanz(
            scenario.grid_model_config,
            active_load_events=scenario.load_events,
            active_load_profiles=scenario.load_profiles,
        )
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
        fault_port=w.fault_port,
        agent_bus=w.agent_bus,
        agents=resolved_agents,
        log_port=w.log_port,
        metrics_port=w.metrics_port,
        trace_port=w.trace_port,
        protocol_ports=w.protocol_ports,
        run_repository=w.run_repository,
        telemetry_sink=w.telemetry_sink,
        replay_snapshot=w.replay_snapshot,
        replay_reference_run_id=w.replay_reference_run_id,
        alarm_id_source=w.alarm_id_source,
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


# ---------------------------------------------------------------------------
# M3-Welle-4b (ADR 0027 §2.1 + §2.2): agents-Top-Level-Block + Factory
# ---------------------------------------------------------------------------


def _parse_agents(raw: Mapping[str, object]) -> tuple[ScenarioAgent, ...]:
    """ADR 0027 §2.1: liest den optionalen `agents`-Block (nested
    Mapping) aus dem validierten Scenario-Mapping in eine
    lexikographisch sortierte Tuple von `ScenarioAgent`-Eintraegen.

    Sortier-Vertrag (ADR 0027 §2.1): Iteration ueber
    `sorted(agents.keys())` lexikographisch, damit YAML-Loader-
    spezifische Reihenfolge keine Drift erzeugt.
    """
    if "agents" not in raw:
        return ()
    block = cast(Mapping[str, object], raw["agents"])
    return tuple(
        ScenarioAgent(
            id=agent_id,
            type=cast(str, cast(Mapping[str, object], block[agent_id])["type"]),
            params=cast(
                Mapping[str, object], cast(Mapping[str, object], block[agent_id])["params"]
            ),
        )
        for agent_id in sorted(block.keys())
    )


_AGENT_FACTORIES: Final[Mapping[str, Callable[[ScenarioAgent], Agent]]] = {
    "rule_based": lambda scenario_agent: _build_rule_based_agent(scenario_agent),
}
"""ADR 0027 §2.2: Welle-4b-Agent-Factory-Map. Welle 4c+/M5
muessen sich hier eintragen, analog `_DEVICE_FACTORIES`."""


_AGENT_PLUGIN_FACTORIES: Final[Mapping[str, Callable[[Mapping[str, object]], AgentPlugin]]] = {}
"""ADR 0027 §2.3: Plugin-Factory-Map fuer den
`RuleBasedAgent`-Plugin-Pfad. Welle 4b ist leer; konkrete
Plugins (`LearnedPolicyPlugin`, `MPCControllerPlugin` etc.)
sind Welle 4c+ Material.

Aufrufer mit einem Scenario, das `plugin: "<name>"` nutzt
ohne registrierte Factory, sieht `ScenarioUnknownAgentPluginError`
beim `build_agents(...)`-Aufruf (Fail-fast vor erstem Tick)."""


def _build_agents(
    scenario_agents: tuple[ScenarioAgent, ...],
) -> tuple[Agent, ...]:
    """ADR 0027 §2.2: Factory-Dispatch nach `ScenarioAgent.type`
    zu konkreten `Agent`-Implementern.

    Pattern parallel zu `build_devices(...)` aus Welle 6b. Pro
    `ScenarioAgent`:

    1. Factory aus `_AGENT_FACTORIES[type]`
       (Unknown → `ScenarioUnknownAgentTypeError`).
    2. `agent = factory(scenario_agent)`.

    Lifecycle (`set_run_id`, optional `attach_random`) ist
    Welle-4a-`_attach_agents()`-Verantwortung — das laeuft im
    `TickLoop`-Konstruktor (ADR 0026 §2.3), nicht hier.

    `random_root` wird NICHT injiziert (anders als
    `build_devices(...)`): RuleBasedAgent ist deterministisch
    und braucht keinen Random-Sub-Stream. Plugin-basierte
    Agents bekommen Random — falls ueberhaupt — via
    `_AGENT_PLUGIN_FACTORIES` (Welle 4c+ Material).
    """
    agents: list[Agent] = []
    for scenario_agent in scenario_agents:
        factory = _AGENT_FACTORIES.get(scenario_agent.type)
        if factory is None:
            raise ScenarioUnknownAgentTypeError(scenario_agent.type, tuple(_AGENT_FACTORIES))
        agents.append(factory(scenario_agent))
    return tuple(agents)


def _build_rule_based_agent(scenario_agent: ScenarioAgent) -> RuleBasedAgent:
    """ADR 0027 §2.3: konstruiert einen `RuleBasedAgent` aus dem
    `ScenarioAgent`-Eintrag.

    Hybrid-Mutual-Exclusivity ist vom Validator bereits geprueft
    (`ScenarioInvalidAgentParamsError`), daher hier nur die
    Konstruktion. Plugin-Pfad: Plugin-Factory-Lookup +
    Konstruktion mit `plugin_params`.
    """
    params = scenario_agent.params
    if "plugin" in params:
        plugin_name = cast(str, params["plugin"])
        plugin_factory = _AGENT_PLUGIN_FACTORIES.get(plugin_name)
        if plugin_factory is None:
            raise ScenarioUnknownAgentPluginError(
                scenario_agent.id, plugin_name, tuple(_AGENT_PLUGIN_FACTORIES)
            )
        plugin_params_raw = params.get("plugin_params")
        plugin_params: Mapping[str, object] = (
            cast(Mapping[str, object], plugin_params_raw)
            if isinstance(plugin_params_raw, Mapping)
            else {}
        )
        plugin_instance = plugin_factory(plugin_params)
        return RuleBasedAgent(
            RuleBasedAgentConfig(
                agent_id=scenario_agent.id,
                plugin=plugin_instance,
                plugin_name=plugin_name,
                plugin_params=plugin_params,
            )
        )
    # Rules-Pfad.
    target_device_id = cast(str, params["target_device_id"])
    rules_raw = cast(list[Mapping[str, object]], params["rules"])
    rules: tuple[Rule, ...] = tuple(_build_rule(rule_raw) for rule_raw in rules_raw)
    return RuleBasedAgent(
        RuleBasedAgentConfig(
            agent_id=scenario_agent.id,
            target_device_id=target_device_id,
            rules=rules,
        )
    )


def _build_rule(rule_raw: Mapping[str, object]) -> Rule:
    """Konstruiert eine `Rule` aus dem Scenario-Mapping. Validator
    hat alle Pflicht-Felder + Typen + Whitelists bereits geprueft."""
    condition_raw = cast(Mapping[str, object], rule_raw["condition"])
    action_raw = cast(Mapping[str, object], rule_raw["action"])
    return Rule(
        condition=RuleCondition(
            metric=cast(str, condition_raw["metric"]),
            comparator=cast(str, condition_raw["comparator"]),
            threshold=cast(int, condition_raw["threshold"]),
        ),
        action=RuleAction(
            type=cast(str, action_raw["type"]),
            payload=cast(Mapping[str, object], action_raw["payload"]),
        ),
    )
