"""TickLoop — die invariante Simulations-Spine (M1 Welle 4 / M2 Welle 6a).

Der `TickLoop` verbindet `ClockPort`, `RandomPort`, `Scheduler` und
ab Welle 6a die fuenf MVP-`DeviceModel`-Implementationen + das
`GridModelBilanz` zu einem deterministischen Tick-zu-Tick-Pfad
(`GG-SIM-001`/`002`, `GG-ARCH-008`).

**M1 Welle 4** liefert den Kern ohne Geraete. **M2 Welle 6a**
erweitert ihn um Device-Iteration + `grid_model.update(...)` und
hebt das Snapshot-Schema von `version=1` auf `version=2`
(ADR 0015):

- Pro `tick()` ruft der Loop fuer jedes Device
  `device.tick(DeviceTickContext(...))`. Telemetry wird
  konkateniert in `TickResult.emitted_telemetry` (sortiert nach
  Device-Reihenfolge x Per-Device-`TelemetryPoint.sequence`).
- Nach allen Device-Ticks ruft der Loop
  `grid_model.update(generation_kw, load_kw, storage_kw,
  grid_connection_kw)` mit aggregierten Power-Werten. Welle-6b
  ergaenzt den GridConnection-Auto-Schluss (ADR 0017 §2.2 /
  ADR 0019 §6 — Pre-Grid-Restbilanz).

Snapshot-Vertrag (Welle 6a, `version=2`):

- `TickLoop.snapshot()["version"] = 2`.
- `sub_snapshots` enthaelt zusaetzlich zu Welle-4-Eintraegen
  (`scheduler`, `random_root`):
  - `devices.<device_type>.<device_id>` je angemeldetem Geraet
    (Type-Segment ist Pflicht fuer `from_snapshot`-Dispatch).
  - `grid_model` (Single-Instance, sofern gesetzt).
- v1-Read in `TickLoop.from_snapshot(...)` wirft den typisierten
  `TickLoopSnapshotVersionError` (ADR 0015 §2.4).

Welle-6a-`TickLoop.from_snapshot(state, *, clock, random)`
rekonstruiert den Loop **ohne** Devices/grid_model — Aufrufer
(Welle 6b Scenario-Loader) injiziert sie separat ueber den
Konstruktor. Welle 6a haelt nur den Snapshot-Versions-Wechsel
und das Sub-Snapshot-Emission-Pattern. Konsistenz-Pruefungen
fuer `clock.now()` und `random.snapshot_as_mapping()` bleiben
unveraendert.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Final

from grid_gym.hexagon.core.agents import Agent, AgentMessageBus, _RandomAttachableAgent
from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.quality import QUALITY_SEVERITY, Quality
from grid_gym.hexagon.core.domain.replay import ReplayDelta, ReplayDeltaClassification
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile

from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.run import ControlAction, RunStatus
from grid_gym.hexagon.core.simulation.alarm_mappers import dispatch_alarm_mapper
from grid_gym.hexagon.core.errors import (
    AgentDuplicateIdError,
    AgentInvalidCommandTargetError,
    RunNotFoundError,
    TickLoopAgentInstanceSnapshotMismatchError,
    TickLoopAgentSnapshotDeviceMismatchError,
    TickLoopAgentSnapshotGridModelMismatchError,
    TickLoopAgentSnapshotInvalidCommandResultError,
    TickLoopAgentSnapshotLoadOverlayMismatchError,
    TickLoopAgentSnapshotMissingKeysError,
    TickLoopAgentSnapshotWrongTypeError,
    TickLoopInvalidMaxAgeMsError,
    TickLoopInvalidTickMsError,
    TickLoopInvalidTransitionError,
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
    TickLoopStoppedError,
    TickLoopUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.replay.diff import diff_replay
from grid_gym.hexagon.ports.driven.replay_snapshot import ReplaySnapshotPort
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driven.telemetry_sink import TelemetrySinkPort
from grid_gym.hexagon.core.grid_model import GridModelBilanz
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortError,
)
from grid_gym.hexagon.ports.driven.fault import FaultPort
from grid_gym.hexagon.ports.driven.observability import (
    LogEntry,
    LogPort,
    MetricsPort,
    SpanContext,
    TracePort,
)
from grid_gym.hexagon.ports.driven.random import RandomPort

_SNAPSHOT_VERSION: Final[int] = 2
"""Schema-Version des TickLoop-Snapshots. Welle-6a-Bump 1->2 ueber
ADR 0015. Erhoehung -> Folge-ADR."""

_ZERO = Decimal(0)
_TICK_LOOP_DECIMAL_PRECISION: Final[int] = 28


@contextmanager
def _tick_loop_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper fuer die Bilanz-Aggregation in
    `tick()` (Welle-6a-Review M-4, Welle-5b-Review-M-2-Pattern).
    Pinnt `prec=28` + `ROUND_HALF_EVEN`, analog
    `bilanz.py::_grid_model_decimal_context` und
    `loads.py::_loads_decimal_context`."""
    with localcontext() as ctx:
        ctx.prec = _TICK_LOOP_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


# Welle-6a-Review L-3: v2-Top-Level-Pflicht-Keys sind identisch
# zu v1; die Welle-6a-Erweiterung liegt ausschliesslich im
# `sub_snapshots`-Mapping (siehe ADR 0015 §2.3 + §1 Bruch-
# Begruendung). Beim naechsten Versions-Bump in M6/Folge-Welle
# kann das Set ggf. waeqsen.
_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"version", "run_id", "simulation_time", "tick_count", "tick_ms", "sub_snapshots"}
)

# Welle-6a: M1-Welle-4-Pflicht-Sub-Snapshots bleiben unveraendert.
# `devices.<device_type>.<device_id>` und `grid_model` werden nur
# vom TickLoop selbst geschrieben (Welle-6a) und sollen NICHT
# Aufrufer-Pflicht in der Welle-6a-Lese-Pfad-Validierung sein
# (ADR 0015 §2.3 — Hexagon-Layer bleibt sauber, generische
# Envelope-Validierung kennt keine M2-Sub-Snapshot-Namen).
_REQUIRED_SUB_SNAPSHOT_KEYS: Final[frozenset[str]] = frozenset({"scheduler", "random_root"})

_POWER_KW_METRIC: Final[str] = "power_kw"
"""TelemetryPoint.metric, ueber den die Bilanz aggregiert (ADR 0019 §2.2)."""

_DEVICE_TYPE_BY_CLASS_NAME: Final[Mapping[str, str]] = {
    "BatteryDevice": "battery",
    "PvDevice": "pv",
    "LoadDevice": "load",
    "GridConnectionDevice": "grid_connection",
    "SmartMeterDevice": "smart_meter",
}
"""Welle-6a-Device-Type-Mapping fuer Sub-Snapshot-Key-Konstruktion
(ADR 0015 §2.3). Welle 7+/M3-Geraete muessen sich hier eintragen
oder eine `device_type`-Protocol-Erweiterung erzwingen.

`SmartMeter`-Telemetry traegt die Metric `aggregated_power_kw` (kein
`power_kw`); SmartMeter wird daher in der Bilanz-Aggregation
ueber den Metric-Filter automatisch uebersprungen, ohne dass die
SmartMeter-Aggregation den `imbalance_kw`-Wert verdoppelt."""

_AGENT_TYPE_BY_CLASS_NAME: Final[Mapping[str, str]] = {
    "RuleBasedAgent": "rule_based",
}
"""M3-Welle-4b-Agent-Type-Mapping fuer Sub-Snapshot-Key-Konstruktion
`agents.<agent_type>.<agent_id>` (ADR 0027 §2.4 + ADR 0015 §2.3-
additiv). Welle 4c+/M5-Agent-Typen muessen sich hier eintragen,
pattern-konsistent zu `_DEVICE_TYPE_BY_CLASS_NAME`."""


def _default_alarm_id_source() -> str:
    """Production-Default fuer die Alarm-ID-Generierung
    (`uuid.uuid4` als String; M5 Welle 4b, ADR 0040 Decision 16).
    Tests injizieren einen monoton zaehlenden Stub via
    `alarm_id_source`-Konstruktor-Kwarg."""
    return str(uuid.uuid4())


_CONTROL_ACTION_TRANSITIONS: Final[
    Mapping[ControlAction, tuple[RunStatus, tuple[RunStatus, ...]]]
] = {
    "pause": ("paused", ("pending", "running", "paused")),
    "resume": ("running", ("pending", "paused", "running")),
    "stop": ("stopped", ("pending", "running", "paused", "stopped")),
}
"""ADR 0039 Decision 13 Transitions-Matrix: pro ControlAction die
``(target_state, allowed_from_states)``-Paarung. Idempotenter
No-op-Pfad ist im Caller (`TickLoop.request`) — der Target-State
ist in `allowed_from` enthalten."""

_REPLAY_PREFLIGHT_FIELDS: Final[tuple[str, ...]] = (
    "scenario_hash",
    "schema_version",
    "seed",
    "tick_ms",
    "tool_version",
)
"""M7-Welle-1b-b (ADR 0049 §2.3): die 5 bereits strukturierten
`RunMetadata`-Felder des `GG-TERM-002/003`-MVP-Replay-Preflights.
Bei Ungleichheit eines Felds wird der Replay-Diff verworfen (kein
`replay_diff_status`). Die volle Matrix (`platform_arch` etc.)
bleibt Carveout Trigger 038."""

_BILANZ_SOURCE_BUCKETS: Final[Mapping[str, str]] = {
    "pv": "generation",
    "load": "load",
    "battery": "storage",
    "grid_connection": "grid_connection",
}
"""TelemetryPoint.source -> Bilanz-Bucket fuer
`GridModelBilanz.update(...)` (ADR 0019 §2.2 Sign-Konvention).
SmartMeter (`source="smart_meter"`) ist nicht abgebildet —
aggregated_power_kw faellt durch den Metric-Filter."""


def _assert_unique_agent_ids(agents: tuple[Agent, ...]) -> None:
    """Welle-4a-Duplicate-ID-Pruefung (ADR 0026 §2.5 Registry-
    Fail-Fast): doppelte `agent_id`-Werte werfen
    `AgentDuplicateIdError`. M7-Welle-3a aus `__init__` extrahiert
    (PLR0915-Drop); Verhalten unveraendert."""
    seen_agent_ids: set[str] = set()
    for agent in agents:
        if agent.agent_id in seen_agent_ids:
            raise AgentDuplicateIdError(agent.agent_id)
        seen_agent_ids.add(agent.agent_id)


