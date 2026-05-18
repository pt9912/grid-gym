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
from contextlib import contextmanager
from collections.abc import Iterator
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
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
    MissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.ports.driven.random import RandomPort

_SATURATION_COMMAND_ID = "<saturation>"
"""Welle-2-Review C-2: spezieller command_id-Marker fuer
Saturation-Alarme aus dem Hard-Clamp-Pfad (ADR 0014 §2.4).
Welle 6 TickLoop kann die Alarme per String-Match filtern."""

_BATTERY_DECIMAL_PRECISION = 28
"""Default-`decimal.getcontext().prec`. Welle-2-Review M-2: das
Tick-Body wird in `with localcontext() as ctx: ctx.prec = 28;
ctx.rounding = ROUND_HALF_EVEN` eingeschlossen, damit Tests/
Adapter, die die globale Decimal-Context mutieren, den
Determinismus-Vertrag aus ADR 0014 §2.6 nicht brechen."""


@contextmanager
def _battery_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper fuer die Tick-Berechnung
    (Welle-2-Review M-2). Pinnt `prec=28` und `rounding=ROUND_HALF_EVEN`
    fuer die Dauer der Tick-Body-Ausfuehrung."""
    with localcontext() as ctx:
        ctx.prec = _BATTERY_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


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


class BatteryDevice:  # noqa: PLR0904 — Protocol-Surface plus Welle-2-Review-Hooks (drain_alarms/set_run_id)
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
        Verwende `drain_alarms()` fuer destruktives Auslesen.
        """
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[BatteryAlarm, ...]:
        """Liefert alle bisher emittierten Alarme und leert die
        interne Liste (Welle-2-Review M-3: AlarmSinkPort kommt mit
        M3; bis dahin braucht der Aufrufer eine Drain-Semantik,
        damit lange Laeufe nicht unbeschraenkt Speicher binden)."""
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        """Setzt `TelemetryPoint.run_id` fuer alle nachfolgenden
        Tick-Emissions (Welle-2-Review H-2). TickLoop ruft das
        beim Lauf-Start; Welle 2 hat keinen TickLoop, der das
        macht — Test-Setup ruft direkt."""
        self._run_id = run_id

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
        with _battery_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        config = cast(BatteryConfig, self._config)
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

        # SOC-Hard-Clamp + Saturation-Power-Reset (GG-BESS-005,
        # Welle-2-Review C-2).
        new_soc_kwh, new_power_kw = self._apply_soc_clamp(
            self._soc_kwh + energy_delta_kwh, new_power_kw, config
        )

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
        if config is None or self._scenario_device is None:
            # Pre-init: nur `version`-Felder (ADR 0013 §2.6).
            return {"version": SNAPSHOT_VERSION}
        snap = BatterySnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=config,
            soc_kwh=self._soc_kwh,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # Welle-2-Review C-1: from_snapshot ist self-sufficient
        # (ADR 0014 §2.2). Wir synthesizen ein minimales
        # ScenarioDevice aus device_id + embedded config, damit
        # die Lifecycle-Pre-init-Raises sofort aufgeloest sind.
        # `_random` bleibt None — Welle 2 Battery konsumiert es
        # nicht; Welle 3+ Geraete brauchen separate Loesung.
        snap = BatterySnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="battery",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._soc_kwh = snap.soc_kwh
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    # ------------------------------------------------------------------
    # Equality (fuer Roundtrip-Vergleich von_snapshot(snapshot()) == device)
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        # Welle-2-Review M-1: Equality vergleicht persistierten
        # State (alles, was im Snapshot landet). Run-Segment-lokale
        # Felder wie `_alarms` und `_last_telemetry`/`_random` sind
        # bewusst ausgeschlossen — sie sind Effekt der bisherigen
        # Iteration, nicht des Zustands.
        if not isinstance(other, BatteryDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._soc_kwh == other._soc_kwh
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
                self._soc_kwh,
                self._current_power_kw,
                self._pending_power_kw,
                self._device_id_or_none(),
                self._run_id,
                self._sequence,
            )
        )

    def _device_id_or_none(self) -> str | None:
        return None if self._scenario_device is None else self._scenario_device.id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_soc_clamp(
        self,
        target_soc_kwh: Decimal,
        current_power_kw: Decimal,
        config: BatteryConfig,
    ) -> tuple[Decimal, Decimal]:
        """SOC-Hard-Clamp (GG-BESS-005) + Saturation-Power-Reset
        (Welle-2-Review C-2). Liefert das Tupel
        `(new_soc_kwh, new_power_kw)` zurueck.

        Bei Saturation:
        - `new_soc_kwh = clamp(target_soc_kwh, min/max_soc_kwh)`,
        - `new_power_kw = 0` (kein Ghost-Discharge),
        - `_pending_power_kw = 0` (kein „auto-resume",
          `GG-BESS-005`-Akzeptanz),
        - Saturation-Alarm via `command_id="<saturation>"` in
          `_alarms` angefuegt.
        """
        if target_soc_kwh < config.min_soc_kwh:
            new_soc_kwh = config.min_soc_kwh
            saturation_limit_pct: Decimal = config.min_soc_pct
        elif target_soc_kwh > config.max_soc_kwh:
            new_soc_kwh = config.max_soc_kwh
            saturation_limit_pct = config.max_soc_pct
        else:
            return target_soc_kwh, current_power_kw

        if current_power_kw == _ZERO:
            # SOC kommt zwar aus den Grenzen heraus, aber das war
            # nicht durch eigene Power getrieben (z. B. anfaengliche
            # Konfiguration genau am Limit) — kein Alarm.
            return new_soc_kwh, current_power_kw

        # Power+Pending zero + Alarm
        self._pending_power_kw = _ZERO
        device_id = cast(ScenarioDevice, self._scenario_device).id
        self._alarms.append(
            BatteryAlarm(
                target_device_id=device_id,
                limit=saturation_limit_pct,
                result=CommandResult.LIMITED,
                command_id=_SATURATION_COMMAND_ID,
            )
        )
        return new_soc_kwh, _ZERO

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
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return BatteryConfig(**fields)


def _config_to_params(config: BatteryConfig) -> Mapping[str, Decimal]:
    """Inverse von `_config_from_params`: serialisiert
    `BatteryConfig` zurueck in das Params-Mapping-Form fuer das
    synthesizte `ScenarioDevice` post-`from_snapshot`
    (Welle-2-Review C-1)."""
    return {key: getattr(config, key) for key in _PARAM_KEYS}
