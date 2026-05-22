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

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Final

from grid_gym.hexagon.core.agents import Agent, AgentMessageBus, _RandomAttachableAgent
from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.errors import (
    AgentDuplicateIdError,
    AgentInvalidCommandTargetError,
    TickLoopAgentInstanceSnapshotMismatchError,
    TickLoopAgentSnapshotDeviceMismatchError,
    TickLoopAgentSnapshotGridModelMismatchError,
    TickLoopAgentSnapshotInvalidCommandResultError,
    TickLoopAgentSnapshotLoadOverlayMismatchError,
    TickLoopAgentSnapshotMissingKeysError,
    TickLoopAgentSnapshotWrongTypeError,
    TickLoopInvalidTickMsError,
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
    TickLoopUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelBilanz
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.fault import FaultPort
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
        # Registry-Fail-Fast).
        seen_agent_ids: set[str] = set()
        for agent in agents:
            if agent.agent_id in seen_agent_ids:
                raise AgentDuplicateIdError(agent.agent_id)
            seen_agent_ids.add(agent.agent_id)
        if agents and agent_bus is None:
            agent_bus = AgentMessageBus()
        self._agent_bus: AgentMessageBus | None = agent_bus
        self._agents: tuple[Agent, ...] = agents
        # M3-Welle-3-Review-Folge-2 F-1 + M3-Welle-4a F-1 produktiv:
        # `_pending_agent_commands` ist der Buffer, den Schritt D2
        # (Agent-Tick) fuellt und Schritt A0a (Pre-Tick-Drain) in
        # der naechsten Tick auf die Target-Devices anwendet.
        # Welle-4a (ADR 0026 §2.6) persistiert den Buffer als
        # `pending_agent_commands`-Sub-Snapshot, damit Snapshots
        # zwischen Agent-Tick und Folgetick keine Commands
        # verlieren.
        self._pending_agent_commands: list[Command] = []
        # Welle-6a-Review M-3: Counter fuer unbekannte source-Tags
        # (Welle-7+/M3-Forward-Compat-Defense gegen Silent-Skip).
        self._unknown_source_count: int = 0
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

    def _attach_devices(self) -> None:
        """Reicht `run_id` an alle Devices durch (Welle-3-Review-M-4-
        Vertrag). `attach_random` und `attach_sources` (SmartMeter)
        bleiben Welle-6b-Scenario-Loader-Verantwortung — die brauchen
        Quell-Referenzen, die hier nicht verfuegbar sind."""
        for device in self._devices:
            device.set_run_id(self._run_id)

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
    def unknown_source_count(self) -> int:
        """Welle-6a-Review M-3: kumulative Anzahl von TelemetryPoints
        mit `power_kw`-Metric und unbekanntem `source`-Tag (nicht in
        `_BILANZ_SOURCE_BUCKETS`). Forward-Looking-Defense fuer
        Welle-7+/M3-Geraete-Drift (z. B. `WindDevice` mit
        `source='wind'`)."""
        return self._unknown_source_count

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

    def tick(self) -> TickResult:  # noqa: PLR0915 — Welle-4a-tick() integriert A0v/A0a-Drain, Vor-Tick-Block, Device-Iteration in zwei Phasen, GridConnection-Auto-Close, Bilanz-Aggregation (ADR 0026 §2.1).
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

        self._clock.advance(self._tick_ms)
        now = self._clock.now()
        popped = tuple(self._scheduler.pop_due(now))

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
            # Schritt A0a (M3-Welle-4a, ADR 0026 §2.1) — Apply der
            # in A0v validierten Pending-Agent-Commands. Laeuft
            # VOR Schritt A (LoadEvent/Profile-Overlay), damit
            # Agent-Commands der vorigen Ticks im aktuellen Tick
            # in den Device-Command-Pfad eingespeist werden
            # (GG-AGENT-008 Commit-Reihenfolge-Invariante).
            #
            # Agent-Commands auf GridConnection-IDs zaehlen als
            # manueller Auto-Close-Override (ergaenzen
            # `manual_override_grid_ids`); LoadEvent/Profile-Overlay
            # in Schritt A laeuft danach und gewinnt auf
            # LoadDevices (Baseline-Praezedenz aus Welle-6b).
            for command in commands_to_apply:
                target = self._device_by_id[command.target_device_id]
                target.apply_command(command)
                if (
                    isinstance(target, GridConnectionDevice)
                    and target.device_id not in manual_override_grid_ids
                ):
                    manual_override_grid_ids.append(target.device_id)
            # Buffer erst nach erfolgreichem Apply-Durchlauf
            # leeren — bei `apply_command(...)`-Exception bleibt
            # er ungeleert (ADR 0026 §2.1 Exception-Pfade).
            self._pending_agent_commands.clear()
            # Schritt A — Vor-Tick-Block (ADR 0021 §2.5).
            # Welle-6b-Review H-3: Event-Window-Check nutzt die
            # Tick-Start-Zeit (`now - tick_ms`), nicht die Tick-End-
            # Zeit `now`. Damit deckt die halbgeoffene Pruefung
            # `event.start_s <= now_s < event_end_s` korrekt das
            # erste Tick-Intervall `[0, tick_ms)` ab — sonst
            # wuerde ein Event mit `duration_s == tick_ms/1000`
            # bereits im ersten Tick als abgelaufen behandelt.
            tick_start_ms = now - self._tick_ms
            self._consume_load_inputs_into(
                tick_start_ms=tick_start_ms,
                now_ms=now,
                manual_override_grid_ids=manual_override_grid_ids,
            )
            # Schritt A2 — Fault-Injection (M3-Welle-1, ADR 0022 §2.4).
            # Hook laeuft nach LoadEvent-/Profile-Overlay und vor
            # der ersten Device-Iteration, damit Faults in derselben
            # Tick wirksam werden (Order-Pflicht aus ADR 0022 §2.4).
            # `None`-Default skippt sauber; produktiver Adapter
            # kommt mit Welle 2.
            if self._fault_port is not None:
                self._fault_port.apply_active_faults(self._devices, context)
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
            # Architektur §6 Schritt 7: Agents laufen NACH der
            # Geraete-Iteration und VOR `grid_model.update(...)`.
            # Sie sehen den fertigen Welt-Zustand (alle Devices haben
            # getickt, alle Telemetry ist emittiert) und produzieren
            # Commands fuer die naechste Tick. `None`-Default skippt
            # sauber; Welle-3-Stand: `self._agents` ist `()`.
            #
            # **Welle-3-Review-Folge-2 F-1 (2026-05-21)**: emittierte
            # Commands landen im `_pending_agent_commands`-Buffer
            # (nicht verworfen). Welle 4 verdrahtet den Drain-Pfad
            # (Scheduler-Push, `apply_command`-direct-Apply o. ae.) —
            # Welle-3-Foundation persistiert nur die Commands, fuehrt
            # sie aber NICHT aus. Konsistent mit GG-AGENT-008-Vertrag
            # (Commit-Reihenfolge eines Ticks bleibt unveraendert).
            if self._agent_bus is not None:
                for agent in self._agents:
                    self._pending_agent_commands.extend(agent.tick(context, self._agent_bus))
            # Schritt E — Bilanz-Aggregation.
            if self._grid_model is not None:
                self._grid_model.update(
                    generation_kw=bucket_sums["generation"],
                    load_kw=bucket_sums["load"],
                    storage_kw=bucket_sums["storage"],
                    grid_connection_kw=bucket_sums["grid_connection"],
                )
        self._unknown_source_count += unknown_count

        result = TickResult(
            tick=self._tick_count,
            simulation_time=now,
            popped_events=popped,
            emitted_telemetry=tuple(emitted),
        )
        self._tick_count += 1
        return result

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
        )
        # `_pending_agent_commands` muss nach Konstruktor-Init
        # gefuellt werden — der Konstruktor initialisiert es leer.
        loop._pending_agent_commands.extend(pending_commands)
        loop._tick_count = parsed.tick_count
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


