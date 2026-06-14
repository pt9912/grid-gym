"""`WindTurbineDevice` — DeviceModel (M8 Welle 2c, `GG-DEV-017`, ADR 0057).

Command-loser Erneuerbaren-Generator nach dem PV-Muster ([`ADR 0016`]),
mit **stochastischem** Windgeschwindigkeits-Eingang (seeded `RandomPort`,
ADR 0057 §2.4) und **kubischer** Leistungskennlinie (§2.5).

Wind ist das erste Geraet, das den `RandomPort` tatsaechlich konsumiert:
pro Tick eine `next_float()`-Ziehung. `apply_command` ist ein No-Op
(`IGNORED`) — keine Steuerbefehle, kein Alarm, kein Fault.

Tick-Mechanik (Decimal-Localcontext `prec=28`, `ROUND_HALF_EVEN`):

1. `wind_speed_ms = min + next_float() * (max - min)`.
2. `power_kw = curve(wind_speed_ms)` (§2.5; `0` unter cut-in/ueber
   cut-out, kubisch zwischen cut-in und rated, flach bei rated).
3. `generated_kwh += power_kw * (tick_ms / 3_600_000)`.

Sign-Konvention (ADR 0057 §2.2): `power_kw >= 0` (Einspeisung).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.wind_turbine.config import (
    CONFIG_FIELD_NAMES,
    WindTurbineConfig,
)
from grid_gym.hexagon.core.devices.wind_turbine.snapshot import (
    SNAPSHOT_VERSION,
    WindTurbineSnapshot,
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
_WIND_TURBINE_SOURCE = "wind_turbine"
_SUBSYSTEM = "wind_turbine"
_WIND_TURBINE_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-Pattern)."""

_PARAM_KEYS = CONFIG_FIELD_NAMES


@contextmanager
def _wind_turbine_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (ADR 0057 §2.4): pinnt `prec=28`
    und `rounding=ROUND_HALF_EVEN` fuer die Tick-Berechnung."""
    with localcontext() as ctx:
        ctx.prec = _WIND_TURBINE_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class WindTurbineDevice:
    """`DeviceModel`-Implementation fuer die Windkraftanlage."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: WindTurbineConfig | None = None
        self._current_power_kw: Decimal = _ZERO
        self._current_wind_speed_ms: Decimal = _ZERO
        self._generated_kwh: Decimal = _ZERO
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._run_id: str = _RUN_ID_UNSET
        self._sequence: int = 0

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot` (ADR 0007 §5 +
        ADR 0013 §2.6). **Anders als die uebrigen Geraete konsumiert Wind
        `_random` tatsaechlich** — nach `from_snapshot` MUSS dieser Hook
        vor dem ersten `tick` laufen, sonst wirft der Tick fail-loud.
        Voller stand-kontinuierlicher Resume stochastischer Geraete ist
        ein Folge-Slice (ADR 0057 §2.6/§6); Welle 2c deckt nur den
        Fresh-Start-Pfad ab."""
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
        self._current_power_kw = _ZERO
        self._current_wind_speed_ms = _ZERO
        self._generated_kwh = _ZERO

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        _ = command  # Wind nimmt keine Steuerbefehle (ADR 0057 §2.1).
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("tick")
        if self._random is None:
            # Resume-Vertrag (ADR 0057 §2.6): nach `from_snapshot` muss
            # `attach_random` vor dem ersten Tick laufen (sonst kein
            # RandomPort fuer die stochastische Wind-Ziehung).
            raise DeviceNotInitializedError("tick")
        with _wind_turbine_decimal_context():
            return self._tick_in_context(context, self._random)

    def _tick_in_context(self, context: DeviceTickContext, random: RandomPort) -> DeviceTickOutcome:
        config = cast(WindTurbineConfig, self._config)
        wind_speed = self._draw_wind_speed(random, config)
        power = self._power_from_curve(wind_speed, config)
        dt_hours = Decimal(context.tick_ms) / _MS_PER_HOUR
        self._generated_kwh += power * dt_hours
        self._current_wind_speed_ms = wind_speed
        self._current_power_kw = power
        telemetry = self._emit_telemetry(context, power, wind_speed)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    @staticmethod
    def _draw_wind_speed(random: RandomPort, config: WindTurbineConfig) -> Decimal:
        """ADR 0057 §2.4: uniforme Ziehung in `[min, max)` ueber EINE
        `next_float()`-Ziehung. Bei `min == max` konstant `min` (die
        Ziehung erfolgt trotzdem, Stream bleibt sequenz-konsistent)."""
        span = config.max_wind_speed_ms - config.min_wind_speed_ms
        return config.min_wind_speed_ms + random.next_float() * span

    @staticmethod
    def _power_from_curve(wind_speed: Decimal, config: WindTurbineConfig) -> Decimal:
        """Kubische Leistungskennlinie (ADR 0057 §2.5)."""
        if wind_speed < config.cut_in_speed_ms or wind_speed >= config.cut_out_speed_ms:
            return _ZERO
        if wind_speed >= config.rated_speed_ms:
            return config.rated_power_kw
        cut_in = config.cut_in_speed_ms
        rated = config.rated_speed_ms
        numerator = wind_speed * wind_speed * wind_speed - cut_in * cut_in * cut_in
        denominator = rated * rated * rated - cut_in * cut_in * cut_in
        return config.rated_power_kw * numerator / denominator

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    def snapshot(self) -> Mapping[str, object]:
        if self._config is None or self._scenario_device is None:
            return {"version": SNAPSHOT_VERSION}
        snap = WindTurbineSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            current_power_kw=self._current_power_kw,
            current_wind_speed_ms=self._current_wind_speed_ms,
            generated_kwh=self._generated_kwh,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        snap = WindTurbineSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="wind_turbine",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._current_power_kw = snap.current_power_kw
        device._current_wind_speed_ms = snap.current_wind_speed_ms
        device._generated_kwh = snap.generated_kwh
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WindTurbineDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._current_power_kw == other._current_power_kw
            and self._current_wind_speed_ms == other._current_wind_speed_ms
            and self._generated_kwh == other._generated_kwh
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
                self._current_wind_speed_ms,
                self._generated_kwh,
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
        power: Decimal,
        wind_speed: Decimal,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id

        # Drei Tupel; alphabetisch sortiert nach Metrikname (ADR 0057 §2.6).
        emissions = (
            ("generated_kwh", self._generated_kwh, "kWh"),
            ("power_kw", power, "kW"),
            ("wind_speed_ms", wind_speed, "m/s"),
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
                    value=value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN),
                    unit=unit,
                    quality=Quality.VALID,
                    source=_WIND_TURBINE_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> WindTurbineConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `WindTurbineConfig`
    (ADR 0057 §2.3). Erwartet alle Pflicht-Felder als `Decimal`."""
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return WindTurbineConfig(**fields)


def _config_to_params(config: WindTurbineConfig) -> Mapping[str, Decimal]:
    return {key: getattr(config, key) for key in _PARAM_KEYS}
