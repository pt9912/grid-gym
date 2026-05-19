"""`GridConnectionDevice` — DeviceModel-Implementation
(M2 Welle 4a, `GG-DEV-012`).

Welle-4a-Minimum (ADR 0017 §2.5): idealer Anschlusspunkt ohne
Wirkungsgrad / Ramp-Limit / Hard-Clamp. Validierung laeuft am
`apply_command`-Eingang (Import-/Export-Caps).

Tick-Mechanik (ADR 0017 §2.5):

1. `new_power_kw = self._pending_power_kw` (kein Ramp).
2. Energie-Akkumulation:
   `delta_kwh = abs(new_power_kw) * (tick_ms / 3600_000)`.
   - `new_power_kw > 0` → `import_kwh += delta_kwh`.
   - `new_power_kw < 0` → `export_kwh += delta_kwh`.
3. Telemetrie-Emission: 3 `TelemetryPoint`s (sortiert nach
   Metrikname: `export_kwh`, `import_kwh`, `power_kw`).

Sign-Konvention (ADR 0017 §2.2): Bezug = lokales System;
`> 0` = Import (Energie ins lokale System), `< 0` = Export
(Energie ins Netz), `== 0` = Balanced.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.grid_connection.commands import (
    GridConnectionAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.grid_connection.config import (
    GridConnectionConfig,
)
from grid_gym.hexagon.core.devices.grid_connection.snapshot import (
    CONFIG_FIELD_NAMES,
    SNAPSHOT_VERSION,
    GridConnectionSnapshot,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
    MissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_QUANTUM = Decimal("0.000001")
_MS_PER_HOUR = Decimal(3_600_000)
_GRID_CONNECTION_SOURCE = "grid_connection"
_SUBSYSTEM = "grid_connection"
_GRID_CONNECTION_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-
Pattern). Welle 6 TickLoop ruft `set_run_id` vor dem ersten Tick."""

# Welle-4a-Review L-3: Single-Source-of-Truth ueber `snapshot.py`.
_PARAM_KEYS = CONFIG_FIELD_NAMES


@contextmanager
def _grid_connection_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (Welle-2-Review-M-2-Spiegel).

    Hier mit sichtbarem Effekt (ADR 0017 §2.5 Forward-Looking-
    Defense): die Tick-Mechanik rechnet
    `delta_kwh = abs(power_kw) * (tick_ms / 3_600_000)` — eine echte
    Decimal-Multiplikation, im Gegensatz zum trivialen
    PV/Load-Tick.
    """
    with localcontext() as ctx:
        ctx.prec = _GRID_CONNECTION_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class GridConnectionDevice:
    """`DeviceModel`-Implementation fuer den Netzanschlusspunkt."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: GridConnectionConfig | None = None
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._import_kwh: Decimal = _ZERO
        self._export_kwh: Decimal = _ZERO
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[GridConnectionAlarm] = []
        self._run_id: str = _RUN_ID_UNSET
        self._sequence: int = 0

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[GridConnectionAlarm, ...]:
        """Unveraenderliches Snapshot-Tupel; siehe `drain_alarms()`
        fuer destruktiven Read (ADR 0014 §2.5-Spiegel)."""
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[GridConnectionAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot`
        (Welle-3-Review M-6-Pattern). Welle 4a GridConnection
        konsumiert `_random` nicht; M3 (Fault-Injection
        Spannungs-/Frequenz-Drops, `GG-FAULT-005`/`007`) wird
        es verbrauchen."""
        self._random = random

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        if self._scenario_device is not None:
            raise DeviceAlreadyInitializedError
        config = _config_from_params(scenario_device.params)
        self._scenario_device = scenario_device
        self._random = random
        self._config = config
        # ADR 0017 §2.6: Default-Output ist `0` (Balanced),
        # **nicht** rated_power_kw — Anschlusspunkt soll nicht
        # spontan importieren / exportieren.
        self._current_power_kw = _ZERO
        self._pending_power_kw = _ZERO
        self._import_kwh = _ZERO
        self._export_kwh = _ZERO

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        outcome = validate_set_power_command(
            config=self._config,
            command=command,
            device_id=self._scenario_device.id,
        )
        if outcome.pending_power_kw is not None:
            self._pending_power_kw = outcome.pending_power_kw
        if outcome.alarm is not None:
            self._alarms.append(outcome.alarm)
        return outcome.result

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("tick")
        with _grid_connection_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        # Welle-4a-Minimum (ADR 0017 §2.5): kein Ramp.
        new_power_kw = self._pending_power_kw
        self._current_power_kw = new_power_kw

        # Energie-Akkumulation: delta_kwh = |power_kw| * (tick_ms / 3_600_000).
        # tick_ms wird zu Decimal gehoben, damit der Local-Context greift
        # und das Ergebnis byte-stabil bleibt.
        delta_kwh = abs(new_power_kw) * Decimal(context.tick_ms) / _MS_PER_HOUR
        if new_power_kw > _ZERO:
            self._import_kwh += delta_kwh
        elif new_power_kw < _ZERO:
            self._export_kwh += delta_kwh

        telemetry = self._emit_telemetry(context, new_power_kw)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    def snapshot(self) -> Mapping[str, object]:
        if self._config is None or self._scenario_device is None:
            return {"version": SNAPSHOT_VERSION}
        snap = GridConnectionSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
            import_kwh=self._import_kwh,
            export_kwh=self._export_kwh,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # ADR 0014 §2.2-Schaerfung / ADR 0017 §2.3: self-sufficient.
        snap = GridConnectionSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="grid_connection",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._import_kwh = snap.import_kwh
        device._export_kwh = snap.export_kwh
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GridConnectionDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
            and self._import_kwh == other._import_kwh
            and self._export_kwh == other._export_kwh
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._current_power_kw,
                self._pending_power_kw,
                self._import_kwh,
                self._export_kwh,
                self._device_id_or_none(),
                self._run_id,
                self._sequence,
            )
        )

    def _device_id_or_none(self) -> str | None:
        return None if self._scenario_device is None else self._scenario_device.id

    def _emit_telemetry(
        self,
        context: DeviceTickContext,
        new_power_kw: Decimal,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id
        export_kwh = self._export_kwh.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        import_kwh = self._import_kwh.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        power_kw = new_power_kw.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

        # Drei Tupel; alphabetisch sortiert nach Metrikname (ADR 0017 §2.5).
        emissions = (
            ("export_kwh", export_kwh, "kWh"),
            ("import_kwh", import_kwh, "kWh"),
            ("power_kw", power_kw, "kW"),
        )
        points = []
        for metric, value, unit in emissions:
            self._sequence += 1
            points.append(
                TelemetryPoint(
                    run_id=self._run_id,
                    tick=context.tick,
                    simulation_time=context.simulation_time,
                    device_id=device_id,
                    metric=metric,
                    value=value,
                    unit=unit,
                    quality=Quality.VALID,
                    source=_GRID_CONNECTION_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> GridConnectionConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `GridConnectionConfig`.

    Erwartet alle Pflicht-Felder als `Decimal`. YAML-Adapter-Schicht
    ist fuer die Decimal-Konversion verantwortlich; hier wird
    strukturell geprueft.
    """
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return GridConnectionConfig(**fields)


def _config_to_params(config: GridConnectionConfig) -> Mapping[str, Decimal]:
    return {key: getattr(config, key) for key in _PARAM_KEYS}
