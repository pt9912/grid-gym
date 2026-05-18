"""`PvDevice` — DeviceModel-Implementation (M2 Welle 3, GG-DEV-011).

Welle-3-Minimum (ADR 0016 §2.5): konstantes
`rated_power_kw`-Erzeugungsmodell mit `set_power_kw`-Override.
Kein SOC, kein Ramp-Limit, kein Hard-Clamp — die ganze Validierung
laeuft am `apply_command`-Eingang.

Tick-Mechanik (ADR 0016 §2.5):

1. `new_power_kw = self._pending_power_kw` (kein Ramp).
2. Telemetrie-Emission: 1 `TelemetryPoint` mit Metric
   `power_kw`, Quality `VALID`, quantisiert auf 6 Nachkommastellen.

Sign-Konvention (ADR 0016 §2.2): PV erzeugt nicht-negativ.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.pv.commands import (
    PvAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.pv.config import PvConfig
from grid_gym.hexagon.core.devices.pv.snapshot import (
    SNAPSHOT_VERSION,
    PvSnapshot,
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
_PV_SOURCE = "pv"
_SUBSYSTEM = "pv"
_PV_DECIMAL_PRECISION = 28

_PARAM_KEYS = ("rated_power_kw",)


@contextmanager
def _pv_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (Welle-2-Review-M-2-Spiegel)."""
    with localcontext() as ctx:
        ctx.prec = _PV_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class PvDevice:  # noqa: PLR0904 — Protocol-Surface + Hooks (drain_alarms/set_run_id) wie ADR-0014-Battery
    """`DeviceModel`-Implementation fuer den PV-Geraetetyp."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: PvConfig | None = None
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[PvAlarm] = []
        self._run_id: str = ""
        self._sequence: int = 0

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[PvAlarm, ...]:
        """Unveraenderliches Snapshot-Tupel; siehe `drain_alarms()`
        fuer destruktiven Read (ADR 0014 §2.5-Spiegel)."""
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[PvAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

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
        # ADR 0016 §2.6: Default-Output ist Nennleistung.
        self._current_power_kw = config.rated_power_kw
        self._pending_power_kw = config.rated_power_kw

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
        with _pv_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        # Welle-3-Minimum (ADR 0016 §2.5): kein Ramp, kein SOC.
        new_power_kw = self._pending_power_kw
        self._current_power_kw = new_power_kw
        telemetry = self._emit_telemetry(context, new_power_kw)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    def snapshot(self) -> Mapping[str, object]:
        if self._config is None or self._scenario_device is None:
            return {"version": SNAPSHOT_VERSION}
        snap = PvSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # ADR 0014 §2.2-Schaerfung: self-sufficient post-Resume.
        snap = PvSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="pv",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PvDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
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
        power_kw = new_power_kw.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        self._sequence += 1
        return (
            TelemetryPoint(
                run_id=self._run_id,
                tick=context.tick,
                simulation_time=context.simulation_time,
                device_id=device_id,
                metric="power_kw",
                value=power_kw,
                unit="kW",
                quality=Quality.VALID,
                source=_PV_SOURCE,
                sequence=self._sequence,
            ),
        )


def _config_from_params(params: Mapping[str, object]) -> PvConfig:
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return PvConfig(**fields)


def _config_to_params(config: PvConfig) -> Mapping[str, Decimal]:
    return {key: getattr(config, key) for key in _PARAM_KEYS}