class TickLoop:
    """Deterministischer Tick-Loop (`GG-SIM-001`/`002`).

    `tick_ms` ist die Schrittweite je `tick()`-Aufruf (10/100/1000
    per `GG-SIM-002`); `run_id` ist die stabile Lauf-Identitaet
    (`GG-DATA-001`); `tick_count` ist 0-basiert und zaehlt die
    bereits abgeschlossenen Ticks.
    """

    def __init__(
        self,
        *,
        run_id: str,
        tick_ms: int,
        clock: ClockPort,
        random: RandomPort,
        scheduler: Scheduler,
        devices: tuple[DeviceModel, ...] = (),
        grid_model: GridModelBilanz | None = None,
        active_load_events: tuple[LoadEvent, ...] = (),
        active_load_profiles: tuple[LoadProfile, ...] = (),
        fault_port: FaultPort | None = None,
        agent_bus: AgentMessageBus | None = None,
        agents: tuple[Agent, ...] = (),
        log_port: LogPort | None = None,
        metrics_port: MetricsPort | None = None,
        trace_port: TracePort | None = None,
        protocol_ports: tuple[DeviceProtocolPort, ...] | None = None,
        run_repository: RunRepositoryPort | None = None,
        telemetry_sink: TelemetrySinkPort | None = None,
        replay_snapshot: ReplaySnapshotPort | None = None,
        replay_reference_run_id: str | None = None,
        max_age_ms: int | None = None,
        alarm_id_source: Callable[[], str] | None = None,
    ) -> None:
        if tick_ms <= 0:
            # Format-Validierung am Konstruktor. Policy-Validierung
            # (Whitelist 10/100/1000 per `GG-SIM-002`) ist Welle-5-
            # Scenario-Loader-Verantwortung.
            raise TickLoopInvalidTickMsError(tick_ms)
        self._run_id: str = run_id
        self._tick_ms: int = tick_ms
        self._clock: ClockPort = clock
        self._random: RandomPort = random
        self._scheduler: Scheduler = scheduler
        self._tick_count: int = 0
        # Welle-6a: Devices und grid_model sind optional, damit M1-
        # Tests ohne Aenderung weiter laufen. Welle 6b-Scenario-
        # Loader injiziert die produktive Liste + grid_model.
        self._devices: tuple[DeviceModel, ...] = devices
        self._grid_model: GridModelBilanz | None = grid_model
        # Welle-6b (ADR 0021 §2.4/§2.5): active LoadEvents/Profiles
        # werden in jedem Tick zum apply_command-Pfad an LoadDevices
        # uebersetzt (Jedes-Tick-Baseline + Profile-Overlay +
        # Event-Overlay).
        self._active_load_events: tuple[LoadEvent, ...] = active_load_events
        self._active_load_profiles: tuple[LoadProfile, ...] = active_load_profiles
        # M3-Welle-1 (ADR 0022 §2.5): optionaler FaultPort fuer
        # Fault-Injection-Orchestrierung im Vor-Tick-Block. `None`
        # skippt den Hook in `tick()`; Welle-1-Code liefert noch
        # keinen produktiven Adapter (Welle 2).
        self._fault_port: FaultPort | None = fault_port
        # M7-Welle-1a telemetry_sink wird in `_attach_control_state`
        # neben `run_repository` gehalten (Driven-Persistenz-Sibling) —
        # haelt `__init__` unter dem PLR0915-Statement-Limit.
        # M3-Welle-3 (ADR 0023 §2.5) + M3-Welle-4a (ADR 0026 §2.2):
        # produktive Agent-Registry am TickLoop. `agent_bus=None`-
        # Default bleibt der saubere Skip-Pfad fuer agentenlose
        # Runs (Welle-3-Hook in Schritt D2 skippt dann).
        #
        # Welle-4a-Auto-Bus-Regel: wenn `agents != ()` aber
        # `agent_bus is None`, erzeugt der Konstruktor einen
        # frischen `AgentMessageBus`, damit registrierte Agents
        # nicht still als No-op enden (ADR 0026 §2.2).
        #
        # Welle-4a-Duplicate-ID-Pruefung: doppelte `agent_id`-
        # Werte werfen `AgentDuplicateIdError` (ADR 0026 §2.5
        # Registry-Fail-Fast). M7-Welle-3a: in den Modul-Helper
        # `_assert_unique_agent_ids` extrahiert (PLR0915-Drop,
        # Pattern analog `_attach_*`-Helper).
        _assert_unique_agent_ids(agents)
        if agents and agent_bus is None:
            agent_bus = AgentMessageBus()
        self._agent_bus: AgentMessageBus | None = agent_bus
        self._agents: tuple[Agent, ...] = agents
        # M3-Welle-5 (ADR 0024 §2.6): Observability-Port-Trio.
        # M4-Welle-1 (ADR 0030 §4): DeviceProtocolPort-Adapter
        # (Caller-Scope-Lifecycle). Beide Setups in Helper-Methoden
        # ausgelagert, weil der Konstruktor sonst die PLR0915-
        # Schwelle reisst (Pattern analog `_attach_devices` /
        # `_attach_agents`).
        self._attach_observability_ports(log_port, metrics_port, trace_port)
        self._attach_protocol_ports(protocol_ports)
        # M3-Welle-3-Review-Folge-2 F-1 + M3-Welle-4a F-1 produktiv:
        # `_pending_agent_commands` ist der Buffer, den Schritt D2
        # (Agent-Tick) fuellt und Schritt A0a (Pre-Tick-Drain) in
        # der naechsten Tick auf die Target-Devices anwendet.
        # Welle-4a (ADR 0026 §2.6) persistiert den Buffer als
        # `pending_agent_commands`-Sub-Snapshot, damit Snapshots
        # zwischen Agent-Tick und Folgetick keine Commands
        # verlieren.
        self._pending_agent_commands: list[Command] = []
        self._init_drift_counters()
        # Welle-6b (ADR 0021 §2.5): O(1)-Lookup-Tabelle fuer Devices
        # per device_id; einmal im Konstruktor aufgebaut, in
        # jedem Tick wiederverwendet.
        self._device_by_id: dict[str, DeviceModel] = {d.device_id: d for d in self._devices}
        # Welle-6b-Review M-2: konstante Load-Baseline-Map einmal
        # cachen statt jeden Tick aus `_devices` zu filtern.
        # `rated_power_kw` ist pro LoadDevice nach `initialize(...)`
        # invariant.
        self._load_baseline_by_id: dict[str, Decimal] = {
            d.device_id: d.rated_power_kw for d in self._devices if isinstance(d, LoadDevice)
        }
        # Welle-6a-Review C-1: Welle-3-Review-M-4-Vertrag erfordert,
        # dass TickLoop fuer jedes Device `set_run_id(self._run_id)`
        # ruft, bevor der erste Tick laeuft — sonst emittieren alle
        # Devices Telemetrie mit `run_id=""` statt der echten run_id
        # (verletzt GG-DATA-001). Konstruktor-Phase ist der natuerliche
        # Ort fuer den Lifecycle-Hook.
        self._attach_devices()
        # M3-Welle-4a (ADR 0026 §2.3): Lifecycle-Hook fuer
        # registrierte Agents — set_run_id + optionaler
        # `_RandomAttachableAgent.attach_random(random.sub_port(
        # f"agent-{agent_id}"))`. Wird NACH `_attach_devices()`
        # aufgerufen, damit `_device_by_id` schon gebaut ist
        # (Welle-4b-Agents koennten Device-Referenzen brauchen).
        self._attach_agents()
        self._attach_welle_4_state(
            run_repository,
            telemetry_sink,
            replay_snapshot,
            replay_reference_run_id,
            alarm_id_source,
        )
        # M7-Welle-3a (ADR 0052 §2.1): optionale `max_age`-Schwelle
        # fuer die STALE-Stage in `tick()`. `None` (Default) = Stage
        # aus; nicht-positive Werte sind ein Konstruktor-Fehler.
        self._attach_max_age(max_age_ms)

    def _init_drift_counters(self) -> None:
        """Welle-6a-Review M-3 + Welle-4b-Review-Fix #4: Forward-
        Compat-Counter fuer Drift gegen die jeweils registrierten
        Tabellen (`_BILANZ_SOURCE_BUCKETS` bzw. `dispatch_alarm_mapper`).
        Bundle, damit `__init__` die PLR0915-Schwelle nicht reisst."""
        self._unknown_source_count: int = 0
        self._unknown_alarm_type_count: int = 0

    def _attach_devices(self) -> None:
        """Reicht `run_id` an alle Devices durch (Welle-3-Review-M-4-
        Vertrag). `attach_random` und `attach_sources` (SmartMeter)
        bleiben Welle-6b-Scenario-Loader-Verantwortung — die brauchen
        Quell-Referenzen, die hier nicht verfuegbar sind."""
        for device in self._devices:
            device.set_run_id(self._run_id)

    def _attach_observability_ports(
        self,
        log_port: LogPort | None,
        metrics_port: MetricsPort | None,
        trace_port: TracePort | None,
    ) -> None:
        """M3-Welle-5 (ADR 0024 §2.6): initialisiert das optionale
        Observability-Port-Trio. `None`-Default skippt jeden Hook
        in `tick()`; produktive Adapter (Null oder OTLP) injizieren
        strukturierte Logs/Metriken/Traces. Loest ADR 0023 §2.6
        Observability-Vorgriff-Verbot auf (Welle-3-Klausel).
        """
        self._log_port: LogPort | None = log_port
        self._metrics_port: MetricsPort | None = metrics_port
        self._trace_port: TracePort | None = trace_port

    def _attach_protocol_ports(
        self,
        protocol_ports: tuple[DeviceProtocolPort, ...] | None,
    ) -> None:
        """M4-Welle-1 (ADR 0030 §2.2 + §4): initialisiert die
        optionalen DeviceProtocolPort-Adapter mit Caller-Scope-
        Lifecycle. `None`-Default skippt
        `start_protocol_ports()`/`stop_protocol_ports()` als No-op
        (Replay-Mode-Skip). Welle-1-Code liefert nur Lifecycle-
        Methoden; konkrete Adapter (`adapters/driven/protocol_*/`)
        kommen ab Welle 2.

        `_started_protocol_port_indices` ist der Tracking-Buffer
        fuer Partial-Start-Failure-Cleanup und LIFO-Stop +
        Idempotenz fuer den "nichts gestartet"-Fall.
        """
        self._protocol_ports: tuple[DeviceProtocolPort, ...] | None = protocol_ports
        self._started_protocol_port_indices: list[int] = []

    def _drain_and_map_device_alarms(self, simulation_time_ms: int) -> tuple[Alarm, ...]:
        """M5-Welle-4b (ADR 0040 Decision 16): drainst + mapped die
        device-spezifischen Raw-Alarms am Tick-Ende.

        Iteriert die Devices in Konstruktor-Reihenfolge
        (Determinismus-Garantie), drainst pro Device, mapped jeden
        raw-Alarm auf einen Unified-`Alarm` mit Run-Kontext
        (run_id + simulation_time_ms + alarm_id aus dem injizierten
        Source). `drain_alarms()` ist nur fuer die 5 device-
        Familien implementiert; der `hasattr`-Guard skippt
        Welle-7+/M3-Geraete, die das Pattern noch nicht
        uebernommen haben.

        Welle-4b-Review-Fix #4: erst ALLE Devices drainen, dann
        mappen. Sonst koennte ein Mapper-Fehler in der Mitte des
        Drain-Pfads die Raw-Alarms spaeterer Devices verschlucken
        und den Tick zwischen `clock.advance` und `_tick_count += 1`
        in einen inkonsistenten Zustand reissen. Unmappable Raw-
        Alarms werden geloggt + im `_unknown_alarm_type_count`
        gezaehlt, statt den ganzen Tick zu killen (Forward-Compat-
        Defense fuer Welle-7+-Geraete, deren Raw-Klasse noch nicht
        beim Mapper registriert ist).
        """
        raw_alarms: list[object] = []
        for device in self._devices:
            if not hasattr(device, "drain_alarms"):
                continue
            raw_alarms.extend(device.drain_alarms())
        alarms: list[Alarm] = []
        for raw in raw_alarms:
            try:
                alarms.append(
                    dispatch_alarm_mapper(
                        raw,
                        run_id=self._run_id,
                        simulation_time_ms=simulation_time_ms,
                        alarm_id=self._alarm_id_source(),
                    )
                )
            except TypeError:
                self._unknown_alarm_type_count += 1
                self._obs_log(
                    "warning",
                    "alarm_unknown_raw_type",
                    event_id=f"alarm-unknown-{self._unknown_alarm_type_count}",
                    attributes={"raw_type": type(raw).__name__},
                )
        return tuple(alarms)

    def _attach_welle_4_state(
        self,
        run_repository: RunRepositoryPort | None,
        telemetry_sink: TelemetrySinkPort | None,
        replay_snapshot: ReplaySnapshotPort | None,
        replay_reference_run_id: str | None,
        alarm_id_source: Callable[[], str] | None,
    ) -> None:
        """Run-Lifecycle-State-Setup-Bundle (Welle-4a Control-State +
        M7-Welle-1a Telemetrie-Sink + M7-Welle-1b-b Replay-Snapshot +
        Welle-4b Alarm-ID-Source). Bewusst gebuendelt, um `PLR0915
        max-statements=30` in `__init__` nicht zu reissen — die Slots
        sind klein und verwandt (Run-Lifecycle/Driven-Persistenz vs.
        Alarm-Aggregation), alle lesen optional `app.state`-Parameter
        aus dem Konstruktor."""
        self._attach_control_state(
            run_repository, telemetry_sink, replay_snapshot, replay_reference_run_id
        )
        self._attach_alarm_id_source(alarm_id_source)

    def _attach_alarm_id_source(
        self,
        alarm_id_source: Callable[[], str] | None,
    ) -> None:
        """M5-Welle-4b (ADR 0040 Decision 16): UUIDv4-Source-
        Injection fuer den `Alarm.alarm_id`-Slot. Production-
        Default ist `uuid.uuid4` (kollisionsfrei in der Praxis);
        Tests injizieren einen monoton zaehlenden Stub fuer
        deterministische Snapshot-Asserts. Pattern analog
        `random: RandomPort` aus M1."""
        self._alarm_id_source: Callable[[], str] = alarm_id_source or _default_alarm_id_source

    def _attach_control_state(
        self,
        run_repository: RunRepositoryPort | None,
        telemetry_sink: TelemetrySinkPort | None,
        replay_snapshot: ReplaySnapshotPort | None,
        replay_reference_run_id: str | None,
    ) -> None:
        """M5-Welle-4a (ADR 0039 Decisions 12+13): Run-Control-State-
        Mirror + optionale Repository-Persistenz. `_control_state`
        ist Cache der Repository-Wahrheit; bei `run_repository=None`
        (Default-Welle-1+M2-Tests) skippt die Repository-Mirror-
        Sequenz in `request`, der Pre-Tick-Guard greift trotzdem.
        Snapshot-Format aus ADR 0015 bleibt unveraendert —
        `_control_state` ist Run-Lifecycle, nicht Tick-Determinismus.
        Welle-4b-Review-Fix #3: `from_snapshot` nimmt jetzt einen
        `control_state`-Kwarg, den der Caller (Welle-5-Scenario-
        Loader) aus `RunRepository.get_status(run_id)` speist,
        damit ein `paused`-Run nach Resume nicht stillschweigend
        per First-Tick-Auto-Flip auf `running` springt."""
        self._control_state: RunStatus = "pending"
        self._run_repository: RunRepositoryPort | None = run_repository
        # M7-Welle-1a (ADR 0047 §2.3): Driven-Persistenz-Sibling zu
        # `run_repository` — append-only Telemetrie-Zeitreihen-Sink,
        # pro Tick aus dem Spine bedient (`None` → No-op-Skip).
        self._telemetry_sink: TelemetrySinkPort | None = telemetry_sink
        # M7-Welle-1b-b (ADR 0049 §2.1/§2.2): Replay-Lifecycle-State.
        # `replay_snapshot` rekonstruiert `expected`/`actual`-
        # ReplaySample-Sequenzen; `replay_reference_run_id` ist die
        # explizite Vergleichs-Bindung (beide `None` → `finalize()`
        # no-op). `_finalized` macht `finalize()` idempotent
        # (Driver-Loop-Exit + Lifespan-`stop()` koennen beide rufen).
        self._replay_snapshot: ReplaySnapshotPort | None = replay_snapshot
        self._replay_reference_run_id: str | None = replay_reference_run_id
        self._finalized: bool = False

    def _attach_max_age(self, max_age_ms: int | None) -> None:
        """M7-Welle-3a (ADR 0052 §2.1): `max_age`-Schwelle fuer die
        STALE-Stage. `None` (Default) = Stage aus (byte-identischer
        Bestands-Pfad); `<= 0` ist Format-Fehler am Konstruktor
        (Pattern analog `TickLoopInvalidTickMsError`)."""
        if max_age_ms is not None and max_age_ms <= 0:
            raise TickLoopInvalidMaxAgeMsError(max_age_ms)
        self._max_age_ms: int | None = max_age_ms

    def _attach_agents(self) -> None:
        """M3-Welle-4a (ADR 0026 §2.3): Lifecycle-Hook fuer Agents.

        Reicht `run_id` an alle registrierten Agents durch +
        attached einen Per-Agent-Sub-Random-Stream
        (`RandomPort.sub_port(f"agent-{agent_id}")`) an Agents,
        die das optionale `_RandomAttachableAgent`-Sub-Protocol
        implementieren (Hasattr-frei via `isinstance`-Check
        gegen `@runtime_checkable`-Protocol).

        Welle-4a-Foundation: Agents ohne Stochastik
        implementieren das Sub-Protocol nicht und bekommen
        weder einen Sub-Port noch einen No-op-Hook aufgezwungen.
        """
        for agent in self._agents:
            agent.set_run_id(self._run_id)
            if isinstance(agent, _RandomAttachableAgent):
                agent.attach_random(self._random.sub_port(f"agent-{agent.agent_id}"))

    # ------------------------------------------------------------------
    # Observability-Hook-Helpers (M3 Welle 5, ADR 0024 §2.6).
    # Jeder Helper kapselt die `if self._..._port is None: skip`-Logik,
    # damit `tick()` lesbar bleibt. Hooks sind rein additiv — sie
    # aendern weder Schritt-Reihenfolge noch Atomizitaets-Vertraege.
    # ------------------------------------------------------------------
    def _obs_start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext | None:
        if self._trace_port is None:
            return None
        return self._trace_port.start_span(name, parent=parent, attributes=attributes)

    def _obs_end_span(self, span: SpanContext | None) -> None:
        if self._trace_port is None or span is None:
            return
        self._trace_port.end_span(span)

    def _obs_log(
        self,
        level: str,
        message: str,
        *,
        event_id: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        if self._log_port is None:
            return
        self._log_port.log(
            LogEntry(
                level=level,
                message=message,
                run_id=self._run_id,
                module="tick_loop",
                event_id=event_id,
                attributes=attributes,
            )
        )

    def _obs_gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        if self._metrics_port is None:
            return
        self._metrics_port.gauge(name, value, attributes=attributes)

    def _obs_increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        if self._metrics_port is None:
            return
        self._metrics_port.increment(name, value, attributes=attributes)

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def tick_ms(self) -> int:
        return self._tick_ms

    @property
    def tick_count(self) -> int:
        """Anzahl bereits abgeschlossener Ticks (0 vor dem ersten
        `tick()`-Aufruf)."""
        return self._tick_count

    @property
    def device_types(self) -> Mapping[str, str]:
        """Welle-6a (Decision 20): Mapping `device_id → device_type`
        (`"battery"`/`"pv"`/`"load"`/`"grid_connection"`/`"smart_
        meter"`) per `_DEVICE_TYPE_BY_CLASS_NAME`-Lookup.

        Read-only public Surface fuer Cross-Field-Validation im
        POST-/faults-Handler: der Handler prueft, ob ein Form-
        eingegebenes `target_device_id` zum Run gehoert und ob das
        zugewiesene Fault-Type zum Device-Typ passt. Vermeidet
        DeviceModel-Klassen-Import in der HTTP-Adapter-Schicht
        (AC-ADAPTER-PURE-Konsistenz).

        Welle-6a-Review F3: nicht-gemappte DeviceModel-Klassen
        (Welle-7+/M3-Geraete ohne `_DEVICE_TYPE_BY_CLASS_NAME`-
        Eintrag) werden silent **gedroppt** statt
        `TickLoopUnknownDeviceTypeError` zu propagieren. Sonst
        crasht jeder Cross-Field-Validation-Call mit 500, auch
        fuer Targets gegen bekannte Devices im selben Run.
        Drop ist konservativ: target-lookup gegen die
        gedroppten Devices schlaegt mit `fault_unknown_target`
        fehl, Operator sieht klare 422 statt 500.
        """
        mapping: dict[str, str] = {}
        for device in self._devices:
            try:
                mapping[device.device_id] = _device_type_for(device)
            except TickLoopUnknownDeviceTypeError:
                continue
        return mapping

    @property
    def devices(self) -> tuple[DeviceModel, ...]:
        """M5-Welle-6b-Review F9: Read-only public Surface auf die
        registrierte Device-Sequenz (Konstruktor-Reihenfolge, also
        deterministisch).

        Geschwister-Property zu `device_types`. Driving-Adapter
        (M5-Welle-6b `GET /runs/{id}/devices/state`) iterieren ueber
        die Devices, um per-Geraet-State + Quality zu extrahieren.
        Welle-6b-C2 griff zunaechst auf `_devices` direkt zu (cast
        + private-Attr); die Review-Folge hebt den Zugriff auf eine
        oeffentliche Property, damit ein Future-Refactor (Rename,
        Container-Wechsel) den Adapter typed bricht statt silent
        am Laufzeit-cast vorbei.
        """
        return self._devices

    @property
    def control_state(self) -> RunStatus:
        """Aktueller `RunStatus`-Lifecycle-State (M5 Welle 4a, ADR
        0039 Decision 13).

        Read-only Cache des Repository-Status; nur `request_*`-
        Methoden mutieren das Feld. Default ``"pending"`` bis zum
        ersten erfolgreichen `tick()` oder `request_resume()` —
        der erste Tick flippt das State auf ``"running"`` als
        Side-Effect (Pre-Tick-Guard-Pfad). Externer asyncio-Tick-
        Driver liest dieses Property, um den Loop bei
        ``stopped``/``completed`` zu verlassen.
        """
        return self._control_state

    def request(self, action: ControlAction) -> None:
        """Setzt `_control_state` gemaess Welle-4a-Transition-Matrix
        (M5 Welle 4a, ADR 0039 Decision 13).

        ``action`` ist eines von ``"pause"``/``"resume"``/``"stop"``
        — gespiegelt aus dem HTTP-`ControlRequest`-Body (ADR 0037
        Decision API-1). Erlaubte Transitions:

        - ``pause`` aus ``pending``/``running`` → ``paused``.
        - ``resume`` aus ``pending``/``paused`` → ``running``.
        - ``stop`` aus ``pending``/``running``/``paused`` →
          ``stopped``.
        - Idempotente Wiederholung auf demselben State ist No-op.
        - Sonst: `TickLoopInvalidTransitionError`.

        Reihenfolge: Guard (Invalid-Transition-Check) → Repository-
        Write (Persistenz-Wahrheit, sofern Port gesetzt) → Cache-
        Set. Bei `run_repository=None` skippt der Mirror-Step;
        der Cache-Set bleibt.
        """
        target_state, allowed_from = _CONTROL_ACTION_TRANSITIONS[action]
        if self._control_state == target_state:
            return
        if self._control_state not in allowed_from:
            raise TickLoopInvalidTransitionError(
                run_id=self._run_id,
                current_state=self._control_state,
                target_state=target_state,
            )
        if self._run_repository is not None:
            self._run_repository.update_status(self._run_id, target_state)
        self._control_state = target_state

    def finalize(self) -> tuple[ReplayDelta, ...]:
        """M7-Welle-1b-b (ADR 0049 §2.1): idempotenter Run-Terminal-
        Hook fuer den deterministischen Replay-Diff.

        Der externe Driver (bzw. der Lifespan-`stop()`-Pfad) ruft
        `finalize()` am Loop-Ende; die Diff-Logik sitzt **hier im
        Core-Spine** (GG-AR-P-003/007), nicht im Driver. `finalize()`
        ist idempotent (`_finalized`-Flag → genau eine Emission) und
        aendert `control_state` **nicht** (`"completed"` wird nicht
        auto-gesetzt).

        No-op, wenn keine Replay-Bindung konfiguriert ist
        (`replay_snapshot`/`replay_reference_run_id`/`run_repository`
        nicht alle gesetzt). Sonst: `GG-TERM-002/003`-MVP-Preflight
        (ADR 0049 §2.3) → bei Mismatch **oder fehlenden Lauf-Metadaten
        (`RunNotFoundError`)** sauberer Reject (kein Status, Log statt
        Crash); sonst `diff_replay()` + `replay_diff_status`-Emission +
        `GG-SAFE-006`-Detail-Log. Gibt die `ReplayDelta`-Tupel
        zurueck (Test-/Caller-Evidence; der Driver verwirft sie).

        **Idempotenz-/Retry-Vertrag (C2-Review-Folge F3):** das
        `_finalized`-Flag wird erst nach einem **entschiedenen**
        Ausgang gesetzt (no-op / Reject / erfolgreiche Emission). Ein
        harter I/O-Fehler (z. B. DB-Ausfall im `read_samples`) laesst
        das Flag `False` und propagiert — ein spaeterer `finalize()`-
        Aufruf darf erneut versuchen (statt einen Crash als erledigte
        Emission zu verbuchen).
        """
        if self._finalized:
            return ()
        snapshot = self._replay_snapshot
        reference_run_id = self._replay_reference_run_id
        repository = self._run_repository
        if snapshot is None or reference_run_id is None or repository is None:
            self._finalized = True
            return ()
        try:
            mismatch = self._replay_preflight_mismatch(repository, reference_run_id)
            if mismatch is not None:
                self._log_replay_reject(reference_run_id, reason=mismatch)
                self._finalized = True
                return ()
            expected = snapshot.read_samples(reference_run_id)
            actual = snapshot.read_samples(self._run_id)
            deltas = diff_replay(expected, actual, tick_ms=self._tick_ms)
            self._emit_replay_diff_status(deltas, reference_run_id)
        except RunNotFoundError:
            # Fehlende Referenz-/Lauf-Metadaten → sauberer Reject (kein
            # valider Vergleich moeglich), kein Crash im Terminal-Pfad
            # (C2-Review-Folge F2). `_finalized` bleibt gesetzt: eine
            # fehlende Metadaten-Zeile erscheint nicht durch Retry.
            self._log_replay_reject(reference_run_id, reason="run_metadata_missing")
            self._finalized = True
            return ()
        else:
            # Nur bei erfolgreicher Emission als erledigt markieren
            # (C2-Review-Folge F3): ein harter I/O-Fehler oben laesst
            # `_finalized` False → Retry moeglich.
            self._finalized = True
            return deltas

    def _log_replay_reject(self, reference_run_id: str, *, reason: str) -> None:
        """ADR 0049 §2.3: strukturierter Reject-Log, wenn der Replay-Diff
        **nicht** ausgefuehrt wird (Preflight-Feld-Mismatch oder fehlende
        Lauf-Metadaten). Es wird **kein** `replay_diff_status` emittiert —
        die Metrik bleibt nur fuer valide Vergleiche definiert (§2.4);
        der Reject ist nur ueber `log_port` sichtbar (bekannte R3)."""
        self._obs_log(
            "warning",
            f"replay diff skipped: {reason}",
            event_id="replay_preflight_mismatch",
            attributes={
                "run_id": self._run_id,
                "reference_run_id": reference_run_id,
                "field": reason,
            },
        )

    def _replay_preflight_mismatch(
        self,
        repository: RunRepositoryPort,
        reference_run_id: str,
    ) -> str | None:
        """`GG-TERM-002/003`-MVP-Preflight (ADR 0049 §2.3): erstes
        ungleiches der 5 strukturierten `RunMetadata`-Felder zwischen
        Referenz- und aktuellem Lauf, sonst `None`. Ein Diff
        ungleich-konfigurierter Laeufe ist fachlich bedeutungslos."""
        reference = repository.get_by_id(reference_run_id)
        current = repository.get_by_id(self._run_id)
        for field in _REPLAY_PREFLIGHT_FIELDS:
            if getattr(reference, field) != getattr(current, field):
                return field
        return None

    def _emit_replay_diff_status(
        self,
        deltas: tuple[ReplayDelta, ...],
        reference_run_id: str,
    ) -> None:
        """ADR 0049 §2.4/§2.5: binaerer `replay_diff_status`-Gauge
        (1.0 clean / 0.0 diverged; nur **fachliche** Deltas zaehlen
        als Divergenz) + maschinenlesbare `GG-SAFE-006`-Detail-
        Evidence pro `ReplayDelta` via `log_port`."""
        diverged = any(
            delta.classification is ReplayDeltaClassification.FACHLICH for delta in deltas
        )
        self._obs_gauge(
            "replay_diff_status",
            0.0 if diverged else 1.0,
            attributes={
                "run_id": self._run_id,
                "reference_run_id": reference_run_id,
                "status": "diverged" if diverged else "clean",
            },
        )
        for delta in deltas:
            # Festes `warning`-Level: ein Replay-Delta ist immer
            # auffaellig; die `fachlich`/`volatil`-Klassifikation bleibt
            # maschinenlesbar im `classification`-Attribut (GG-SAFE-006).
            self._obs_log(
                "warning",
                f"replay delta {delta.path}",
                event_id="replay_diff_delta",
                attributes={
                    "run_id": self._run_id,
                    "reference_run_id": reference_run_id,
                    "path": delta.path,
                    "expected": delta.expected,
                    "actual": delta.actual,
                    "tick": delta.tick,
                    "device_id": delta.device_id,
                    "classification": delta.classification.value,
                },
            )

    @property
    def unknown_source_count(self) -> int:
        """Welle-6a-Review M-3: kumulative Anzahl von TelemetryPoints
        mit `power_kw`-Metric und unbekanntem `source`-Tag (nicht in
        `_BILANZ_SOURCE_BUCKETS`). Forward-Looking-Defense fuer
        Welle-7+/M3-Geraete-Drift (z. B. `WindDevice` mit
        `source='wind'`)."""
        return self._unknown_source_count

    @property
    def unknown_alarm_type_count(self) -> int:
        """Welle-4b-Review-Fix #4: kumulative Anzahl von Raw-Alarms,
        deren Typ `dispatch_alarm_mapper` nicht kennt. Forward-
        Looking-Defense fuer Welle-7+/M3-Geraete, die einen neuen
        Raw-Alarm-Subtyp einfuehren, ohne den Mapper zu erweitern.
        Der Tick laeuft trotzdem durch — der Counter macht die
        Drift sichtbar."""
        return self._unknown_alarm_type_count

    @property
    def pending_agent_commands(self) -> tuple[Command, ...]:
        """M3-Welle-3-Review-Folge-2 F-1 (2026-05-21): Read-only-
        Sicht auf die Commands, die der Welle-3-D2-Hook von Agents
        gesammelt hat. Welle 4 wird einen Drain-Mechanismus
        einfuehren (Scheduler-Push, `apply_command`-Pfad, o. ae.).

        Rueckgabe ist `tuple[...]`-Snapshot der internen Liste,
        damit Aufrufer den Buffer nicht versehentlich mutieren.
        """
        return tuple(self._pending_agent_commands)

    # ------------------------------------------------------------------
    # DeviceProtocolPort-Lifecycle (M4 Welle 1, ADR 0030 §2.2)
    # ------------------------------------------------------------------
    # Caller-Scope-Lifecycle: Caller wrappt die bestehende Tick-Schleife
    # in `try/finally` um `start_protocol_ports()`/`stop_protocol_ports()`,
    # weil `TickLoop` keine `run(ticks)`-Methode hat (ADR 0030 §2.2
    # Alternative A3 verworfen — Tick-Granularitaet aus GG-SIM-001/
    # GG-ARCH-007 bleibt).
    # ------------------------------------------------------------------
    def start_protocol_ports(self) -> None:
        """Startet die konfigurierten `DeviceProtocolPort`-Adapter
        in **FIFO**-Reihenfolge (Tuple-Index aufsteigend).

        No-op bei `protocol_ports=None` (Replay-Mode-Skip).

        **Partial-Start-Failure-Vertrag (ADR 0030 §2.2)**: wirft
        `protocol_ports[i].start()` (mit i > 0) eine Exception,
        wird **Best-Effort-Cleanup** in **LIFO**-Reihenfolge
        durchgefuehrt — die Indizes `0..i-1` werden mit `stop()`
        abgebaut. Die erste Exception aus dem Cleanup wird als
        `__context__` an die Original-Start-Exception gehaengt
        (Pythons Auto-Context wird vorher explizit gebrochen,
        um Zyklen zu vermeiden). Die Original-Start-Exception
        propagiert; weitere Cleanup-Exceptions gehen in Welle 1
        verloren — Welle-2-Schaerfung kann ein
        `BaseExceptionGroup`-Pattern einfuehren.

        Erfolg: `self._started_protocol_port_indices` traegt alle
        i in FIFO, sodass `stop_protocol_ports()` in LIFO abbauen
        kann.
        """
        if self._protocol_ports is None:
            return
        started: list[int] = []
        try:
            for idx, port in enumerate(self._protocol_ports):
                port.start()
                started.append(idx)
        except DeviceProtocolPortError as start_exc:
            # Adapter-Vertrag (ADR 0030 §2.1): Library-Exceptions
            # werden adapter-intern in `DeviceProtocolPortError`-
            # Subclasses gewrappt; TickLoop catched ausschliesslich
            # typed Errors (AC-TYPED-ERRORS-konform, Boundary-
            # Translation gehoert in Adapter, nicht in Core).
            first_cleanup_exc: DeviceProtocolPortError | None = None
            for idx in reversed(started):
                try:
                    self._protocol_ports[idx].stop()
                except DeviceProtocolPortError as stop_exc:
                    if first_cleanup_exc is None:
                        first_cleanup_exc = stop_exc
            self._started_protocol_port_indices = []
            if first_cleanup_exc is not None:
                # Pythons Auto-Context im except-Block setzt
                # `first_cleanup_exc.__context__ = start_exc` — das
                # wuerde mit unserer Inversion einen Zyklus bauen.
                # Auto-Context explizit brechen, dann ADR-konform
                # `start_exc.__context__ = first_cleanup_exc` setzen.
                first_cleanup_exc.__context__ = None
                start_exc.__context__ = first_cleanup_exc
            raise
        self._started_protocol_port_indices = started

    def stop_protocol_ports(self) -> None:
        """Stoppt die zuvor mit `start_protocol_ports()` erfolgreich
        gestarteten `DeviceProtocolPort`-Adapter in **LIFO**-
        Reihenfolge (Tuple-Index absteigend).

        No-op bei `protocol_ports=None` (Replay-Mode-Skip).

        **Idempotenz-Vertrag (ADR 0030 §2.2)**: nach dem ersten
        Aufruf ist `self._started_protocol_port_indices` leer; ein
        zweiter Aufruf ist No-op. Auch nach erfolglosem
        `start_protocol_ports()` (Partial-Cleanup ist schon
        gelaufen) ist `stop_protocol_ports()` No-op.

        Welle-1-Vertrag: die erste Stop-Exception propagiert
        ungewrappt — weitere Stops in der LIFO-Schleife laufen
        nicht mehr durch. Welle-2-Schaerfung kann ein
        `BaseExceptionGroup`-Pattern einfuehren, sodass alle Stops
        in einer Group propagiert werden.
        """
        if self._protocol_ports is None:
            return
        for idx in reversed(self._started_protocol_port_indices):
            self._protocol_ports[idx].stop()
        self._started_protocol_port_indices = []

    def tick(self) -> TickResult:
        """Schiebt die Simulationszeit um `tick_ms` vor und faehrt
        die Welle-6b-Split-Iteration durch (ADR 0021 §2.7/§2.8):

        1. Clock advance, Scheduler-Events poppen (M1).
        2. **Vor-Tick-Block** (ADR 0021 §2.5): LoadProfile-Overlay
           + LoadEvent-Overlay -> `apply_command(set_power_kw)` an
           LoadDevices; sammelt manuelle Override-IDs fuer
           GridConnection (falls Profile/Event auf eine
           GridConnection-ID zielen).
        3. **Vor-Tick-Block Schritt A2** (ADR 0022 §2.4): Fault-
           Injection-Hook auf alle Devices, falls `fault_port`
           gesetzt. Skippt bei `fault_port=None` (Default).
           Order-Pflicht: vor erster Device-Iteration, damit
           Faults in derselben Tick wirksam sind.
        4. **Erste Iteration**: PV/Load/Battery/SmartMeter ticken
           (alle ausser `GridConnectionDevice`). Telemetry sammeln
           + Bilanz-Aggregation in `generation`/`load`/`storage`-
           Buckets.
        5. **Auto-Schluss-Berechnung** (ADR 0021 §2.7): pro
           GridConnection ohne manuellen Override
           `apply_command(set_power_kw, -pre_grid_residual)`.
        6. **Zweite Iteration**: GridConnection-Devices ticken;
           Telemetry sammeln + `grid_connection`-Bucket.
        7. `grid_model.update(...)` mit allen vier Bilanz-Werten.

        Welle-4-Scope: ohne Devices/grid_model bleibt das
        Verhalten identisch zur M1-Welle-4-Spine.
        """
        # M5-Welle-4a (ADR 0039 Decision 13) — Pre-Tick-Guard
        # GANZ am Anfang. `paused` skippt den kompletten Tick-Body
        # (keine Agent-Validierung, kein Span, keine Clock-Advance);
        # `stopped`/`completed` wirft `TickLoopStoppedError`. Der
        # externe asyncio-Tick-Driver soll den Loop verlassen,
        # sobald `control_state` auf terminal flippt — der Guard ist
        # eine zweite Schutzschicht.
        if self._control_state == "paused":
            return TickResult.paused_result(
                tick=self._tick_count,
                simulation_time=self._clock.now(),
            )
        if self._control_state in ("stopped", "completed"):
            raise TickLoopStoppedError(
                run_id=self._run_id,
                control_state=self._control_state,
            )
        # `pending` flippt beim ersten produktiven Tick auf
        # `running` (mit Repository-Mirror, falls konfiguriert) —
        # damit `GET /runs/{id}/status` nach dem ersten Tick den
        # `running`-State sieht ohne explizites `request_resume`.
        if self._control_state == "pending":
            self._control_state = "running"
            if self._run_repository is not None:
                self._run_repository.update_status(self._run_id, "running")

        # Schritt A0v (M3-Welle-4a, ADR 0026 §2.1) — Pre-Clock-
        # Target-Validierung des Pending-Agent-Command-Buffers.
        # Laeuft VOR `clock.advance(...)` und `scheduler.pop_due(...)`,
        # damit ein `AgentInvalidCommandTargetError` den Tick
        # komplett unangetastet laesst (Atomizitaets-Vertrag).
        if self._pending_agent_commands:
            commands_to_apply: tuple[Command, ...] = tuple(self._pending_agent_commands)
            for command in commands_to_apply:
                if command.target_device_id not in self._device_by_id:
                    raise AgentInvalidCommandTargetError(
                        command.target_device_id, command.command_id
                    )
        else:
            commands_to_apply = ()

        # M3-Welle-5-Review-Folge H-1: Outer-Tick-Span im try/finally,
        # damit eine Body-Exception keinen ungeschlossenen Span
        # hinterlaesst. Inner-Spans (`fault.inject`, `agent.tick`)
        # haben die Garantie bereits; der Outer-Tick-Span braucht sie
        # ebenso. Body in `_run_tick_body` extrahiert, damit `tick()`
        # lesbar bleibt und der try/finally nicht 130 Zeilen wrappt.
        #
        # Welle-5-Review-Folge L-1 ist im Body geloest: `tick_end`-Log
        # + `tick_count`-Counter laufen VOR der Span-Close, damit
        # OTLP-Korrelations-Konsumenten beide Telemetrie-Events als
        # Tick-Member sehen.
        #
        # Pre-Clock-Validierung (A0v) bleibt VOR `_obs_start_span` —
        # eine A0v-Exception soll keinen Span oeffnen.
        tick_event_id = f"tick-{self._tick_count}"
        tick_span = self._obs_start_span(
            "tick.cycle",
            attributes={"tick": self._tick_count, "run_id": self._run_id},
        )
        try:
            return self._run_tick_body(commands_to_apply, tick_event_id, tick_span)
        finally:
            self._obs_end_span(tick_span)

    def _run_tick_body(
        self,
        commands_to_apply: tuple[Command, ...],
        tick_event_id: str,
        tick_span: SpanContext | None,
    ) -> TickResult:
        """M3-Welle-5-Review-Folge H-1: Body-Extraktion fuer den
        try/finally-Span-Wrap in `tick()`. Vertrag identisch zu
        Welle-4a-tick — A0a/A/A2/B/C/D/D2/E in derselben Reihenfolge.
        Aufrufer (`tick()`) garantiert, dass `tick_span` (sofern
        non-None) im finally geschlossen wird, auch wenn der Body
        throwet.

        Slice 027 Paket D: Schritt-A0a/A2/D2 in eigene Helper-Methoden
        extrahiert (`_apply_pending_agent_commands`,
        `_apply_fault_injection`, `_run_agent_tick_phase`); PLR0915-Drop.
        Reihenfolge bleibt zwingend A0a → A → A2 → B → C → D → D2 → E
        (ADR 0026 §2.1; Determinismus-Vertrag aus M3-Welle-2-Property-
        Tests).
        """
        self._obs_log(
            "info",
            "tick_begin",
            event_id=tick_event_id,
            attributes={"tick": self._tick_count},
        )

        self._clock.advance(self._tick_ms)
        now = self._clock.now()
        popped = tuple(self._scheduler.pop_due(now))

        self._obs_gauge(
            "event_queue_len",
            float(len(popped)),
            attributes={"run_id": self._run_id},
        )

        context = DeviceTickContext(
            tick=self._tick_count,
            simulation_time=now,
            tick_ms=self._tick_ms,
        )
        emitted: list[TelemetryPoint] = []
        # Welle-6b-Review M-1: `list[str]` statt `set[str]` — die
        # Reihenfolge ist deterministisch (Konstruktor-Reihenfolge),
        # und O(N) `in`-Check ist bei typisch ≤ 2 GridConnections
        # vernachlaessigbar gegen das Determinismus-Risiko von
        # Set-Hash-Iteration.
        manual_override_grid_ids: list[str] = []
        bucket_sums: dict[str, Decimal] = {
            "generation": _ZERO,
            "load": _ZERO,
            "storage": _ZERO,
            "grid_connection": _ZERO,
        }
        unknown_count = 0

        with _tick_loop_decimal_context():
            # Schritt A0a — Apply der in A0v validierten Pending-Agent-Commands.
            self._apply_pending_agent_commands(commands_to_apply, manual_override_grid_ids)
            # Schritt A — Vor-Tick-Block (ADR 0021 §2.5).
            # Welle-6b-Review H-3: Event-Window-Check nutzt die
            # Tick-Start-Zeit (`now - tick_ms`).
            tick_start_ms = now - self._tick_ms
            self._consume_load_inputs_into(
                tick_start_ms=tick_start_ms,
                now_ms=now,
                manual_override_grid_ids=manual_override_grid_ids,
            )
            # Schritt A2 — Fault-Injection (M3-Welle-1, ADR 0022 §2.4).
            self._apply_fault_injection(context, tick_span)
            grid_devices = [d for d in self._devices if isinstance(d, GridConnectionDevice)]
            non_grid_devices = [d for d in self._devices if not isinstance(d, GridConnectionDevice)]
            # Schritt B — Erste Iteration (ohne GridConnection).
            unknown_count += self._run_device_iteration(
                non_grid_devices, context, emitted, bucket_sums
            )
            # Schritt C — GridConnection-Auto-Schluss (ADR 0021 §2.7).
            self._apply_grid_connection_auto_close(
                grid_devices, bucket_sums, manual_override_grid_ids, now
            )
            # Schritt D — Zweite Iteration (GridConnection ticken).
            unknown_count += self._run_device_iteration(grid_devices, context, emitted, bucket_sums)
            # Schritt D2 — Agent-Tick (M3-Welle-3, ADR 0023 §2.4).
            self._run_agent_tick_phase(context, tick_span)
            # Schritt E — Bilanz-Aggregation.
            if self._grid_model is not None:
                self._grid_model.update(
                    generation_kw=bucket_sums["generation"],
                    load_kw=bucket_sums["load"],
                    storage_kw=bucket_sums["storage"],
                    grid_connection_kw=bucket_sums["grid_connection"],
                )
        self._unknown_source_count += unknown_count

        # M7-Welle-3a (ADR 0052 §2.2): max_age-STALE-Stage VOR dem
        # TickResult-Bau — eine Stelle, drei Konsumenten (Stream +
        # Persistenz + Replay sehen identisch markierte Punkte).
        result = TickResult(
            tick=self._tick_count,
            simulation_time=now,
            popped_events=popped,
            emitted_telemetry=tuple(self._apply_max_age_stage(emitted, now)),
            emitted_alarms=self._drain_and_map_device_alarms(now),
        )
        self._tick_count += 1
        self._persist_emitted_telemetry(result)
        # M3-Welle-5 (ADR 0024 §2.6) + Review-Folge L-1: Observability-
        # Hook tick_end. Counter + Log laufen NACH `_tick_count += 1`
        # (damit der naechste `tick()` das frische Inkrement sieht) und
        # VOR der Span-Close — die Span-Close passiert im
        # `tick()`-Wrapper-finally (Review-Folge H-1). Damit liegen
        # `tick_count`-Counter und `tick_end`-Log innerhalb des
        # `tick.cycle`-Spans und OTLP-Korrelations-Konsumenten sehen
        # beide als Tick-Member.
        self._obs_increment(
            "tick_count",
            attributes={"run_id": self._run_id},
        )
        self._obs_log(
            "info",
            "tick_end",
            event_id=tick_event_id,
            attributes={"tick": result.tick, "emitted_count": len(emitted)},
        )
        return result

    def _apply_max_age_stage(self, emitted: list[TelemetryPoint], now: int) -> list[TelemetryPoint]:
        """M7-Welle-3a (ADR 0052 §2.2): `max_age`-`STALE`-Stage.

        Markiert Punkte, deren Sim-Zeitstempel die konfigurierte
        Schwelle ueberschreitet (strikt `>`, ADR 0052 §2.5 —
        Gleichheit ist nicht „ueberschritten"), via
        `dataclasses.replace` mit `Quality.STALE`. Vergleich nur
        ueber Sim-Zeit (`now` = Tick-`simulation_time`; AC-NO-TIME).
        Severity-Override (§2.3): STALE ersetzt nur Qualities mit
        niedrigerer `QUALITY_SEVERITY` (VALID/ESTIMATED/LIMITED);
        schwerere Befunde (FAULT_INJECTED/INVALID/NAN/MISSING)
        dominieren. `max_age_ms=None` (Default) ist der no-op-Pfad.
        """
        if self._max_age_ms is None:
            return emitted
        stale_severity = QUALITY_SEVERITY[Quality.STALE]
        return [
            replace(point, quality=Quality.STALE)
            if (now - point.simulation_time) > self._max_age_ms
            and QUALITY_SEVERITY[point.quality] < stale_severity
            else point
            for point in emitted
        ]

    def _persist_emitted_telemetry(self, result: TickResult) -> None:
        """M7-Welle-1a (ADR 0047 §2.3): append-only Zeitreihen-
        Persistenz der pro Tick emittierten Telemetrie ueber den
        Driven-Sink-Port. Insertion-Reihenfolge = deterministische
        `emitted_telemetry`-Reihenfolge; `None`-Sink skippt (no-op,
        analog `run_repository`)."""
        if self._telemetry_sink is not None:
            self._telemetry_sink.persist(result.emitted_telemetry)

    def _apply_pending_agent_commands(
        self,
        commands_to_apply: tuple[Command, ...],
        manual_override_grid_ids: list[str],
    ) -> None:
        """Schritt A0a (M3-Welle-4a, ADR 0026 §2.1) — Apply der in A0v
        validierten Pending-Agent-Commands.

        Slice 027 Paket D: aus `_run_tick_body` ausgelagert, Reihenfolge
        und Mutation des `manual_override_grid_ids`-Buffers bleiben
        identisch (Determinismus-Vertrag).

        Agent-Commands auf GridConnection-IDs zaehlen als manueller
        Auto-Close-Override (ergaenzen `manual_override_grid_ids`);
        LoadEvent/Profile-Overlay in Schritt A laeuft danach und
        gewinnt auf LoadDevices (Baseline-Praezedenz aus Welle-6b).
        Buffer-Clear nur nach erfolgreichem Apply-Durchlauf (ADR 0026
        §2.1 Exception-Pfade).
        """
        for command in commands_to_apply:
            target = self._device_by_id[command.target_device_id]
            target.apply_command(command)
            if (
                isinstance(target, GridConnectionDevice)
                and target.device_id not in manual_override_grid_ids
            ):
                manual_override_grid_ids.append(target.device_id)
        # Buffer-Clear NUR nach erfolgreichem Apply-Durchlauf (ADR 0026
        # §2.1 Exception-Pfad). Eine `apply_command(...)`-Exception oben
        # laesst den Buffer ungeleert, damit Resume die Pending-Commands
        # nochmal sehen kann.
        self._pending_agent_commands.clear()

    def _apply_fault_injection(
        self,
        context: DeviceTickContext,
        tick_span: SpanContext | None,
    ) -> None:
        """Schritt A2 — Fault-Injection (M3-Welle-1, ADR 0022 §2.4).

        Slice 027 Paket D: aus `_run_tick_body` ausgelagert. `None`-
        Default skippt sauber. Trace-Wrap aus M3-Welle-5 (ADR 0024
        §2.6) bleibt mit try/finally erhalten.
        """
        if self._fault_port is None:
            return
        fault_span = self._obs_start_span(
            "fault.inject",
            parent=tick_span,
            attributes={"tick": self._tick_count},
        )
        try:
            self._fault_port.apply_active_faults(self._devices, context)
        finally:
            self._obs_end_span(fault_span)

    def _run_agent_tick_phase(
        self,
        context: DeviceTickContext,
        tick_span: SpanContext | None,
    ) -> None:
        """Schritt D2 — Agent-Tick (M3-Welle-3, ADR 0023 §2.4).

        Slice 027 Paket D: aus `_run_tick_body` ausgelagert. Agents
        laufen NACH der Geraete-Iteration und VOR `grid_model.update(...)`
        (Architektur §6 Schritt 7). `None`-Bus-Default skippt sauber.

        Welle-3-Review-Folge-2 F-1: emittierte Commands landen im
        `_pending_agent_commands`-Buffer (nicht verworfen). Welle 4
        verdrahtet den Drain-Pfad.
        """
        if self._agent_bus is None:
            return
        for agent in self._agents:
            agent_span = self._obs_start_span(
                "agent.tick",
                parent=tick_span,
                attributes={
                    "agent_id": agent.agent_id,
                    "tick": self._tick_count,
                },
            )
            try:
                self._pending_agent_commands.extend(agent.tick(context, self._agent_bus))
            finally:
                self._obs_end_span(agent_span)

    def _run_device_iteration(
        self,
        devices: Sequence[DeviceModel],
        context: DeviceTickContext,
        emitted: list[TelemetryPoint],
        bucket_sums: dict[str, Decimal],
    ) -> int:
        """Ruft `device.tick(context)` fuer alle uebergebenen
        Devices, konkateniert Telemetrie in `emitted` und summiert
        `power_kw`-Werte nach `TelemetryPoint.source` in
        `bucket_sums`. Liefert die Anzahl der unbekannten
        source-Tags (Welle-6a-Review-M-3-Counter)."""
        unknown = 0
        for device in devices:
            outcome = device.tick(context)
            for point in outcome.telemetry:
                emitted.append(point)
                if point.metric != _POWER_KW_METRIC:
                    continue
                bucket = _BILANZ_SOURCE_BUCKETS.get(point.source)
                if bucket is None:
                    unknown += 1
                    continue
                bucket_sums[bucket] += point.value
        return unknown

    def _apply_grid_connection_auto_close(
        self,
        grid_devices: Sequence[DeviceModel],
        bucket_sums: dict[str, Decimal],
        manual_override_grid_ids: list[str],
        now_ms: int,
    ) -> None:
        """Welle-6b (ADR 0021 §2.7): GridConnection-Auto-Schluss
        nach erster Device-Iteration. Pro GridConnection ohne
        manuellen Override setzt
        `power_kw := -(generation - load - storage)`. Manuelle
        Heuristik: nur LoadEvent/LoadProfile qualifizieren — keine
        M1-Scheduler-Events (Welle-6b-Review-Round-1-High-3)."""
        pre_grid_residual = bucket_sums["generation"] - bucket_sums["load"] - bucket_sums["storage"]
        for grid_dev in grid_devices:
            if grid_dev.device_id in manual_override_grid_ids:
                continue
            # Welle-6b-Review M-5: `result=IGNORED` ist hier ein
            # **Konstruktor-Default**, kein semantischer Endstatus.
            # `Command.result` ist by-`GG-DATA-004` ein End-Status —
            # eine in-flight `result=None` ist out-of-scope. Den
            # echten Endstatus liefert der Rueckgabewert von
            # `apply_command`; das vorgegebene `IGNORED` wird durch
            # die Geraete-Validierung ueberschrieben (intern als
            # Outcome zurueckgegeben), nicht hier persistiert.
            grid_dev.apply_command(
                Command(
                    command_id=(f"auto_close_{grid_dev.device_id}_tick_{self._tick_count}"),
                    simulation_time=now_ms,
                    target_device_id=grid_dev.device_id,
                    type="set_power_kw",
                    payload={"value": -pre_grid_residual},
                    validation_status="validated",
                    result=CommandResult.IGNORED,
                )
            )

    def _consume_load_inputs_into(
        self,
        *,
        tick_start_ms: int,
        now_ms: int,
        manual_override_grid_ids: list[str],
    ) -> None:
        """Welle-6b (ADR 0021 §2.5): Jedes-Tick-Baseline +
        Profile/Event-Overlay an LoadDevices anwenden.

        Schritt:
        1. Baseline: pro LoadDevice `intent = rated_power_kw`
           (Welle-6b-Review-Befund H-2: TickLoop besitzt
           `set_power_kw` an LoadDevices exklusiv — externe
           `apply_command`-Aufrufe zwischen Ticks werden im
           Folge-Tick durch die Baseline ueberschrieben).
        2. Profile-Overlay: LoadProfile setzt intent fuer ihren
           `target_device_id` auf `tick_values[profile_index]`.
        3. Event-Overlay: aktiver LoadEvent setzt intent auf
           `event.power_kw` (Window-Check `start_s <= now_s <
           start_s + duration_s` mit `now_s = tick_start_ms/1000`
           — Welle-6b-Review H-3).
        4. `apply_command(set_power_kw, value=intent)` pro Device.

        Wenn `target_device_id` eine GridConnection ist, wird die
        ID in `manual_override_grid_ids` getragen (Welle-6b-Auto-
        Schluss-Heuristik aus §2.7). Welle-6b-Review M-1:
        `list[str]` statt `set[str]` — Determinismus-Pflicht
        (kein Hash-Seeding bei kuenftiger Iteration).
        """
        intent_by_id: dict[str, Decimal] = dict(self._load_baseline_by_id)

        # Profile-Overlay.
        for profile in self._active_load_profiles:
            target_dev = self._device_by_id.get(profile.target_device_id)
            if target_dev is None:
                continue
            profile_index = (self._tick_count * self._tick_ms) // profile.tick_ms
            tick_values = profile.tick_values
            value = tick_values[min(profile_index, len(tick_values) - 1)]
            intent_by_id[profile.target_device_id] = value
            if (
                isinstance(target_dev, GridConnectionDevice)
                and profile.target_device_id not in manual_override_grid_ids
            ):
                manual_override_grid_ids.append(profile.target_device_id)

        # Event-Overlay. Welle-6b-Review H-3: `now_s` ist die Tick-
        # Start-Zeit, damit ein Event mit `duration_s = tick_ms/1000`
        # waehrend genau des ersten Tick-Intervalls als aktiv gilt.
        _ = now_ms  # Tick-End-Zeit nicht mehr fuer Window-Check noetig.
        now_s = Decimal(tick_start_ms) / Decimal(1000)
        for event in self._active_load_events:
            event_end_s = event.start_s + event.duration_s
            if not (event.start_s <= now_s < event_end_s):
                continue
            target_dev = self._device_by_id.get(event.target_device_id)
            if target_dev is None:
                continue
            intent_by_id[event.target_device_id] = event.power_kw
            if (
                isinstance(target_dev, GridConnectionDevice)
                and event.target_device_id not in manual_override_grid_ids
            ):
                manual_override_grid_ids.append(event.target_device_id)

        # apply_command pro Device mit berechnetem intent.
        for device_id, intent in intent_by_id.items():
            device = self._device_by_id[device_id]
            device.apply_command(
                Command(
                    command_id=(f"baseline_{device_id}_tick_{self._tick_count}"),
                    simulation_time=now_ms,
                    target_device_id=device_id,
                    type="set_power_kw",
                    payload={"value": intent},
                    validation_status="validated",
                    result=CommandResult.IGNORED,
                )
            )

    def snapshot(self) -> Mapping[str, object]:
        """Liefert den TickLoop-State als `SnapshotEnvelope`-konformes
        Mapping (`GG-SIM-005`).

        Welle 6a (ADR 0015):
        - `version` ist `2`.
        - `sub_snapshots` enthaelt zusaetzlich zu M1-Welle-4-Keys
          (`scheduler`, `random_root`) je Device einen
          `devices.<device_type>.<device_id>`-Key (sofern Devices
          ueber den Konstruktor injiziert wurden) und einen
          `grid_model`-Key (sofern `grid_model` injiziert).

        `random_root` wird per `RandomPort.snapshot_as_mapping()`
        (`ADR 0010`) als Mapping eingebunden — keine Encoder-Logik
        in der Domain.
        """
        sub_snapshots: dict[str, Mapping[str, object]] = {
            "scheduler": self._scheduler.snapshot(),
            "random_root": self._random.snapshot_as_mapping(),
        }
        for device in self._devices:
            device_type = _device_type_for(device)
            device_id = device.device_id
            # Welle-6a-Review L-5: Punkt im device_id kollidiert mit
            # dem `devices.<type>.<id>`-Schluessel-Schema (dot-getrennt).
            # Welle-6b-Scenario-Loader sollte device_ids vor der
            # Konstruktion validieren; defensiver Assert hier macht
            # die Kollision sichtbar, statt eine still-falsche
            # Sub-Snapshot-Key-Struktur zu produzieren.
            if "." in device_id:
                raise TickLoopUnknownDeviceTypeError(
                    f"{type(device).__name__}(device_id={device_id!r})",
                    tuple(_DEVICE_TYPE_BY_CLASS_NAME),
                )
            key = f"devices.{device_type}.{device_id}"
            sub_snapshots[key] = device.snapshot()
        if self._grid_model is not None:
            sub_snapshots["grid_model"] = self._grid_model.snapshot()
        # M3-Welle-4a (ADR 0026 §2.6): Agent-Foundation-State-
        # Sub-Snapshots. `agent_bus` und `pending_agent_commands`
        # werden nur eingehaengt, wenn sie nicht-trivial sind —
        # alte Snapshots ohne diese Keys bleiben backward-kompatibel.
        if self._agent_bus is not None:
            sub_snapshots["agent_bus"] = self._agent_bus.snapshot()
        if self._pending_agent_commands:
            sub_snapshots["pending_agent_commands"] = _serialize_pending_agent_commands(
                self._pending_agent_commands
            )
        # M3-Welle-4b (ADR 0027 §2.4): konkrete Agent-Instanz-
        # Sub-Snapshots `agents.<agent_type>.<agent_id>` (additiv
        # per ADR 0015 §2.3 — kein Schema-Bump). Welle-4b-only
        # fuer Agents in `_AGENT_TYPE_BY_CLASS_NAME`; unbekannte
        # Klassen werden hier defensiv geskippt (Forward-Compat
        # fuer Welle-4c+-Agent-Typen, die noch nicht registriert
        # sind — die wuerden vom Validator/Loader-Pfad bereits
        # vor dem Konstruktor abgewiesen).
        for agent in self._agents:
            agent_class_name = type(agent).__name__
            if agent_class_name not in _AGENT_TYPE_BY_CLASS_NAME:
                continue
            agent_type = _AGENT_TYPE_BY_CLASS_NAME[agent_class_name]
            agent_id = agent.agent_id
            if "." in agent_id:
                raise TickLoopUnknownDeviceTypeError(
                    f"{agent_class_name}(agent_id={agent_id!r})",
                    tuple(_AGENT_TYPE_BY_CLASS_NAME),
                )
            sub_snapshots[f"agents.{agent_type}.{agent_id}"] = agent.snapshot()
        return {
            "version": _SNAPSHOT_VERSION,
            "run_id": self._run_id,
            "simulation_time": self._clock.now(),
            "tick_count": self._tick_count,
            "tick_ms": self._tick_ms,
            "sub_snapshots": sub_snapshots,
        }

    @classmethod
    def from_snapshot(
        cls,
        state: Mapping[str, object],
        *,
        clock: ClockPort,
        random: RandomPort,
        devices: tuple[DeviceModel, ...] = (),
        grid_model: GridModelBilanz | None = None,
        active_load_events: tuple[LoadEvent, ...] = (),
        active_load_profiles: tuple[LoadProfile, ...] = (),
        fault_port: FaultPort | None = None,
        agents: tuple[Agent, ...] = (),
        log_port: LogPort | None = None,
        metrics_port: MetricsPort | None = None,
        trace_port: TracePort | None = None,
        protocol_ports: tuple[DeviceProtocolPort, ...] | None = None,
        run_repository: RunRepositoryPort | None = None,
        max_age_ms: int | None = None,
        alarm_id_source: Callable[[], str] | None = None,
        control_state: RunStatus | None = None,
    ) -> TickLoop:
        """Stellt einen `TickLoop` aus einem Snapshot wieder her.

        Aufrufer injiziert `clock` und `random` als bereits restored
        Instanzen (z. B. via `MersenneTwisterRandomPort.from_snapshot`
        und einer Clock, die per `advance` auf
        `state['simulation_time']` gebracht wurde).

        M3-Welle-4a (ADR 0026 §2.6) ergaenzt optionale Runtime-
        Dependency-Kwargs: `devices`, `grid_model`,
        `active_load_events`, `active_load_profiles`, `fault_port`,
        `agents`. Ohne diese Kwargs bleibt der Welle-6a-Pfad
        unveraendert (TickLoop ohne Devices/Agents); mit ihnen wird
        der produktive Resume-Pfad fuer Welle 4a aktiviert,
        einschliesslich `pending_agent_commands`-Drain im ersten
        Tick.

        Resume-Match-Checks:
        - Wenn der Snapshot `devices.<type>.<id>`-Sub-Snapshots
          enthaelt und `devices` injiziert ist, muessen IDs/Typen/
          Snapshot-State exakt passen
          (`TickLoopAgentSnapshotDeviceMismatchError`).
        - Wenn der Snapshot `grid_model`-Sub-Snapshot enthaelt
          und `grid_model` injiziert ist, muss
          `grid_model.snapshot()` exakt zum Sub-Snapshot passen
          (`TickLoopAgentSnapshotGridModelMismatchError`).
        - Wenn ein `grid_model`-Sub-Snapshot vorhanden ist und
          nicht-leere LoadOverlay-Tupel injiziert werden, muessen
          sie zum persistierten GridModel-Overlay-State passen
          (`TickLoopAgentSnapshotLoadOverlayMismatchError`).

        Auto-Bus-Praezedenz: alte Snapshots ohne `agent_bus`-Sub-
        Snapshot mit nicht-leeren `agents` injiziert bekommen
        einen leeren `AgentMessageBus` (gleiche Regel wie im
        Konstruktor).

        Welle-4b-Review-Fix #8 + #3 ergaenzt drei Resume-Kwargs:

        - ``run_repository``: erlaubt dem resumed Loop, weitere
          `request(...)`-Transitions auf den Repository-Status zu
          mirrorn. Ohne den Kwarg waere `_run_repository=None`
          und Cache/Persistenz wuerden silently divergieren.
        - ``alarm_id_source``: Test-Determinismus-Stub fuer
          `Alarm.alarm_id`; Production-Default ist `uuid.uuid4`.
        - ``control_state``: Run-Lifecycle-State (paused/running/
          stopped/...), den der Caller aus
          `RunRepository.get_status(run_id)` speist. `None`
          behaelt das Default-`pending` und damit den
          First-Tick-Auto-Flip-Pfad — produktiver Resume sollte
          den State immer explizit setzen.

        M7-Welle-3a-Review-Folge F1 ergaenzt ``max_age_ms``:
        Resume-Symmetrie zum Konstruktor-Kwarg (ADR 0052 §2.1) —
        der Caller re-injiziert die `STALE`-Stage-Schwelle wie
        die uebrigen Runtime-Dependencies; ohne das Kwarg liefe
        ein resumed Lauf still mit `max_age_ms=None` (Stage aus)
        und divergierte im Quality-Verhalten vom Original-Lauf.
        Der Snapshot persistiert die Schwelle (wie alle
        injizierten Runtime-Deps) bewusst nicht.
        """
        parsed = _validate_tick_loop_snapshot(state)
        if parsed.version != _SNAPSHOT_VERSION:
            raise TickLoopSnapshotVersionError(_SNAPSHOT_VERSION, parsed.version)
        if clock.now() != parsed.simulation_time:
            raise TickLoopSnapshotClockMismatchError(parsed.simulation_time, clock.now())
        if random.snapshot_as_mapping() != parsed.random_root:
            raise TickLoopSnapshotRandomMismatchError
        scheduler = Scheduler.from_snapshot(parsed.scheduler)
        # M3-Welle-4a Resume-Match-Checks (ADR 0026 §2.6).
        _assert_device_resume_match(parsed.sub_snapshots, devices)
        _assert_grid_model_resume_match(parsed.sub_snapshots, grid_model)
        _assert_load_overlay_resume_match(
            parsed.sub_snapshots, active_load_events, active_load_profiles
        )
        # M3-Welle-4b (ADR 0027 §2.4): bidirektionaler Resume-Match-
        # Check fuer Agent-Instanz-Sub-Snapshots.
        _assert_agent_instance_resume_match(parsed.sub_snapshots, agents)
        # M3-Welle-4a Agent-Foundation-State-Restore (ADR 0026 §2.6).
        agent_bus = _restore_agent_bus_from_snapshot(parsed.sub_snapshots, has_agents=bool(agents))
        pending_commands = _restore_pending_agent_commands(
            parsed.sub_snapshots.get("pending_agent_commands")
        )
        loop = cls(
            run_id=parsed.run_id,
            tick_ms=parsed.tick_ms,
            clock=clock,
            random=random,
            scheduler=scheduler,
            devices=devices,
            grid_model=grid_model,
            active_load_events=active_load_events,
            active_load_profiles=active_load_profiles,
            fault_port=fault_port,
            agent_bus=agent_bus,
            agents=agents,
            log_port=log_port,
            metrics_port=metrics_port,
            trace_port=trace_port,
            protocol_ports=protocol_ports,
            run_repository=run_repository,
            max_age_ms=max_age_ms,
            alarm_id_source=alarm_id_source,
        )
        # `_pending_agent_commands` muss nach Konstruktor-Init
        # gefuellt werden — der Konstruktor initialisiert es leer.
        loop._pending_agent_commands.extend(pending_commands)
        loop._tick_count = parsed.tick_count
        # Welle-4b-Review-Fix #3: Run-Control-State explizit aus
        # dem Caller (RunRepository.get_status) — sonst startet der
        # resumed Loop als `pending` und der erste Tick flippt
        # blind auf `running`, was den Resume eines `paused`-Runs
        # silently aufhebt.
        if control_state is not None:
            loop._control_state = control_state
        return loop


# ---------------------------------------------------------------------------
# Snapshot-Validierung (Pattern parallel zu Welle 2/3 — Trigger 012
# generalisiert das in Welle 5+).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _ParsedTickLoopSnapshot:
    """Geprueftes Snapshot-Payload mit allen Pflicht-Keys typisiert.

    Liegt ausserhalb `domain/` — AC-DOMAIN-FROZEN gilt hier nicht;
    `frozen=True, slots=True` ist rein pragmatisch (Schreibschutz
    nach Validierung).
    """

    version: int
    run_id: str
    simulation_time: int
    tick_count: int
    tick_ms: int
    scheduler: Mapping[str, object]
    random_root: Mapping[str, object]
    sub_snapshots: Mapping[str, object]


def _validate_tick_loop_snapshot(state: Mapping[str, object]) -> _ParsedTickLoopSnapshot:
    """Prueft Top-Level-Keys/-Typen und Sub-Snapshot-Konvention."""
    missing = _REQUIRED_KEYS - state.keys()
    if missing:
        raise TickLoopSnapshotMissingKeysError(sorted(missing))
    version = _require_int(state, "version")
    run_id = _require_str(state, "run_id")
    simulation_time = _require_int(state, "simulation_time")
    tick_count = _require_int(state, "tick_count")
    tick_ms = _require_int(state, "tick_ms")
    sub_snapshots = state["sub_snapshots"]
    if not isinstance(sub_snapshots, Mapping):
        raise TickLoopSnapshotWrongTypeError(
            "sub_snapshots", "Mapping", type(sub_snapshots).__name__
        )
    missing_subs = _REQUIRED_SUB_SNAPSHOT_KEYS - sub_snapshots.keys()
    if missing_subs:
        raise TickLoopSnapshotMissingKeysError(
            [f"sub_snapshots.{name}" for name in sorted(missing_subs)]
        )
    scheduler_state = _require_sub_mapping(sub_snapshots, "scheduler")
    random_state = _require_sub_mapping(sub_snapshots, "random_root")
    return _ParsedTickLoopSnapshot(
        version=version,
        run_id=run_id,
        simulation_time=simulation_time,
        tick_count=tick_count,
        tick_ms=tick_ms,
        scheduler=scheduler_state,
        random_root=random_state,
        sub_snapshots=sub_snapshots,
    )


def _require_int(state: Mapping[str, object], key: str) -> int:
    value = state[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TickLoopSnapshotWrongTypeError(key, "int", type(value).__name__)
    return value


def _require_str(state: Mapping[str, object], key: str) -> str:
    value = state[key]
    if not isinstance(value, str):
        raise TickLoopSnapshotWrongTypeError(key, "str", type(value).__name__)
    return value


def _require_sub_mapping(sub_snapshots: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = sub_snapshots[name]
    if not isinstance(value, Mapping):
        raise TickLoopSnapshotWrongTypeError(
            f"sub_snapshots.{name}", "Mapping", type(value).__name__
        )
    return value


def _device_type_for(device: DeviceModel) -> str:
    """Liefert das `device_type`-Segment fuer die
    `devices.<device_type>.<device_id>`-Sub-Snapshot-Key-Konstruktion
    (ADR 0015 §2.3). Welle 7+/M3-Geraete muessen ihren Klassen-Namen
    in `_DEVICE_TYPE_BY_CLASS_NAME` registrieren oder eine
    `device_type`-Protocol-Erweiterung erzwingen.

    Welle-6a-Review M-6: Schreib-Pfad-Exception
    `TickLoopUnknownDeviceTypeError` (statt der Lese-Pfad-spezifischen
    `TickLoopSnapshotWrongTypeError`) — Exception-Hierarchie bleibt
    semantisch sauber."""
    class_name = type(device).__name__
    if class_name not in _DEVICE_TYPE_BY_CLASS_NAME:
        raise TickLoopUnknownDeviceTypeError(class_name, tuple(_DEVICE_TYPE_BY_CLASS_NAME))
    return _DEVICE_TYPE_BY_CLASS_NAME[class_name]


# ---------------------------------------------------------------------------
# Agent-Foundation-State-Snapshot-Helpers (M3 Welle 4a, ADR 0026 §2.6)
# ---------------------------------------------------------------------------


_PENDING_COMMAND_FIELDS: Final[tuple[str, ...]] = (
    "command_id",
    "simulation_time",
    "target_device_id",
    "type",
    "payload",
    "validation_status",
    "result",
)


def _serialize_pending_agent_commands(commands: list[Command]) -> Mapping[str, object]:
    """`pending_agent_commands`-Sub-Snapshot-Format (ADR 0026 §2.6).

    `result` wird als `CommandResult`-Stringwert (`enum.name`)
    serialisiert; canonical_json akzeptiert dict/list/str/int/Decimal,
    aber keine Enum-Instanzen.
    """
    return {
        "version": 1,
        "commands": tuple(
            {
                "command_id": command.command_id,
                "simulation_time": command.simulation_time,
                "target_device_id": command.target_device_id,
                "type": command.type,
                "payload": dict(command.payload),
                "validation_status": command.validation_status,
                "result": command.result.name,
            }
            for command in commands
        ),
    }


def _restore_pending_agent_commands(
    raw: object,
) -> tuple[Command, ...]:
    """Rekonstruiert `_pending_agent_commands` aus Sub-Snapshot.

    Fehlt der Sub-Snapshot, ist der Buffer leer (Backward-Compat
    fuer Welle-3-Snapshots).
    """
    if raw is None:
        return ()
    if not isinstance(raw, Mapping):
        raise TickLoopAgentSnapshotWrongTypeError(
            "sub_snapshots.pending_agent_commands", "Mapping", type(raw).__name__
        )
    missing = sorted({"version", "commands"} - raw.keys())
    if missing:
        raise TickLoopAgentSnapshotMissingKeysError("pending_agent_commands", missing)
    version = raw["version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise TickLoopAgentSnapshotWrongTypeError(
            "pending_agent_commands.version", "int", type(version).__name__
        )
    commands_raw = raw["commands"]
    if not isinstance(commands_raw, Sequence) or isinstance(commands_raw, (str, bytes)):
        raise TickLoopAgentSnapshotWrongTypeError(
            "pending_agent_commands.commands", "Sequence", type(commands_raw).__name__
        )
    restored: list[Command] = []
    for index, entry in enumerate(commands_raw):
        restored.append(_restore_pending_command_entry(entry, index))
    return tuple(restored)


def _restore_pending_command_entry(raw: object, index: int) -> Command:
    """Pro-Eintrag-Restore mit typed-Errors fuer Format-Verstoesse.

    Slice 027 Paket D: pro-Feld-Typchecks in
    `_check_pending_command_str_field`/`_check_pending_command_int_field`/
    `_parse_pending_command_payload`/`_parse_pending_command_result`
    extrahiert (C901+PLR0915-Drop).
    """
    if not isinstance(raw, Mapping):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}]", "Mapping", type(raw).__name__
        )
    missing = [field for field in _PENDING_COMMAND_FIELDS if field not in raw]
    if missing:
        raise TickLoopAgentSnapshotMissingKeysError(
            f"pending_agent_commands.commands[{index}]",
            [f"commands[{index}].{field}" for field in missing],
        )
    command_id = _check_pending_command_str_field(raw, index, "command_id")
    simulation_time = _check_pending_command_int_field(raw, index, "simulation_time")
    target_device_id = _check_pending_command_str_field(raw, index, "target_device_id")
    type_value = _check_pending_command_str_field(raw, index, "type")
    payload = _parse_pending_command_payload(raw, index)
    validation_status = _check_pending_command_str_field(raw, index, "validation_status")
    result = _parse_pending_command_result(raw, index)
    return Command(
        command_id=command_id,
        simulation_time=simulation_time,
        target_device_id=target_device_id,
        type=type_value,
        payload=payload,
        validation_status=validation_status,
        result=result,
    )


