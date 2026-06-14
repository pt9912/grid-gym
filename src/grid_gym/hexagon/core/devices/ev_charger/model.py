"""`EvChargerDevice` — DeviceModel + FaultInjectableDevice
(M8 Welle 2a, `GG-DEV-015`, ADR 0055).

Kombiniert das Battery-SoC-Muster (endlicher Fahrzeug-Akku) mit dem
GridConnection-Set-Power-Muster (steuerbare, bidirektionale Leistung).

Tick-Mechanik (ADR 0055 §2.8) — die SoC-Begrenzung passiert pro Tick
gegen den **aktuellen** `stored_kwh`, nicht beim Command:

1. `unplugged` ODER aktiver `connection_loss`-Fault ⇒ `new_power_kw = 0`.
2. Sonst `requested = _pending_power_kw`, gegen den aktuellen SoC neu
   begrenzen: Laden auf `+effective_max_charge_kw(soc)` (CC/CV-Taper
   §2.4), Entladen auf `-max_discharge_kw` (flach, §2.5).
3. Energie-Limit: die Tick-Energie wird auf den verfuegbaren Rest
   gedeckelt (Laden auf `battery_capacity_kwh - stored_kwh`, Entladen
   auf `stored_kwh`). Reicht der Rest nicht, wird `new_power_kw`
   reduziert — `power_kw`-Telemetrie und gespeicherte Energie bleiben
   konsistent (nie `soc > 1` / `soc < 0`).
4. `stored_kwh` fortschreiben; `charged_kwh`/`discharged_kwh`
   akkumulieren; `_current_power_kw = new_power_kw`.

Sign-Konvention (ADR 0055 §2.2): `power_kw > 0` = Laden (Bezug),
`power_kw < 0` = V2G-Entladen (Einspeisung).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.ev_charger.commands import (
    EvChargerAlarm,
    validate_set_charge_power,
    validate_set_plug_state,
)
from grid_gym.hexagon.core.devices.ev_charger.commands import (
    COMMAND_TYPE_SET_CHARGE_POWER as _CMD_SET_CHARGE_POWER,
)
from grid_gym.hexagon.core.devices.ev_charger.commands import (
    COMMAND_TYPE_SET_PLUG_STATE as _CMD_SET_PLUG_STATE,
)
from grid_gym.hexagon.core.devices.ev_charger.config import (
    DEFAULT_INITIAL_PLUG_STATE,
    DEFAULT_INITIAL_SOC,
    PLUG_STATE_UNPLUGGED,
    EvChargerConfig,
)
from grid_gym.hexagon.core.devices.ev_charger.snapshot import (
    CONFIG_DECIMAL_FIELD_NAMES,
    SNAPSHOT_VERSION,
    EvChargerSnapshot,
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
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_CONNECTION_LOSS
from grid_gym.hexagon.ports.driven.random import RandomPort

_ZERO = Decimal(0)
_ONE = Decimal(1)
_QUANTUM = Decimal("0.000001")
_MS_PER_HOUR = Decimal(3_600_000)
_EV_CHARGER_SOURCE = "ev_charger"
_SUBSYSTEM = "ev_charger"
_EV_CHARGER_DECIMAL_PRECISION = 28

_RUN_ID_UNSET = ""
"""Marker fuer den Pre-`set_run_id`-Zustand (Welle-3-Review-M-4-
Pattern). TickLoop ruft `set_run_id` vor dem ersten Tick."""

# Init-Params: 5 Pflicht-Decimals + optionaler `initial_soc`-Decimal
# + optionaler `initial_plug_state`-String. `_config_from_params`
# unterscheidet Pflicht/optional explizit (ADR 0055 §2.3).
_REQUIRED_DECIMAL_KEYS = (
    "max_charge_kw",
    "max_discharge_kw",
    "nominal_voltage_v",
    "battery_capacity_kwh",
    "cv_phase_start_soc",
)
_INITIAL_SOC_KEY = "initial_soc"
_PLUG_PARAM_KEY = "initial_plug_state"


@contextmanager
def _ev_charger_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (ADR 0055 §2.8): pinnt `prec=28`
    und `rounding=ROUND_HALF_EVEN` fuer die Tick-Berechnung, damit
    globale Context-Mutationen den Determinismus nicht brechen."""
    with localcontext() as ctx:
        ctx.prec = _EV_CHARGER_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class EvChargerDevice:
    """`DeviceModel` + `FaultInjectableDevice` fuer den EV-Ladepunkt."""

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: EvChargerConfig | None = None
        self._plug_state: str = PLUG_STATE_UNPLUGGED
        self._stored_kwh: Decimal = _ZERO
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._charged_kwh: Decimal = _ZERO
        self._discharged_kwh: Decimal = _ZERO
        self._connection_loss_active: bool = False
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[EvChargerAlarm] = []
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
    def alarms(self) -> tuple[EvChargerAlarm, ...]:
        """Unveraenderliches Snapshot-Tupel; `drain_alarms()` fuer
        destruktiven Read (ADR 0014 §2.5-Spiegel)."""
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[EvChargerAlarm, ...]:
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` nach `from_snapshot` (Welle-3-
        Review-M-6-Pattern). Welle-2a EV-Charger konsumiert `_random`
        nicht; die Methode bleibt symmetrisch zu den Bestandsgeraeten."""
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
        # ADR 0055 §2.3: SoC intern als stored_kwh; Plug-Default aus
        # Config (Default `unplugged`).
        self._stored_kwh = config.initial_stored_kwh
        self._plug_state = config.initial_plug_state
        self._current_power_kw = _ZERO
        self._pending_power_kw = _ZERO
        self._charged_kwh = _ZERO
        self._discharged_kwh = _ZERO
        self._connection_loss_active = False

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        if command.type == _CMD_SET_CHARGE_POWER:
            outcome = validate_set_charge_power(
                config=self._config,
                plug_state=self._plug_state,
                connection_loss_active=self._connection_loss_active,
                command=command,
                device_id=self._scenario_device.id,
            )
        elif command.type == _CMD_SET_PLUG_STATE:
            outcome = validate_set_plug_state(command=command)
        else:
            return CommandResult.IGNORED
        if outcome.pending_power_kw is not None:
            self._pending_power_kw = outcome.pending_power_kw
        if outcome.plug_state is not None:
            self._plug_state = outcome.plug_state
        if outcome.alarm is not None:
            self._alarms.append(outcome.alarm)
        return outcome.result

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("tick")
        with _ev_charger_decimal_context():
            return self._tick_in_context(context)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        config = cast(EvChargerConfig, self._config)
        dt_hours = Decimal(context.tick_ms) / _MS_PER_HOUR

        # Schritt 1+2 (ADR 0055 §2.8): Plug/Fault-Gate + SoC-Re-Clamp.
        if self._plug_state == PLUG_STATE_UNPLUGGED or self._connection_loss_active:
            new_power_kw = _ZERO
        else:
            new_power_kw = self._reclamp_against_soc(self._pending_power_kw, config)

        # Schritt 3+4: Energie-Limit + State-Fortschreibung.
        new_power_kw, energy_signed = self._apply_energy_limit(new_power_kw, dt_hours, config)
        if energy_signed > _ZERO:
            self._stored_kwh += energy_signed
            self._charged_kwh += energy_signed
        elif energy_signed < _ZERO:
            self._stored_kwh += energy_signed
            self._discharged_kwh += -energy_signed
        self._current_power_kw = new_power_kw

        telemetry = self._emit_telemetry(context, new_power_kw, config)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def _reclamp_against_soc(self, requested: Decimal, config: EvChargerConfig) -> Decimal:
        """ADR 0055 §2.4/§2.5: begrenzt die angeforderte Power gegen
        den aktuellen SoC — Laden via CC/CV-Taper, Entladen flach."""
        if requested > _ZERO:
            effective_max = self._effective_max_charge_kw(config)
            return min(requested, effective_max)
        if requested < _ZERO:
            return max(requested, -config.max_discharge_kw)
        return _ZERO

    def _soc(self, config: EvChargerConfig) -> Decimal:
        """Aktueller Fahrzeug-SoC `0..1` (ADR 0055 §2.2): `stored_kwh /
        battery_capacity_kwh`. Eine Quelle fuer Kennlinie UND Telemetrie,
        damit die beiden nicht driften (Review-Folge)."""
        return self._stored_kwh / config.battery_capacity_kwh

    def _effective_max_charge_kw(self, config: EvChargerConfig) -> Decimal:
        """CC/CV-Ladekennlinie (ADR 0055 §2.4): CC unterhalb der
        Schwelle, linearer CV-Taper darueber, `0` bei `soc >= 1`."""
        soc = self._soc(config)
        if soc >= _ONE:
            return _ZERO
        if soc < config.cv_phase_start_soc:
            return config.max_charge_kw
        taper = (_ONE - soc) / (_ONE - config.cv_phase_start_soc)
        return config.max_charge_kw * taper

    def _apply_energy_limit(
        self,
        new_power_kw: Decimal,
        dt_hours: Decimal,
        config: EvChargerConfig,
    ) -> tuple[Decimal, Decimal]:
        """ADR 0055 §2.8 Schritt 3: deckelt die Tick-Energie auf den
        verfuegbaren Rest und reduziert `new_power_kw` entsprechend.
        Liefert `(new_power_kw, energy_signed)` — `energy_signed > 0`
        laedt, `< 0` entlaedt (Betrag)."""
        if new_power_kw > _ZERO:
            headroom = config.battery_capacity_kwh - self._stored_kwh
            desired = new_power_kw * dt_hours
            if desired > headroom:
                return headroom / dt_hours, headroom
            return new_power_kw, desired
        if new_power_kw < _ZERO:
            available = self._stored_kwh
            # Hard-Stop bei leerem Akku (ADR 0055 §2.5); explizites `_ZERO`
            # vermeidet ein `Decimal('-0')` aus `-available / dt_hours`,
            # das den Snapshot-/Determinismus-Vertrag braeche.
            if available == _ZERO:
                return _ZERO, _ZERO
            desired_mag = -new_power_kw * dt_hours
            if desired_mag > available:
                return -available / dt_hours, -available
            return new_power_kw, -desired_mag
        return _ZERO, _ZERO

    # ------------------------------------------------------------------
    # Fault-Injection (ADR 0055 §2.7, ADR 0022 §2.1 + ADR 0025)
    # ------------------------------------------------------------------

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """`FaultInjectableDevice`-Vertrag (ADR 0022 §2.1).

        Welle-2a-Closed-Set (ADR 0055 §2.7): nur
        `FAULT_TYPE_CONNECTION_LOSS` (`"connection_loss"`). Effekt:
        `power_kw` ist hart `0` (SoC eingefroren), analog `unplugged`.
        Unbekannter Typ → `FaultUnsupportedTypeError`. Payload wird
        ignoriert (Welle-2a-Pragmatik analog Battery/GridConnection).
        """
        _ = payload  # Welle 2a ignoriert Payload (ADR 0055 §2.7).
        if fault_type == FAULT_TYPE_CONNECTION_LOSS:
            self._connection_loss_active = True
            return
        raise FaultUnsupportedTypeError(_SUBSYSTEM, fault_type)

    def clear_fault(self, fault_type: str) -> None:
        """Recovery-Surface (ADR 0025 §2.2): symmetrisch + idempotent
        zu `inject_fault`. Nur `connection_loss`; unbekannter Typ →
        `FaultUnsupportedTypeError`."""
        if fault_type == FAULT_TYPE_CONNECTION_LOSS:
            self._connection_loss_active = False
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
        snap = EvChargerSnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=self._config,
            plug_state=self._plug_state,
            stored_kwh=self._stored_kwh,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
            charged_kwh=self._charged_kwh,
            discharged_kwh=self._discharged_kwh,
            connection_loss_active=self._connection_loss_active,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        snap = EvChargerSnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="ev_charger",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._plug_state = snap.plug_state
        device._stored_kwh = snap.stored_kwh
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._charged_kwh = snap.charged_kwh
        device._discharged_kwh = snap.discharged_kwh
        device._connection_loss_active = snap.connection_loss_active
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        return device

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EvChargerDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._plug_state == other._plug_state
            and self._stored_kwh == other._stored_kwh
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
            and self._charged_kwh == other._charged_kwh
            and self._discharged_kwh == other._discharged_kwh
            and self._connection_loss_active == other._connection_loss_active
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._plug_state,
                self._stored_kwh,
                self._current_power_kw,
                self._pending_power_kw,
                self._charged_kwh,
                self._discharged_kwh,
                self._connection_loss_active,
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
        config: EvChargerConfig,
    ) -> tuple[TelemetryPoint, ...]:
        device_id = cast(ScenarioDevice, self._scenario_device).id
        soc = self._soc(config)
        plug_flag = _ONE if self._plug_state != PLUG_STATE_UNPLUGGED else _ZERO
        loss_flag = _ONE if self._connection_loss_active else _ZERO

        # Sieben Tupel; alphabetisch sortiert nach Metrikname
        # (ADR 0055 §2.8).
        emissions = (
            ("charged_kwh", self._charged_kwh, "kWh"),
            ("connection_loss", loss_flag, "bool"),
            ("discharged_kwh", self._discharged_kwh, "kWh"),
            ("plug_state", plug_flag, "bool"),
            ("power_kw", new_power_kw, "kW"),
            ("soc", soc, "ratio"),
            ("voltage_v", config.nominal_voltage_v, "V"),
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
                    source=_EV_CHARGER_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> EvChargerConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `EvChargerConfig`
    (ADR 0055 §2.3). Pflicht-Decimals fehlend → `MissingKeysError`;
    Falsch-Typ → `WrongTypeError`. `initial_soc`/`initial_plug_state`
    sind optional (Config-Defaults)."""
    missing = [key for key in _REQUIRED_DECIMAL_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    required = {key: _require_decimal(params, key) for key in _REQUIRED_DECIMAL_KEYS}
    initial_soc = (
        _require_decimal(params, _INITIAL_SOC_KEY)
        if _INITIAL_SOC_KEY in params
        else DEFAULT_INITIAL_SOC
    )
    initial_plug_state = (
        _require_plug_state(params) if _PLUG_PARAM_KEY in params else DEFAULT_INITIAL_PLUG_STATE
    )
    return EvChargerConfig(
        max_charge_kw=required["max_charge_kw"],
        max_discharge_kw=required["max_discharge_kw"],
        nominal_voltage_v=required["nominal_voltage_v"],
        battery_capacity_kwh=required["battery_capacity_kwh"],
        cv_phase_start_soc=required["cv_phase_start_soc"],
        initial_soc=initial_soc,
        initial_plug_state=initial_plug_state,
    )


def _require_decimal(params: Mapping[str, object], key: str) -> Decimal:
    value = params[key]
    if not isinstance(value, Decimal):
        raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
    return value


def _require_plug_state(params: Mapping[str, object]) -> str:
    plug = params[_PLUG_PARAM_KEY]
    if not isinstance(plug, str):
        raise WrongTypeError(_SUBSYSTEM, f"params.{_PLUG_PARAM_KEY}", "str", type(plug).__name__)
    return plug


def _config_to_params(config: EvChargerConfig) -> Mapping[str, object]:
    """Inverse von `_config_from_params` fuer das synthetisierte
    `ScenarioDevice` post-`from_snapshot`."""
    params: dict[str, object] = {key: getattr(config, key) for key in CONFIG_DECIMAL_FIELD_NAMES}
    params[_PLUG_PARAM_KEY] = config.initial_plug_state
    return params
