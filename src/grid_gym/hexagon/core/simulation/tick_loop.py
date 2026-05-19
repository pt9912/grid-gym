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

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.errors import (
    TickLoopInvalidTickMsError,
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelBilanz
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.random import RandomPort

_SNAPSHOT_VERSION: Final[int] = 2
"""Schema-Version des TickLoop-Snapshots. Welle-6a-Bump 1->2 ueber
ADR 0015. Erhoehung -> Folge-ADR."""

_ZERO = Decimal(0)

_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"version", "run_id", "simulation_time", "tick_count", "tick_ms", "sub_snapshots"}
)

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

    def tick(self) -> TickResult:
        """Schiebt die Simulationszeit um `tick_ms` vor, ruft fuer
        jedes registrierte Device `device.tick(context)`, aggregiert
        die `power_kw`-Telemetrie nach `TelemetryPoint.source` und
        ruft `grid_model.update(...)` mit Sign-Konvention aus
        ADR 0019 §2.2.

        - **Device-Iteration** in Konstruktor-Reihenfolge
          (`ScenarioDevice`-Definitionsreihenfolge wird in Welle 6b
          ueber den Scenario-Loader gehalten).
        - `TickResult.emitted_telemetry` ist die Konkatenation aller
          `device.tick().telemetry`-Tupel in Device-Reihenfolge.
        - **grid_model-Aufruf** geschieht nach allen Device-Ticks
          mit aggregierten Power-Werten; ist nur aktiv, wenn ein
          `grid_model`-Parameter ueber den Konstruktor injiziert
          wurde.
        - Welle-4-Scope (`GG-SIM-001`): ohne Devices/grid_model
          bleibt das Verhalten identisch zur M1-Welle-4-Spine
          (nur Scheduler-Event-Pop).
        """
        self._clock.advance(self._tick_ms)
        now = self._clock.now()
        popped = tuple(self._scheduler.pop_due(now))

        # Welle 6a: Device-Iteration + Bilanz-Aggregation.
        context = DeviceTickContext(
            tick=self._tick_count,
            simulation_time=now,
            tick_ms=self._tick_ms,
        )
        emitted: list[TelemetryPoint] = []
        bucket_sums: dict[str, Decimal] = {
            "generation": _ZERO,
            "load": _ZERO,
            "storage": _ZERO,
            "grid_connection": _ZERO,
        }
        for device in self._devices:
            outcome = device.tick(context)
            for point in outcome.telemetry:
                emitted.append(point)
                if point.metric != _POWER_KW_METRIC:
                    continue
                bucket = _BILANZ_SOURCE_BUCKETS.get(point.source)
                if bucket is None:
                    continue
                bucket_sums[bucket] += point.value

        if self._grid_model is not None:
            self._grid_model.update(
                generation_kw=bucket_sums["generation"],
                load_kw=bucket_sums["load"],
                storage_kw=bucket_sums["storage"],
                grid_connection_kw=bucket_sums["grid_connection"],
            )

        result = TickResult(
            tick=self._tick_count,
            simulation_time=now,
            popped_events=popped,
            emitted_telemetry=tuple(emitted),
        )
        self._tick_count += 1
        return result

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
            key = f"devices.{device_type}.{device.device_id}"
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
    `device_type`-Protocol-Erweiterung erzwingen."""
    class_name = type(device).__name__
    if class_name not in _DEVICE_TYPE_BY_CLASS_NAME:
        raise TickLoopSnapshotWrongTypeError(
            f"device({class_name})",
            f"registered DeviceModel class (one of {sorted(_DEVICE_TYPE_BY_CLASS_NAME)})",
            class_name,
        )
    return _DEVICE_TYPE_BY_CLASS_NAME[class_name]