def _check_pending_command_str_field(raw: Mapping[str, object], index: int, field: str) -> str:
    """Pflicht-`str`-Check fuer ein `pending_agent_commands.commands[i].<field>`."""
    value = raw[field]
    if not isinstance(value, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].{field}",
            "str",
            type(value).__name__,
        )
    return value


def _check_pending_command_int_field(raw: Mapping[str, object], index: int, field: str) -> int:
    """Pflicht-`int`-Check (excl. `bool`) fuer ein Pending-Command-Feld."""
    value = raw[field]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].{field}",
            "int",
            type(value).__name__,
        )
    return value


def _parse_pending_command_payload(raw: Mapping[str, object], index: int) -> dict[str, object]:
    """Payload-Parser (Mapping-Check + dict-Kopie)."""
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].payload",
            "Mapping",
            type(payload).__name__,
        )
    return dict(payload)


def _parse_pending_command_result(raw: Mapping[str, object], index: int) -> CommandResult:
    """`CommandResult`-Enum-Restore aus Snapshot-String."""
    result_raw = raw["result"]
    if not isinstance(result_raw, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].result",
            "str",
            type(result_raw).__name__,
        )
    try:
        return CommandResult[result_raw]
    except KeyError as exc:
        raise TickLoopAgentSnapshotInvalidCommandResultError(index, result_raw) from exc


