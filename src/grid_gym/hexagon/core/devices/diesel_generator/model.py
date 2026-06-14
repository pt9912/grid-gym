"""`DieselGeneratorDevice` — DeviceModel + FaultInjectableDevice
(M8 Welle 2d, `GG-DEV-018`, ADR 0058).

Dispatchbarer Generator mit endlicher Ressource nach dem Battery-Muster
([`ADR 0014`]): Kraftstoff-Vorrat (l), Verbrauch (l/kWh), Ramp-Limit,
Anfahr-/Abstell-Hysterese (running-Zustandsmaschine) und
`genset_fault`-Schutz.

Tick-Mechanik (Decimal-Localcontext `prec=28`, `ROUND_HALF_EVEN`):

1. `genset_fault` aktiv ⇒ `running=False`, `power_kw=0`, kein Verbrauch.
2. Hysterese (ADR 0058 §2.4): STOPPED→RUNNING bei `requested >=
   min_start_power_kw` und `fuel_l > 0`; RUNNING→STOPPED bei `requested <
   min_stop_power_kw` (Band verhindert Takten). STOPPED ⇒ `power_kw=0`.
3. RUNNING: Ramp Richtung `requested` (`±ramp_kw_per_s * dt_s`), geclampt
   auf `[0, max_power_kw]`; Kraftstoff-Limit (ADR 0058 §2.5): reicht der
   Tank nicht, wird `power_kw` reduziert und der Genset faehrt leer
   (`fuel_l → 0`, `running=False`).

Sign-Konvention (ADR 0058 §2.2): `power_kw >= 0` (Erzeugung).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.diesel_generator.commands import (
    DieselGeneratorAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.diesel_generator.config import (
    CONFIG_FIELD_NAMES,
    DieselGeneratorConfig,
)
from grid_gym.hexagon.core.devices.diesel_generator.snapshot import (
    SNAPSHOT_VERSION,
    DieselGeneratorSnapshot,
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
    FaultUnsupportedTypeError,
    MissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_GENSET_FAULT
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_ONE = Decimal(1)
_QUANTUM = Decimal("0.000001")
_MS_PER_SECOND = Decimal(1000)
_SECONDS_PER_HOUR = Decimal(3600)
_DIESEL_SOURCE = "diesel_generator"
_SUBSYSTEM = "diesel_generator"
_DIESEL_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-Pattern)."""

_PARAM_KEYS = CONFIG_FIELD_NAMES