def _restore_pending_command_entry(raw: object, index: int) -> Command:  # noqa: C901, PLR0915 — pro-Feld-typed-Errors fuer 7 Pflichtfelder rechtfertigen einen langen Body (ADR 0026 §2.6).
    """Pro-Eintrag-Restore mit typed-Errors fuer Format-Verstoesse."""
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
    command_id = raw["command_id"]
    if not isinstance(command_id, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].command_id",
            "str",
            type(command_id).__name__,
        )
    simulation_time = raw["simulation_time"]
    if isinstance(simulation_time, bool) or not isinstance(simulation_time, int):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].simulation_time",
            "int",
            type(simulation_time).__name__,
        )
    target_device_id = raw["target_device_id"]
    if not isinstance(target_device_id, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].target_device_id",
            "str",
            type(target_device_id).__name__,
        )
    type_value = raw["type"]
    if not isinstance(type_value, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].type",
            "str",
            type(type_value).__name__,
        )
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].payload",
            "Mapping",
            type(payload).__name__,
        )
    validation_status = raw["validation_status"]
    if not isinstance(validation_status, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].validation_status",
            "str",
            type(validation_status).__name__,
        )
    result_raw = raw["result"]
    if not isinstance(result_raw, str):
        raise TickLoopAgentSnapshotWrongTypeError(
            f"pending_agent_commands.commands[{index}].result",
            "str",
            type(result_raw).__name__,
        )
    try:
        result = CommandResult[result_raw]
    except KeyError as exc:
        raise TickLoopAgentSnapshotInvalidCommandResultError(index, result_raw) from exc
    return Command(
        command_id=command_id,
        simulation_time=simulation_time,
        target_device_id=target_device_id,
        type=type_value,
        payload=dict(payload),
        validation_status=validation_status,
        result=result,
    )


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
            raise TickLoopAgentSnapshotDeviceMismatchError(  # noqa: TRY003 — ADR 0026 §2.6 verlangt detail-rich Resume-Match-Diagnostik
                f"injected device {device.device_id!r} (type={device_type!r}) "
                f"has no matching sub-snapshot key {key!r}"
            )
        persisted = sub_snapshots[key]
        if not isinstance(persisted, Mapping):
            raise TickLoopAgentSnapshotWrongTypeError(
                f"sub_snapshots.{key}", "Mapping", type(persisted).__name__
            )
        live = device.snapshot()
        if canonical_json(dict(live)) != canonical_json(dict(persisted)):
            raise TickLoopAgentSnapshotDeviceMismatchError(  # noqa: TRY003
                f"injected device {device.device_id!r} (type={device_type!r}) "
                f"snapshot differs from persisted state"
            )
    extras = device_keys - expected_keys
    if extras:
        raise TickLoopAgentSnapshotDeviceMismatchError(  # noqa: TRY003
            f"persisted device sub-snapshots {sorted(extras)!r} have no "
            "matching injected device (injected subset is not a full restore)"
        )


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
        raise TickLoopAgentSnapshotGridModelMismatchError(  # noqa: TRY003
            "injected grid_model.snapshot() differs from persisted sub-snapshot"
        )


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
        raise TickLoopAgentSnapshotLoadOverlayMismatchError(  # noqa: TRY003
            "injected active_load_events differ from persisted GridModel overlay"
        )
    if persisted_profiles is not None and canonical_json(
        list(persisted_profiles)
    ) != canonical_json(live_profiles):
        raise TickLoopAgentSnapshotLoadOverlayMismatchError(  # noqa: TRY003
            "injected active_load_profiles differ from persisted GridModel overlay"
        )


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
            raise TickLoopAgentInstanceSnapshotMismatchError(  # noqa: TRY003
                f"injected agent {agent.agent_id!r} has unregistered class "
                f"{type(agent).__name__!r} (not in _AGENT_TYPE_BY_CLASS_NAME)"
            )
        key = f"agents.{agent_type}.{agent.agent_id}"
        expected_keys.add(key)
        if key not in sub_snapshots:
            raise TickLoopAgentInstanceSnapshotMismatchError(  # noqa: TRY003
                f"injected agent {agent.agent_id!r} (type={agent_type!r}) "
                f"has no matching sub-snapshot key {key!r}"
            )
        persisted = sub_snapshots[key]
        if not isinstance(persisted, Mapping):
            raise TickLoopAgentSnapshotWrongTypeError(
                f"sub_snapshots.{key}", "Mapping", type(persisted).__name__
            )
        live = agent.snapshot()
        if canonical_json(dict(live)) != canonical_json(dict(persisted)):
            raise TickLoopAgentInstanceSnapshotMismatchError(  # noqa: TRY003
                f"injected agent {agent.agent_id!r} (type={agent_type!r}) "
                f"snapshot differs from persisted state"
            )
    extras = agent_keys - expected_keys
    if extras:
        raise TickLoopAgentInstanceSnapshotMismatchError(  # noqa: TRY003
            f"persisted agent sub-snapshots {sorted(extras)!r} have no "
            "matching injected agent (injected subset is not a full restore)"
        )