def _restore_agent_bus_from_snapshot(
    sub_snapshots: Mapping[str, object],
    *,
    has_agents: bool,
) -> AgentMessageBus | None:
    """Rekonstruiert den AgentMessageBus aus Sub-Snapshot oder
    Auto-Bus-Regel (ADR 0026 §2.6).

    - Sub-Snapshot vorhanden → `AgentMessageBus.from_snapshot(...)`.
    - Kein Sub-Snapshot + `has_agents == True` → leerer Bus
      (Auto-Bus-Praezedenz, backward-kompatibel fuer Welle-3-
      Snapshots ohne `agent_bus`-Key bei produktiver Welle-4a-
      Restore mit injizierten Agents).
    - Kein Sub-Snapshot + `has_agents == False` → `None`
      (Welle-6a-Pfad unveraendert).
    """
    raw = sub_snapshots.get("agent_bus")
    if raw is not None:
        if not isinstance(raw, Mapping):
            raise TickLoopAgentSnapshotWrongTypeError(
                "sub_snapshots.agent_bus", "Mapping", type(raw).__name__
            )
        return AgentMessageBus.from_snapshot(raw)
    if has_agents:
        return AgentMessageBus()
    return None


class _DeviceMissingSubSnapshotError(TickLoopAgentSnapshotDeviceMismatchError):
    """Resume-Diagnostik: injizierte Device-ID hat keinen `devices.<type>.<id>`-Slot.

    Slice 027 Paket B TRY003-Drop: Message in `__init__` (statt
    f-string am `raise`-Site).
    """

    def __init__(self, device_id: str, device_type: str, key: str) -> None:
        super().__init__(
            f"injected device {device_id!r} (type={device_type!r}) "
            f"has no matching sub-snapshot key {key!r}"
        )


