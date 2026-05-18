"""`BatteryDevice` — DeviceModel-Implementation (M2 Welle 2).

Implementiert das `DeviceModel`-Protocol fuer den Battery-
Geraetetyp (`GG-DEV-010`) inklusive SOC-Fortschreibung
(`GG-BESS-001/003`), Ramp-Limits (`GG-BESS-004`), Sicherheits-
grenzen-Validierung (`GG-BESS-005`) und Lifecycle-/Snapshot-
Vertrag aus ADR 0013.

Tick-Mechanik (ADR 0014 §2.4):

1. Ramp-Limit auf Power-Delta `pending - current`.
2. Energiebilanz: `power * dt_hours * efficiency` (Laden) bzw.
   `power * dt_hours / efficiency` (Entladen).
3. SOC-Hard-Clamp auf `[min_soc_kwh, max_soc_kwh]` (`GG-BESS-005`).
4. Telemetrie-Emission: `soc_pct`, `soc_kwh`, `power_kw`
   (alphabetisch sortiert nach Metrikname, deterministisch).

Decimal-Quantisierung: alle Telemetrie-Werte vor Emission auf
6 Nachkommastellen quantisiert (`GG-DATA-005`-Soll).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.battery.commands import (
    BatteryAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.devices.battery.snapshot import (
    SNAPSHOT_VERSION,
    BatterySnapshot,
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
    WrongTypeError,
)
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)
_QUANTUM = Decimal("0.000001")
"""GG-DATA-005-Soll: max. 6 Nachkommastellen in Telemetrie."""
_TICK_MS_PER_HOUR = Decimal(1000 * 3600)
"""1 Stunde = 3 600 000 ms (Decimal-Konstante fuer Energie-Umrechnung)."""

_SUBSYSTEM = "battery"
_BATTERY_SOURCE = "battery"
"""TelemetryPoint.source-Wert; ADR 0007 §5 Sub-Port-Konvention."""

# Parameter-Schluessel im ScenarioDevice.params-Mapping.
_PARAM_KEYS = (
    "capacity_kwh",
    "initial_soc_pct",
    "min_soc_pct",
    "max_soc_pct",
    "max_charge_kw",
    "max_discharge_kw",
    "charge_efficiency",
    "discharge_efficiency",
    "ramp_kw_per_s",
)


class BatteryDevice:
    """`DeviceModel`-Implementation fuer den Battery-Geraetetyp.

    Lifecycle, Snapshot-Vertrag und Determinismus sind in
    ADR 0013/0014 fixiert; siehe Modul-Docstring oben fuer die
    Tick-Mechanik.

    Welle 2 nutzt den injizierten `RandomPort` nicht (keine
    stochastischen Anteile); Welle 3+ Fault-Injection wird ihn
    via `sub_port`-Konvention konsumieren.
    """

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: BatteryConfig | None = None
        self._soc_kwh: Decimal = _ZERO
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[BatteryAlarm] = []
        self._run_id: str = ""
        # `_sequence` zaehlt monoton ueber alle emittierten
        # `TelemetryPoint.sequence`-Felder — pro Tick werden drei
        # Werte ausgegeben (`power_kw`, `soc_kwh`, `soc_pct`); ohne
        # eigenen Counter wuerden mehrere Battery-Devices im selben
        # Tick kollidieren. ADR 0007 §5 `RandomPort.sub_port` ist
        # nicht der richtige Hebel, weil `sequence` keine Zufalls-
        # Quelle ist.
        self._sequence: int = 0

    # ------------------------------------------------------------------
    # Pflicht-Property (ADR 0013 §2.7)
    # ------------------------------------------------------------------

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[BatteryAlarm, ...]:
        """Bisher emittierte Alarme als Tupel-Snapshot
        (ADR 0014 §2.5). Unveraenderlich; Welle 6 TickLoop kann
        die Liste konsumieren, ohne Mutation zu riskieren.
        """
        return tuple(self._alarms)

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
        self._soc_kwh = config.initial_soc_kwh
        self._current_power_kw = _ZERO
        self._pending_power_kw = _ZERO

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        outcome = validate_set_power_command(
            config=self._config,
            soc_kwh=self._soc_kwh,
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
        config = self._config
        dt_seconds = Decimal(context.tick_ms) / Decimal(1000)
        dt_hours = Decimal(context.tick_ms) / _TICK_MS_PER_HOUR

        # Ramp-Limit (GG-BESS-004)
        max_delta = config.ramp_kw_per_s * dt_seconds
        delta = self._pending_power_kw - self._current_power_kw
        if delta > max_delta:
            new_power_kw = self._current_power_kw + max_delta
        elif delta < -max_delta:
            new_power_kw = self._current_power_kw - max_delta
        else:
            new_power_kw = self._pending_power_kw

        # Energiebilanz (GG-BESS-001/003)
        if new_power_kw > _ZERO:
            energy_delta_kwh = new_power_kw * dt_hours * config.charge_efficiency
        elif new_power_kw < _ZERO:
            energy_delta_kwh = new_power_kw * dt_hours / config.discharge_efficiency
        else:
            energy_delta_kwh = _ZERO

        # SOC-Hard-Clamp (GG-BESS-005)
        new_soc_kwh = self._soc_kwh + energy_delta_kwh
        if new_soc_kwh < config.min_soc_kwh:
            new_soc_kwh = config.min_soc_kwh
        elif new_soc_kwh > config.max_soc_kwh:
            new_soc_kwh = config.max_soc_kwh

        self._soc_kwh = new_soc_kwh
        self._current_power_kw = new_power_kw

        telemetry = self._emit_telemetry(context, new_soc_kwh, new_power_kw)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> Mapping[str, object]:
        config = self._config
        if config is None:
            # Pre-init: nur `version`-Felder (ADR 0013 §2.6).
            return {"version": SNAPSHOT_VERSION}
        snap = BatterySnapshot(
            version=SNAPSHOT_VERSION,
            config=config,
            soc_kwh=self._soc_kwh,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        snap = BatterySnapshot.from_dict(state)
        device = cls()
        device._config = snap.config
        device._soc_kwh = snap.soc_kwh
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        return device

    # ------------------------------------------------------------------
    # Equality (fuer Roundtrip-Vergleich von_snapshot(snapshot()) == device)
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BatteryDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._soc_kwh == other._soc_kwh
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._soc_kwh,
                self._current_power_kw,
                self._pending_power_kw,
            )
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_telemetry(
        self,
        context: DeviceTickContext,
        new_soc_kwh: Decimal,
        new_power_kw: Decimal,
    ) -> tuple[TelemetryPoint, ...]:
        config = cast(BatteryConfig, self._config)
        device_id = cast(ScenarioDevice, self._scenario_device).id

        soc_pct = (new_soc_kwh / config.capacity_kwh * _HUNDRED).quantize(
            _QUANTUM, rounding=ROUND_HALF_EVEN
        )
        soc_kwh = new_soc_kwh.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        power_kw = new_power_kw.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

        # Drei Tupel; alphabetisch sortiert nach Metrikname.
        emissions = (
            ("power_kw", power_kw, "kW"),
            ("soc_kwh", soc_kwh, "kWh"),
            ("soc_pct", soc_pct, "pct"),
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
                    source=_BATTERY_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> BatteryConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `BatteryConfig`.

    Welle 2: erwartet alle Pflicht-Felder als `Decimal` im Params-
    Mapping. YAML-Adapter-Schicht (M3/Welle-5-Scenario-YAML) ist
    fuer die Decimal-Konversion verantwortlich; hier wird strukturell
    geprueft. Mismatches werfen `WrongTypeError("battery", key,
    "Decimal", actual)`.
    """
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        if key not in params:
            from grid_gym.hexagon.core.errors import MissingKeysError

            missing = [k for k in _PARAM_KEYS if k not in params]
            raise MissingKeysError(_SUBSYSTEM, missing)
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return BatteryConfig(**fields)
