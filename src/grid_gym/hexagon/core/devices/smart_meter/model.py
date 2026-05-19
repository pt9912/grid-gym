"""`SmartMeterDevice` — DeviceModel-Implementation
(M2 Welle 4b, `GG-DEV-014`).

Stateless aggregator (ADR 0018 §2.4). Aggregiert pro Tick neu
ueber die per `attach_sources(...)` verdrahteten Quell-Geraete;
emittiert einen einzigen `TelemetryPoint` mit Metric
`aggregated_power_kw`.

Lifecycle-Erweiterung gegenueber DeviceModel-Protocol
(ADR 0013):

- `attach_sources(sources_by_id: Mapping[str, DeviceModel])` —
  Geraete-spezifischer Lifecycle-Hook (analog
  `attach_random`). Aufrufer-Pflicht: nach `initialize`, vor
  erstem `tick`. Mehrfach-Aufruf ist erlaubt (Welle 6
  TickLoop-Reload).

Drei verschiedene Lookup-Fehler-Modi (ADR 0018 §2.3 / §2.4):

1. **Pre-attach** (Mapping nie gesetzt): Telemetrie mit
   `value=0` + `quality=MISSING` (kein Fehler).
2. **Reference-Lookup-Defense** (Mapping gesetzt, aber ID
   fehlt): `SmartMeterSourceMissingError`.
3. **Quell-Pre-init** (Quell-`telemetry()` ist `()`): Silent-
   Skip auf Metric-Ebene (Beitrag `0`).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.devices.smart_meter.commands import SmartMeterAlarm
from grid_gym.hexagon.core.devices.smart_meter.config import (
    SmartMeterConfig,
    SmartMeterConfigError,
)
from grid_gym.hexagon.core.devices.smart_meter.snapshot import (
    CONFIG_FIELD_NAMES,
    SNAPSHOT_VERSION,
    SmartMeterSnapshot,
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
    GridGymError,
    MissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_QUANTUM = Decimal("0.000001")
_SMART_METER_SOURCE = "smart_meter"
_SUBSYSTEM = "smart_meter"
_SMART_METER_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-
Pattern). Welle 6 TickLoop ruft `set_run_id` vor dem ersten Tick."""

# Welle-4a-Review L-3-Pattern: Single-Source-of-Truth ueber
# `snapshot.py`.
_PARAM_KEYS = CONFIG_FIELD_NAMES

_AGGREGATED_METRIC = "aggregated_power_kw"
_AGGREGATED_UNIT = "kW"


class SmartMeterSourceMissingError(GridGymError):
    """Aggregations-Quell-Device ist im `aggregate_device_ids`-
    Scope, aber nicht im `attach_sources(...)`-Mapping (ADR 0018
    §2.4 Reference-Lookup-Defense)."""

    def __init__(self, device_id: str, missing_source_id: str) -> None:
        super().__init__(
            f"SmartMeter {device_id!r}: source device "
            f"{missing_source_id!r} is in aggregate_device_ids "
            f"but missing from attach_sources(...) mapping. "
            f"Likely scenario drift after snapshot resume."
        )
        self.device_id = device_id
        self.missing_source_id = missing_source_id