class _DeviceSnapshotDiffersError(TickLoopAgentSnapshotDeviceMismatchError):
    """Resume-Diagnostik: `device.snapshot()` weicht vom persistierten Sub-Snapshot ab."""

    def __init__(self, device_id: str, device_type: str) -> None:
        super().__init__(
            f"injected device {device_id!r} (type={device_type!r}) "
            "snapshot differs from persisted state"
        )


class _DeviceExtraSubSnapshotsError(TickLoopAgentSnapshotDeviceMismatchError):
    """Resume-Diagnostik: persistierte Device-Sub-Snapshots ohne injizierten Match.

    Sortier-Verantwortung liegt in `__init__` (deterministische Ausgabe);
    Aufrufer uebergibt eine ungeordnete `set[str]` der Extra-Keys.
    """

    def __init__(self, extras: set[str]) -> None:
        super().__init__(
            f"persisted device sub-snapshots {sorted(extras)!r} have no "
            "matching injected device (injected subset is not a full restore)"
        )


class _GridModelDiffersError(TickLoopAgentSnapshotGridModelMismatchError):
    """Resume-Diagnostik: `grid_model.snapshot()` weicht ab."""

    def __init__(self) -> None:
        super().__init__("injected grid_model.snapshot() differs from persisted sub-snapshot")


