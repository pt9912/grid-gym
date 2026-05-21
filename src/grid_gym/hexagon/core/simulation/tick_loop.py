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

from grid_gym.hexagon.core.agents import Agent, AgentMessageBus
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
    TickLoopInvalidTickMsError,
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
    TickLoopUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelBilanz
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
        # M3-Welle-3 (ADR 0023 §2.5): optionaler AgentMessageBus +
        # Welle-3-leerer Agent-Registry-Tuple. `None`-Default
        # skippt den Hook in `tick()` (Schritt D2). Welle-3-Stand:
        # `_agents` ist fest `()` — Welle 4 entscheidet, ob die
        # Registry via Konstruktor-Kwarg oder Scenario-Loader-
        # Builder gefuellt wird. Tests duerfen `_agents` direkt
        # mutieren, um den Hook zu exerzieren.
        self._agent_bus: AgentMessageBus | None = agent_bus
        self._agents: tuple[Agent, ...] = ()
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

    def _attach_devices(self) -> None:
        """Reicht `run_id` an alle Devices durch (Welle-3-Review-M-4-
        Vertrag). `attach_random` und `attach_sources` (SmartMeter)
        bleiben Welle-6b-Scenario-Loader-Verantwortung — die brauchen
        Quell-Referenzen, die hier nicht verfuegbar sind."""
        for device in self._devices:
            device.set_run_id(self._run_id)

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
            # sauber; Welle-3-Stand: `self._agents` ist `()`. Welle 4
            # entscheidet, wo emittierte Commands gepuffert/angewandt
            # werden (Pending-Buffer im TickLoop vs. direkter Pfad in
            # der naechsten Device-Iteration). Welle-3-Foundation
            # verdrahtet die Anwendung nicht — Return Value wird
            # bewusst verworfen (Welle-4-TODO).
            if self._agent_bus is not None:
                for agent in self._agents:
                    agent.tick(context, self._agent_bus)
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
    ) -> TickLoop:
        """Stellt einen `TickLoop` aus einem Snapshot wieder her.

        Aufrufer injiziert `clock` und `random` als bereits restored
        Instanzen (z. B. via `MersenneTwisterRandomPort.from_snapshot`
        und einer Clock, die per `advance` auf
        `state['simulation_time']` gebracht wurde).

        Konsistenz-Pruefungen:
        - `clock.now() == state['simulation_time']` →
          `TickLoopSnapshotClockMismatchError`.
        - `random.snapshot_as_mapping() == state['sub_snapshots']
          ['random_root']` → `TickLoopSnapshotRandomMismatchError`.

        Der `Scheduler` wird intern aus
        `state['sub_snapshots']['scheduler']` rekonstruiert.

        Bewusste Asymmetrie zwischen `clock`/`random` (extern
        injiziert) und `scheduler` (intern rekonstruiert):
        `clock` und `random` sind **Peer-Ports** mit eigenem
        Persistenz-Pfad — `MersenneTwisterRandomPort` haelt seinen
        State auch in Disk-canonical-Bytes, `ClockPort` ist je nach
        Implementation auf wallclock-/setup-spezifische Restore-
        Schritte angewiesen. Der `Scheduler` dagegen ist
        **Sub-Subsystem** des TickLoops: sein Snapshot lebt
        strukturell in `state['sub_snapshots']['scheduler']` und
        hat ausser dem TickLoop keinen externen Persistenz-Konsumenten.
        Composition-intern erspart das Aufrufern einen redundanten
        Resume-Schritt.
        """
        parsed = _validate_tick_loop_snapshot(state)
        if parsed.version != _SNAPSHOT_VERSION:
            raise TickLoopSnapshotVersionError(_SNAPSHOT_VERSION, parsed.version)
        if clock.now() != parsed.simulation_time:
            raise TickLoopSnapshotClockMismatchError(parsed.simulation_time, clock.now())
        if random.snapshot_as_mapping() != parsed.random_root:
            raise TickLoopSnapshotRandomMismatchError
        scheduler = Scheduler.from_snapshot(parsed.scheduler)
        loop = cls(
            run_id=parsed.run_id,
            tick_ms=parsed.tick_ms,
            clock=clock,
            random=random,
            scheduler=scheduler,
        )
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
