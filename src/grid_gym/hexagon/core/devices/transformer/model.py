"""`TransformerDevice` — DeviceModel + FaultInjectableDevice
(M8 Welle 2b, `GG-DEV-016`, ADR 0056).

Folgt dem GridConnection-Set-Power-Muster ([`ADR 0017`]) mit Spannungs-
Wandlung + Verlusten.

Tick-Mechanik (ADR 0056 §2.4/§2.7), Decimal-Localcontext `prec=28`,
`ROUND_HALF_EVEN`:

1. `winding_fault` aktiv ⇒ Transformator isoliert: `primary_power_kw`,
   `secondary_power_kw`, `loss_kw` hart `0`; `throughput_kwh` eingefroren.
2. Sonst: `primary_power_kw = clamp(_pending_power_kw, ±rated)`
   (Saettigungs-Cap); `load_factor = |primary| / rated`;
   `loss_kw = no_load_loss_kw + load_loss_kw * load_factor**2`;
   `secondary_power_kw = sign(primary) * max(0, |primary| - loss_kw)`;
   `throughput_kwh += |secondary_power_kw| * (tick_ms / 3_600_000)`.

Sign-Konvention (ADR 0056 §2.2): `> 0` = Vorwaerts (Primaer→Sekundaer),
`< 0` = Rueckwaerts.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.transformer.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    TransformerAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.transformer.config import (
    CONFIG_FIELD_NAMES,
    TransformerConfig,
)
from grid_gym.hexagon.core.devices.transformer.snapshot import (
    SNAPSHOT_VERSION,
    TransformerSnapshot,
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
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_WINDING_FAULT
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_QUANTUM = Decimal("0.000001")
_MS_PER_HOUR = Decimal(3_600_000)
_TRANSFORMER_SOURCE = "transformer"
_SUBSYSTEM = "transformer"
_TRANSFORMER_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-
Pattern). TickLoop ruft `set_run_id` vor dem ersten Tick."""

_PARAM_KEYS = CONFIG_FIELD_NAMES