class _LoadEventsOverlayDiffersError(TickLoopAgentSnapshotLoadOverlayMismatchError):
    """Resume-Diagnostik: `active_load_events` weichen vom persistierten Overlay ab."""

    def __init__(self) -> None:
        super().__init__("injected active_load_events differ from persisted GridModel overlay")


class _LoadProfilesOverlayDiffersError(TickLoopAgentSnapshotLoadOverlayMismatchError):
    """Resume-Diagnostik: `active_load_profiles` weichen ab."""

    def __init__(self) -> None:
        super().__init__("injected active_load_profiles differ from persisted GridModel overlay")


class _AgentUnregisteredClassError(TickLoopAgentInstanceSnapshotMismatchError):
    """Resume-Diagnostik: Agent-Klasse nicht in `_AGENT_TYPE_BY_CLASS_NAME`."""

    def __init__(self, agent_id: str, class_name: str) -> None:
        super().__init__(
            f"injected agent {agent_id!r} has unregistered class "
            f"{class_name!r} (not in _AGENT_TYPE_BY_CLASS_NAME)"
        )


class _AgentMissingSubSnapshotError(TickLoopAgentInstanceSnapshotMismatchError):
    """Resume-Diagnostik: injizierter Agent ohne passenden Sub-Snapshot-Slot."""

    def __init__(self, agent_id: str, agent_type: str, key: str) -> None:
        super().__init__(
            f"injected agent {agent_id!r} (type={agent_type!r}) "
            f"has no matching sub-snapshot key {key!r}"
        )