@contextmanager
def _diesel_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (ADR 0058 §2.5): pinnt `prec=28`
    und `rounding=ROUND_HALF_EVEN` fuer die Tick-Berechnung."""
    with localcontext() as ctx:
        ctx.prec = _DIESEL_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class DieselGeneratorDevice:
    """`DeviceModel` + `FaultInjectableDevice` fuer den Dieselgenerator."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: DieselGeneratorConfig | None = None
        self._fuel_l: Decimal = _ZERO
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._running: bool = False
        self._generated_kwh: Decimal = _ZERO
        self._genset_fault_active: bool = False
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[DieselGeneratorAlarm] = []
        self._run_id: str = _RUN_ID_UNSET
        self._sequence: int = 0

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[DieselGeneratorAlarm, ...]:
        """Unveraenderliches Snapshot-Tupel; `drain_alarms()` fuer
        destruktiven Read (ADR 0014 §2.5-Spiegel)."""
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[DieselGeneratorAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot` (Welle-3-
        Review-M-6-Pattern). Diesel konsumiert `_random` nicht;
        symmetrisch zu den Bestandsgeraeten vorgehalten."""
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
        self._fuel_l = config.initial_fuel_l
        self._current_power_kw = _ZERO
        self._pending_power_kw = _ZERO
        self._running = False
        self._generated_kwh = _ZERO
        self._genset_fault_active = False

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
        with _diesel_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        config = cast(DieselGeneratorConfig, self._config)
        dt_s = Decimal(context.tick_ms) / _MS_PER_SECOND
        dt_hours = dt_s / _SECONDS_PER_HOUR

        if self._genset_fault_active:
            self._running = False
            new_power = _ZERO
        else:
            new_power = self._run_dispatch(config, dt_s, dt_hours)

        self._current_power_kw = new_power
        self._generated_kwh += new_power * dt_hours
        telemetry = self._emit_telemetry(context, new_power)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def _run_dispatch(
        self, config: DieselGeneratorConfig, dt_s: Decimal, dt_hours: Decimal
    ) -> Decimal:
        """Hysterese + Ramp + Kraftstoff-Limit (ADR 0058 §2.4/§2.5)."""
        requested = self._pending_power_kw
        if not self._running:
            if requested >= config.min_start_power_kw and self._fuel_l > _ZERO:
                self._running = True
            else:
                return _ZERO
        elif requested < config.min_stop_power_kw:
            self._running = False
            return _ZERO

        # Im Vortick leergefahren (`_consume_fuel` setzt `fuel_l → 0`, laesst
        # aber `running` an, damit der Leerfahr-Tick noch erzeugt): jetzt
        # stoppt der Genset bei `0` — haelt `running==False ⇒ power_kw==0`
        # (ADR 0058 §2.4/§2.5; Review-Folge 2d).
        if self._fuel_l <= _ZERO:
            self._running = False
            return _ZERO

        max_delta = config.ramp_kw_per_s * dt_s
        new_power = self._ramp(self._current_power_kw, requested, max_delta)
        new_power = self._clamp_power(new_power, config.max_power_kw)
        return self._consume_fuel(new_power, dt_hours, config)

    @staticmethod
    def _ramp(current: Decimal, target: Decimal, max_delta: Decimal) -> Decimal:
        delta = target - current
        if delta > max_delta:
            return current + max_delta
        if delta < -max_delta:
            return current - max_delta
        return target

    @staticmethod
    def _clamp_power(power: Decimal, max_power: Decimal) -> Decimal:
        if power < _ZERO:
            return _ZERO
        if power > max_power:
            return max_power
        return power

    def _consume_fuel(
        self, new_power: Decimal, dt_hours: Decimal, config: DieselGeneratorConfig
    ) -> Decimal:
        """Kraftstoff-Limit (ADR 0058 §2.5): deckelt `new_power` auf den
        verfuegbaren Rest und faehrt bei Leerlauf den Genset herunter."""
        needed = new_power * dt_hours * config.fuel_per_kwh_l
        if needed <= self._fuel_l:
            self._fuel_l -= needed
            return new_power
        # Leergefahren: Leistung auf den verbleibenden Kraftstoff begrenzen
        # und den Tank entleeren. `running` bleibt fuer DIESEN Tick an (der
        # Genset erzeugt seinen Rest, ADR 0058 §2.5) — der Stopp passiert im
        # Folge-Tick ueber den `fuel_l <= 0`-Check in `_run_dispatch`, damit
        # `running==False ⇒ power_kw==0` gilt (Review-Folge 2d).
        limited_power = self._fuel_l / (dt_hours * config.fuel_per_kwh_l)
        self._fuel_l = _ZERO
        return limited_power

    # ------------------------------------------------------------------
    # Fault-Injection (ADR 0058 §2.7, ADR 0022 §2.1 + ADR 0025)
    # ------------------------------------------------------------------

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """`FaultInjectableDevice`-Vertrag (ADR 0022 §2.1).

        Welle-2d-Closed-Set (ADR 0058 §2.7): nur `FAULT_TYPE_GENSET_FAULT`
        (`"genset_fault"`). Effekt: Genset gestoppt, `power_kw` hart `0`,
        kein Kraftstoffverbrauch. Unbekannter Typ →
        `FaultUnsupportedTypeError`. Payload ignoriert."""
        _ = payload  # Welle 2d ignoriert Payload (ADR 0058 §2.7).
        if fault_type == FAULT_TYPE_GENSET_FAULT:
            self._genset_fault_active = True
            return
        raise FaultUnsupportedTypeError(_SUBSYSTEM, fault_type)

    def clear_fault(self, fault_type: str) -> None:
        """Recovery-Surface (ADR 0025 §2.2): symmetrisch + idempotent.
        Nur `genset_fault`; unbekannter Typ → `FaultUnsupportedTypeError`."""
        if fault_type == FAULT_TYPE_GENSET_FAULT:
            self._genset_fault_active = False
            return
        raise FaultUnsupportedTypeError(_SUBSYSTEM, fault_type)

    # ------------------------------------------------------------------
    # Telemetry + Snapshot
    # ------------------------------------------------------------------

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    def snapshot(self) -> Mapping[str, object]:
        if self._config is None or self._scenario_device is None:
            return {"version": SNAPSHOT_VERSION}
        snap = DieselGeneratorSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            fuel_l=self._fuel_l,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
            running=self._running,
            generated_kwh=self._generated_kwh,
            genset_fault_active=self._genset_fault_active,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        snap = DieselGeneratorSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="diesel_generator",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._fuel_l = snap.fuel_l
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._running = snap.running
        device._generated_kwh = snap.generated_kwh
        device._genset_fault_active = snap.genset_fault_active
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DieselGeneratorDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._fuel_l == other._fuel_l
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
            and self._running == other._running
            and self._generated_kwh == other._generated_kwh
            and self._genset_fault_active == other._genset_fault_active
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._fuel_l,
                self._current_power_kw,
                self._pending_power_kw,
                self._running,
                self._generated_kwh,
                self._genset_fault_active,
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
        new_power: Decimal,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id
        running_flag = _ONE if self._running else _ZERO
        fault_flag = _ONE if self._genset_fault_active else _ZERO

        # Fuenf Tupel; alphabetisch sortiert nach Metrikname (ADR 0058 §2.8).
        emissions = (
            ("fuel_l", self._fuel_l, "l"),
            ("generated_kwh", self._generated_kwh, "kWh"),
            ("genset_fault", fault_flag, "bool"),
            ("power_kw", new_power, "kW"),
            ("running", running_flag, "bool"),
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
                    source=_DIESEL_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> DieselGeneratorConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `DieselGeneratorConfig`
    (ADR 0058 §2.3). Erwartet alle Pflicht-Felder als `Decimal`."""
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return DieselGeneratorConfig(**fields)


def _config_to_params(config: DieselGeneratorConfig) -> Mapping[str, Decimal]:
    return {key: getattr(config, key) for key in _PARAM_KEYS}