@contextmanager
def _transformer_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (ADR 0056 §2.4): pinnt `prec=28`
    und `rounding=ROUND_HALF_EVEN` fuer die Tick-Berechnung."""
    with localcontext() as ctx:
        ctx.prec = _TRANSFORMER_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class TransformerDevice:
    """`DeviceModel` + `FaultInjectableDevice` fuer den Transformator."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: TransformerConfig | None = None
        self._current_primary_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._throughput_kwh: Decimal = _ZERO
        self._winding_fault_active: bool = False
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[TransformerAlarm] = []
        self._run_id: str = _RUN_ID_UNSET
        self._sequence: int = 0

    # ------------------------------------------------------------------
    # Pflicht-Property + Alarm-Surface
    # ------------------------------------------------------------------

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[TransformerAlarm, ...]:
        """Unveraenderliches Snapshot-Tupel; `drain_alarms()` fuer
        destruktiven Read (ADR 0014 §2.5-Spiegel)."""
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[TransformerAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot` (Welle-3-
        Review-M-6-Pattern). Welle-2b Transformer konsumiert `_random`
        nicht; symmetrisch zu den Bestandsgeraeten vorgehalten."""
        self._random = random

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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
        self._current_primary_power_kw = _ZERO
        self._pending_power_kw = _ZERO
        self._throughput_kwh = _ZERO
        self._winding_fault_active = False

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
        with _transformer_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        config = cast(TransformerConfig, self._config)
        if self._winding_fault_active:
            # Schutzausloesung: isoliert/de-energized (ADR 0056 §2.6).
            primary = _ZERO
            secondary = _ZERO
            loss = _ZERO
        else:
            primary = self._clamp_to_rated(self._pending_power_kw, config)
            loss = self._loss_kw(primary, config)
            secondary = self._secondary_power_kw(primary, loss)
            dt_hours = Decimal(context.tick_ms) / _MS_PER_HOUR
            self._throughput_kwh += abs(secondary) * dt_hours

        self._current_primary_power_kw = primary
        telemetry = self._emit_telemetry(context, primary, secondary, loss, config)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    @staticmethod
    def _clamp_to_rated(power: Decimal, config: TransformerConfig) -> Decimal:
        """Saettigungs-Cap (ADR 0056 §2.4): begrenzt auf
        `[-rated_power_kw, +rated_power_kw]` (defensiv; der Command-
        Validator clampt bereits)."""
        if power > config.rated_power_kw:
            return config.rated_power_kw
        if power < -config.rated_power_kw:
            return -config.rated_power_kw
        return power

    @staticmethod
    def _loss_kw(primary: Decimal, config: TransformerConfig) -> Decimal:
        """Verlust (ADR 0056 §2.4): Eisen (konstant) + Kupfer
        (quadratisch im Lastfaktor)."""
        load_factor = abs(primary) / config.rated_power_kw
        return config.no_load_loss_kw + config.load_loss_kw * load_factor * load_factor

    @staticmethod
    def _secondary_power_kw(primary: Decimal, loss: Decimal) -> Decimal:
        """Sekundaerleistung (ADR 0056 §2.4): Betrag um Verlust
        reduziert (Floor `0`), Vorzeichen der Primaerseite erhalten."""
        magnitude = abs(primary) - loss
        if magnitude <= _ZERO:
            return _ZERO
        return magnitude if primary > _ZERO else -magnitude

    # ------------------------------------------------------------------
    # Fault-Injection (ADR 0056 §2.6, ADR 0022 §2.1 + ADR 0025)
    # ------------------------------------------------------------------

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """`FaultInjectableDevice`-Vertrag (ADR 0022 §2.1).

        Welle-2b-Closed-Set (ADR 0056 §2.6): nur
        `FAULT_TYPE_WINDING_FAULT` (`"winding_fault"`). Effekt:
        Transformator isoliert ⇒ `primary`/`secondary`/`loss` hart `0`.
        Unbekannter Typ → `FaultUnsupportedTypeError`. Payload ignoriert.
        """
        _ = payload  # Welle 2b ignoriert Payload (ADR 0056 §2.6).
        if fault_type == FAULT_TYPE_WINDING_FAULT:
            self._winding_fault_active = True
            return
        raise FaultUnsupportedTypeError(_SUBSYSTEM, fault_type)

    def clear_fault(self, fault_type: str) -> None:
        """Recovery-Surface (ADR 0025 §2.2): symmetrisch + idempotent
        zu `inject_fault`. Nur `winding_fault`; unbekannter Typ →
        `FaultUnsupportedTypeError`."""
        if fault_type == FAULT_TYPE_WINDING_FAULT:
            self._winding_fault_active = False
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
        snap = TransformerSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            current_primary_power_kw=self._current_primary_power_kw,
            pending_power_kw=self._pending_power_kw,
            throughput_kwh=self._throughput_kwh,
            winding_fault_active=self._winding_fault_active,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        snap = TransformerSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="transformer",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._current_primary_power_kw = snap.current_primary_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._throughput_kwh = snap.throughput_kwh
        device._winding_fault_active = snap.winding_fault_active
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransformerDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._current_primary_power_kw == other._current_primary_power_kw
            and self._pending_power_kw == other._pending_power_kw
            and self._throughput_kwh == other._throughput_kwh
            and self._winding_fault_active == other._winding_fault_active
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._current_primary_power_kw,
                self._pending_power_kw,
                self._throughput_kwh,
                self._winding_fault_active,
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
        primary: Decimal,
        secondary: Decimal,
        loss: Decimal,
        config: TransformerConfig,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id
        efficiency = abs(secondary) / abs(primary) if primary != _ZERO else _ZERO
        secondary_voltage = _ZERO if self._winding_fault_active else config.secondary_voltage_v
        fault_flag = Decimal(1) if self._winding_fault_active else _ZERO

        # Sieben Tupel; alphabetisch sortiert nach Metrikname
        # (ADR 0056 §2.7).
        emissions = (
            ("efficiency", efficiency, "ratio"),
            ("loss_kw", loss, "kW"),
            ("primary_power_kw", primary, "kW"),
            ("secondary_power_kw", secondary, "kW"),
            ("secondary_voltage_v", secondary_voltage, "V"),
            ("throughput_kwh", self._throughput_kwh, "kWh"),
            ("winding_fault", fault_flag, "bool"),
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
                    source=_TRANSFORMER_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> TransformerConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `TransformerConfig`
    (ADR 0056 §2.3). Erwartet alle Pflicht-Felder als `Decimal`."""
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return TransformerConfig(**fields)


def _config_to_params(config: TransformerConfig) -> Mapping[str, Decimal]:
    return {key: getattr(config, key) for key in _PARAM_KEYS}