class _AgentSnapshotDiffersError(TickLoopAgentInstanceSnapshotMismatchError):
    """Resume-Diagnostik: `agent.snapshot()` weicht ab."""

    def __init__(self, agent_id: str, agent_type: str) -> None:
        super().__init__(
            f"injected agent {agent_id!r} (type={agent_type!r}) "
            "snapshot differs from persisted state"
        )


class _AgentExtraSubSnapshotsError(TickLoopAgentInstanceSnapshotMismatchError):
    """Resume-Diagnostik: persistierte Agent-Sub-Snapshots ohne injizierten Match.

    Sortier-Verantwortung liegt in `__init__` (deterministische Ausgabe);
    Aufrufer uebergibt eine ungeordnete `set[str]` der Extra-Keys.
    """

    def __init__(self, extras: set[str]) -> None:
        super().__init__(
            f"persisted agent sub-snapshots {sorted(extras)!r} have no "
            "matching injected agent (injected subset is not a full restore)"
        )


def _assert_device_resume_match(
    sub_snapshots: Mapping[str, object],
    devices: tuple[DeviceModel, ...],
) -> None:
    """Resume-Match-Check fuer injizierte Devices (ADR 0026 §2.6).

    Wenn der Snapshot `devices.<type>.<id>`-Sub-Snapshots enthaelt
    und `devices` injiziert ist, muessen IDs, Typen UND
    Device-Snapshot-States exakt passen — **bidirektional**:
    jedes injizierte Device hat einen persistierten Slot, und
    jeder persistierte Slot hat ein passendes injiziertes Device.
    Welle-4a-Review-Folge I-1 (2026-05-22): einseitige Pruefung
    haette beim Resume mit Subset der Devices stille
    Partial-Restores erlaubt.

    State-Vergleich via `canonical_json`-Bytes (Welle-4a-Review-
    Folge I-2): `dict(...) != dict(...)` deckt nur Top-Level ab;
    nested `tuple` vs. `list` (typisch nach Persistence-Roundtrip)
    waeren in der naiven Variante False-Positives. canonical_json
    normalisiert beide auf das gleiche JSON-Array-Layout.
    """
    if not devices:
        return
    device_keys = {key for key in sub_snapshots if key.startswith("devices.")}
    if not device_keys:
        return
    expected_keys: set[str] = set()
    for device in devices:
        device_type = _device_type_for(device)
        key = f"devices.{device_type}.{device.device_id}"
        expected_keys.add(key)
        if key not in sub_snapshots:
            raise _DeviceMissingSubSnapshotError(device.device_id, device_type, key)
        persisted = sub_snapshots[key]
        if not isinstance(persisted, Mapping):
            raise TickLoopAgentSnapshotWrongTypeError(
                f"sub_snapshots.{key}", "Mapping", type(persisted).__name__
            )
        live = device.snapshot()
        if canonical_json(dict(live)) != canonical_json(dict(persisted)):
            raise _DeviceSnapshotDiffersError(device.device_id, device_type)
    extras = device_keys - expected_keys
    if extras:
        raise _DeviceExtraSubSnapshotsError(extras)