@contextmanager
def _smart_meter_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (Welle-2-Review-M-2-Spiegel)."""
    with localcontext() as ctx:
        ctx.prec = _SMART_METER_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class SmartMeterDevice:
    """`DeviceModel`-Implementation fuer SmartMeter (ADR 0018)."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: SmartMeterConfig | None = None
        # `None` = pre-attach (kein Fehler, Quality.MISSING);
        # Mapping = attached (Reference-Lookup-Defense aktiv).
        self._sources_by_id: Mapping[str, DeviceModel] | None = None
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[SmartMeterAlarm] = []
        self._run_id: str = _RUN_ID_UNSET
        self._sequence: int = 0

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[SmartMeterAlarm, ...]:
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[SmartMeterAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot`
        (Welle-3-Review M-6-Pattern).

        **Welle-4b-Vertrag (Review-M-3):** `attach_random` ist in
        Welle 4b **optional** — SmartMeter konsumiert `_random`
        nicht (`tick` ist eine reine Funktion der Quell-
        Telemetrie). `tick(...)` nach `from_snapshot(...)` ohne
        vorherigen `attach_random`-Aufruf ist in Welle 4b
        zulaessig.

        **M3-Vertrag (Forward-Looking):** wenn M3-Fault-Injection
        (`GG-FAULT-*` Mess-Stoerungen, fehlende Ablesungen)
        aktiviert wird, wechselt `attach_random` auf **Pflicht**.
        TickLoop/Scenario-Loader muss dann nach jedem
        `from_snapshot(...)` einen `attach_random(...)`-Aufruf
        sequenzieren, sonst werden Fault-Injection-Pfade
        stillschweigend deaktiviert."""
        self._random = random

    def attach_sources(self, sources_by_id: Mapping[str, DeviceModel]) -> None:
        """Verdrahtet die Aggregations-Quellen (ADR 0018 §2.3).

        Aufrufer-Pflicht: nach `initialize`, vor erstem `tick`.
        Mehrfach-Aufruf ueberschreibt (Welle-6-TickLoop-Reload
        bzw. M3-Re-Wire). Defensive Kopie als `dict`, damit
        nachtraegliche Mutation des Aufrufer-Mappings keinen
        Einfluss hat."""
        self._sources_by_id = dict(sources_by_id)

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

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        # Welle-4b-Minimum (ADR 0018 §2.6): kein produktiver
        # Command-Surface; alles IGNORED. Welle-2-Review-M-7-
        # payload-None-Defensive ist trivial erfuellt.
        _ = command
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("tick")
        with _smart_meter_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        config = cast(SmartMeterConfig, self._config)
        if self._sources_by_id is None:
            # Pre-attach (ADR 0018 §2.3): kein Fehler, Quality.MISSING.
            telemetry = self._emit_telemetry(context, _ZERO, Quality.MISSING)
        else:
            total = self._aggregate_from_sources(
                config.aggregate_device_ids,
                config.aggregate_metric_name,
                self._sources_by_id,
            )
            telemetry = self._emit_telemetry(context, total, Quality.VALID)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def _aggregate_from_sources(
        self,
        aggregate_device_ids: tuple[str, ...],
        metric_name: str,
        sources_by_id: Mapping[str, DeviceModel],
    ) -> Decimal:
        total = _ZERO
        device_id = cast(ScenarioDevice, self._scenario_device).id
        for source_id in aggregate_device_ids:
            if source_id not in sources_by_id:
                # ADR 0018 §2.4 Reference-Lookup-Defense.
                raise SmartMeterSourceMissingError(device_id, source_id)
            source = sources_by_id[source_id]
            total += _read_metric_from_source(source, metric_name)
        return total

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    def snapshot(self) -> Mapping[str, object]:
        if self._config is None or self._scenario_device is None:
            return {"version": SNAPSHOT_VERSION}
        snap = SmartMeterSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # ADR 0014 §2.2-Schaerfung / ADR 0018 §2.5: self-sufficient.
        snap = SmartMeterSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="smart_meter",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        # `_sources_by_id` bleibt `None` — Aufrufer muss nach
        # `from_snapshot(...)` `attach_sources(...)` rufen.
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SmartMeterDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
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
        aggregated_value: Decimal,
        quality: Quality,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id
        value = aggregated_value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        self._sequence += 1
        return (
            TelemetryPoint(
                run_id=self._run_id,
                tick=context.tick,
                simulation_time=context.simulation_time,
                device_id=device_id,
                metric=_AGGREGATED_METRIC,
                value=value,
                unit=_AGGREGATED_UNIT,
                quality=quality,
                source=_SMART_METER_SOURCE,
                sequence=self._sequence,
            ),
        )


def _read_metric_from_source(source: DeviceModel, metric_name: str) -> Decimal:
    """Liest den ersten passenden `TelemetryPoint` aus
    `source.telemetry()`. ADR 0018 §2.4: Pre-init-Quelle
    (leeres Tupel) oder Quelle ohne passenden Metric-Eintrag →
    Beitrag `0` (Silent-Skip auf Metric-Ebene)."""
    for point in source.telemetry():
        if point.metric == metric_name:
            return point.value
    return _ZERO


def _config_from_params(params: Mapping[str, object]) -> SmartMeterConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `SmartMeterConfig`.

    Pflicht-Felder: `aggregate_device_ids` (list[str] oder
    tuple[str, ...]). Optional: `aggregate_metric_name` (str,
    Default `"power_kw"`).
    """
    if "aggregate_device_ids" not in params:
        raise MissingKeysError(_SUBSYSTEM, ["aggregate_device_ids"])

    raw_ids = params["aggregate_device_ids"]
    if not isinstance(raw_ids, (list, tuple)):
        raise WrongTypeError(
            _SUBSYSTEM,
            "params.aggregate_device_ids",
            "list or tuple",
            type(raw_ids).__name__,
        )
    if any(not isinstance(item, str) for item in raw_ids):
        raise WrongTypeError(
            _SUBSYSTEM,
            "params.aggregate_device_ids[*]",
            "str",
            "non-str entry",
        )
    device_ids = tuple(raw_ids)

    metric_name_raw = params.get("aggregate_metric_name", "power_kw")
    if not isinstance(metric_name_raw, str):
        raise WrongTypeError(
            _SUBSYSTEM,
            "params.aggregate_metric_name",
            "str",
            type(metric_name_raw).__name__,
        )

    # Welle-4b-Review M-2: SmartMeterConfig-Validierung (Sortier-
    # Invariante, Welle-4b-`power_kw`-Pflicht, etc.) muss in einen
    # subsystem-typisierten `WrongTypeError` ueberfuehrt werden,
    # damit Aufrufer eine einheitliche Fehler-Hierarchie sehen
    # (Pattern-Spiegel zu PV/Load/GridConnection-snapshot.py:
    # `from_dict`-Wrap).
    try:
        return SmartMeterConfig(
            aggregate_device_ids=device_ids,
            aggregate_metric_name=metric_name_raw,
        )
    except SmartMeterConfigError as err:
        raise WrongTypeError(_SUBSYSTEM, "params", "valid", str(err)) from err


def _config_to_params(config: SmartMeterConfig) -> Mapping[str, object]:
    return {
        "aggregate_device_ids": list(config.aggregate_device_ids),
        "aggregate_metric_name": config.aggregate_metric_name,
    }


__all__ = [
    "SmartMeterDevice",
    "SmartMeterSourceMissingError",
]