def _assert_grid_model_resume_match(
    sub_snapshots: Mapping[str, object],
    grid_model: GridModelBilanz | None,
) -> None:
    """Resume-Match-Check fuer injiziertes GridModel (ADR 0026 §2.6).

    State-Vergleich via `canonical_json`-Bytes (Welle-4a-Review-
    Folge I-2): siehe `_assert_device_resume_match`-Docstring.
    """
    if grid_model is None:
        return
    persisted = sub_snapshots.get("grid_model")
    if persisted is None:
        return
    if not isinstance(persisted, Mapping):
        raise TickLoopAgentSnapshotWrongTypeError(
            "sub_snapshots.grid_model", "Mapping", type(persisted).__name__
        )
    live = grid_model.snapshot()
    if canonical_json(dict(live)) != canonical_json(dict(persisted)):
        raise _GridModelDiffersError


def _assert_load_overlay_resume_match(
    sub_snapshots: Mapping[str, object],
    active_load_events: tuple[LoadEvent, ...],
    active_load_profiles: tuple[LoadProfile, ...],
) -> None:
    """Resume-Match-Check fuer LoadOverlay-Tupel (ADR 0026 §2.6).

    Aktiv nur, wenn:
    - Sub-Snapshot enthaelt einen `grid_model`-Slot (Single Source
      of Truth fuer Overlay-State, ADR 0019 §6).
    - Nicht-leere LoadOverlay-Tupel injiziert (Overlay-only-
      Szenarien ohne GridModel bleiben gueltig).
    """
    if not active_load_events and not active_load_profiles:
        return
    grid_state = sub_snapshots.get("grid_model")
    if grid_state is None:
        return
    if not isinstance(grid_state, Mapping):
        # Match-Check fuer GridModel hat das schon abgefangen;
        # defensive guard hier nicht doppelt werfen.
        return
    persisted_events = grid_state.get("active_load_events")
    persisted_profiles = grid_state.get("active_load_profiles")
    if persisted_events is None and persisted_profiles is None:
        # Welle-5a-GridModel-Snapshot ohne Overlay-Persistenz —
        # akzeptieren, kein Match-Check moeglich (nur v2+ persistiert
        # Overlays, ADR 0020).
        return
    # Persistierte Werte sind List[dict] (canonical_json, ADR 0020 §2.6).
    # Welle-4a-Review-Folge I-2: Vergleich via `canonical_json`-Bytes,
    # damit `tuple` vs. `list` und Decimal-Tail-Nullen einheitlich
    # normalisiert werden (sonst False-Positives nach Persistence-
    # Roundtrip).
    live_events = [dict(_load_event_to_mapping(event)) for event in active_load_events]
    live_profiles = [dict(_load_profile_to_mapping(profile)) for profile in active_load_profiles]
    if persisted_events is not None and canonical_json(list(persisted_events)) != canonical_json(
        live_events
    ):
        raise _LoadEventsOverlayDiffersError
    if persisted_profiles is not None and canonical_json(
        list(persisted_profiles)
    ) != canonical_json(live_profiles):
        raise _LoadProfilesOverlayDiffersError


def _load_event_to_mapping(event: LoadEvent) -> Mapping[str, object]:
    """LoadEvent-zu-Mapping-Helper analog GridModelSnapshot
    (ADR 0020 §2.6 / `core/grid_model/snapshot.py`)."""
    return {
        "start_s": event.start_s,
        "duration_s": event.duration_s,
        "target_device_id": event.target_device_id,
        "power_kw": event.power_kw,
    }


def _load_profile_to_mapping(profile: LoadProfile) -> Mapping[str, object]:
    """LoadProfile-zu-Mapping-Helper analog GridModelSnapshot."""
    return {
        "target_device_id": profile.target_device_id,
        "tick_values": list(profile.tick_values),
        "tick_ms": profile.tick_ms,
    }


def _agent_type_for(agent: Agent) -> str | None:
    """Liefert das `agent_type`-Segment fuer die
    `agents.<agent_type>.<agent_id>`-Sub-Snapshot-Key-Konstruktion
    (M3 Welle 4b, ADR 0027 §2.4).

    Liefert `None`, wenn der Agent-Klassen-Name in
    `_AGENT_TYPE_BY_CLASS_NAME` nicht registriert ist — Aufrufer
    entscheidet, ob er das als Skip (Forward-Compat) oder Error
    behandelt.
    """
    return _AGENT_TYPE_BY_CLASS_NAME.get(type(agent).__name__)


def _assert_agent_instance_resume_match(
    sub_snapshots: Mapping[str, object],
    agents: tuple[Agent, ...],
) -> None:
    """Bidirektionaler Resume-Match-Check fuer Agent-Instanz-
    Sub-Snapshots (M3 Welle 4b, ADR 0027 §2.4).

    Analog `_assert_device_resume_match` (Welle-4a-Review-Folge
    `38272f6`): jeder injizierte Agent muss einen `agents.<type>
    .<id>`-Slot haben, jeder Slot muss einen injizierten Agent
    haben. Snapshot-State-Vergleich via `canonical_json`-Bytes
    (kein False-Positive nach tuple/list-Roundtrip).

    Wenn `agents=()` ist (Welle-6a/Welle-4a-Pfad ohne Agents),
    wird der Check uebersprungen — gleiches Pattern wie
    `_assert_device_resume_match`.
    """
    if not agents:
        return
    agent_keys = {key for key in sub_snapshots if key.startswith("agents.")}
    if not agent_keys:
        return
    expected_keys: set[str] = set()
    for agent in agents:
        agent_type = _agent_type_for(agent)
        if agent_type is None:
            raise _AgentUnregisteredClassError(agent.agent_id, type(agent).__name__)
        key = f"agents.{agent_type}.{agent.agent_id}"
        expected_keys.add(key)
        if key not in sub_snapshots:
            raise _AgentMissingSubSnapshotError(agent.agent_id, agent_type, key)
        persisted = sub_snapshots[key]
        if not isinstance(persisted, Mapping):
            raise TickLoopAgentSnapshotWrongTypeError(
                f"sub_snapshots.{key}", "Mapping", type(persisted).__name__
            )
        live = agent.snapshot()
        if canonical_json(dict(live)) != canonical_json(dict(persisted)):
            raise _AgentSnapshotDiffersError(agent.agent_id, agent_type)
    extras = agent_keys - expected_keys
    if extras:
        raise _AgentExtraSubSnapshotsError(extras)
